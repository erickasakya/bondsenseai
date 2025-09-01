from typing import TypedDict, Sequence, Literal, Annotated
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv, dotenv_values
from pydantic import BaseModel
from ingestions import main as data_model
from sqlmodel import Session
import logging
from db.database import engine


logging.basicConfig(level=logging.INFO)

load_dotenv()
config = dotenv_values(".env")


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    instrument: Literal["Bond", "Bill"] | None
    tenure: int | None
    tool_output: str | None


class AuctionQuery(BaseModel):
    instrument: Literal["Bond", "Bill"] | None = None
    tenure: int | None = None


def auction_to_text(auction, action="next auction for "):
    rate_text = (
        f"{float(auction.rate):.3f}% in {auction.currency}"
        if auction.rate
        else "rate not yet available"
    )
    isin_text = (
        f"(ISIN: {auction.isin})"
        if getattr(auction, "isin", None)
        else "ISIN not available"
    )

    return (
        f"The {action}{auction.tenure}-year {auction.instrument} {isin_text} "
        f"is/was on {auction.auction_date.strftime('%B %d, %Y')}. "
        f"Settlement is on {auction.settlement_date.strftime('%B %d, %Y')}, "
        f"and maturity is on {auction.maturity_date.strftime('%B %d, %Y')}. "
        f"The coupon rate is {rate_text}."
    )


def get_calendar(instrument: str, tenure: int):
    """Get the whole auction calendar for a given instrument. The instrument must be 'Bond' or 'Bill'"""
    with Session(engine) as session:
        return data_model.get_calendar(instrument, tenure, session)


def next_auction(instrument: str, tenure: int):
    """Get the next auction date for a given instrument. The instrument must be 'Bond' or 'Bill'"""
    auctions = []
    with Session(engine) as session:
        auctions = data_model.next_auction(instrument, tenure, session)
    if not auctions:
        return "No auction found for this instrument and tenure."

    return auction_to_text(auctions)


def last_auction(instrument: str, tenure: int):
    """Get the last auction date for a given instrument. The instrument must be 'Bond' or 'Bill'."""
    auctions = []
    with Session(engine) as session:
        auctions = data_model.last_auction(instrument, tenure, session)
    if not auctions:
        return "No auction found for this instrument and tenure."
    return auction_to_text(auctions, action="last auction for ")


def count_auctions(instrument: str, tenure: int):
    """Count the total number of auctions for a given instrument. The instrument must be 'Bond' or 'Bill'"""
    auctions = []
    with Session(engine) as session:
        auctions = data_model.count_auctions(instrument, tenure, session)
    if not auctions:
        return "No auction found for this instrument and tenure."
    return auctions


tools = [next_auction, last_auction, count_auctions, get_calendar]


def build_graph():

    llm = ChatGroq(
        model=config["GROQ_MODEL"],
        api_key=config.get("GROQ_API_KEY"),
        temperature=0,
    ).bind_tools(tools)

    structured_llm = llm.with_structured_output(AuctionQuery)

    def capture_tool_output(state: AgentState) -> AgentState:
        last_msg = state["messages"][-1]
        if last_msg.type == "tool":
            state["tool_output"] = last_msg.content

        tool_message = ToolMessage(
            tool_call_id=last_msg.id, name=last_msg.name, content=last_msg.content
        )
        state["messages"] = state["messages"] + [tool_message]
        return state

    def extract_params(state: AgentState) -> AgentState:
        query = state["messages"][-1].content
        try:
            parsed = structured_llm.invoke(query, config=config)
            state["instrument"] = parsed.instrument
            state["tenure"] = parsed.tenure
        except Exception as e:
            logging.error(f"Failed to parse query: {query}, error: {e}")
            state["messages"] = state["messages"] + [
                AIMessage(
                    content="Could not parse instrument and tenure. Please specify, e.g., 'Bond with 10-year tenure'."
                )
            ]
        return state

    def our_agent(state: AgentState) -> AgentState:
        tool_output = state.get("tool_output")
        tool_section = (
            f"""
This information comes from trusted tools and databases. Unless no data is available, consider it authoritative. 
Your responses must clearly include:
  • Instrument type (Bond or Bill)  
  • Tenure (e.g., 2-year, 10-year)  
  • ISIN  
  • Coupon rate in % and currency  
  • Auction date  
  • Settlement date  
  • Maturity date if available 

{tool_output}
"""
            if tool_output
            else ""
        )

        system_prompt = SystemMessage(
            #             content=f"""
            # You are Bondy Chat, an AI financial assistant specializing in treasury bond auctions in Uganda.
            # Provide concise, accurate answers using the tool outputs if they are available.
            # If information is missing, say you don’t know.
            # """
            content=f"""
            You are Bondy Chat, an AI financial assistant specializing in treasury bond auctions in Uganda.
            You provide accurate, concise, and user-friendly answers.
            Knowledge Scope:
            - You know about auction calendars, maturities, coupon rates, and results of treasury securities in Uganda.
            - You use trusted sources only: BondSense AI DB, BoU announcements, auction results.
            - If tool output is provided, treat it as the correct and final information to answer the user's query.
            - Do not add disclaimers about accuracy. If tool output is empty, then politely say you don't know.
            {tool_section}

            Tense rules:  
            - For future auctions, say: "is scheduled for [date]"  
            - For past auctions, say: "was held on [date]"
            """
        )
        message = [system_prompt] + state["messages"]
        response = llm.invoke(message)
        return {"messages": state["messages"] + [response]}

    def should_continue(state: AgentState) -> str:
        messages = state["messages"]
        last_message = messages[-1]

        if not getattr(last_message, "tool_calls", []):
            return "end"

        last_tool_call = last_message.tool_calls[-1]
        if last_tool_call.get("name") == "stop_tool":
            return "end"

        if not last_message.tool_calls:
            return "end"
        return "continue"

    graph = StateGraph(AgentState)
    graph.add_node("extractor", extract_params)
    graph.add_node("our_agent", our_agent)

    tool_node = ToolNode(tools=tools)
    graph.add_node("tools", tool_node)

    graph.add_node("capture_tool_output", capture_tool_output)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "our_agent")
    graph.add_conditional_edges(
        "our_agent",
        should_continue,
        {"continue": "tools", "end": END},
    )

    graph.add_edge("tools", "capture_tool_output")
    graph.add_edge("capture_tool_output", "our_agent")

    compiled_graph = graph.compile()

    return compiled_graph
