# chat with the data using LangChain and Groq AI.
import streamlit as st
from dotenv import load_dotenv, dotenv_values
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import requests

load_dotenv()
config = dotenv_values("../.env")

st.title("BondSense AI")
st.caption("Your friendly guide to Treasury Bonds.")

if "latest_msgs_sent" not in st.session_state:
    st.session_state.latest_msgs_sent = []

if "messages" not in st.session_state:
    st.session_state.messages = []


def generate_response(msg: str):

    backend_url = config["BACKEND_URL"]
    response = requests.post(
        f"{backend_url}/chat",
        json={"message": msg},
    )
    st.session_state.messages.append(AIMessage(content=response.json()["content"]))
    st.session_state.latest_msgs_sent = HumanMessage(content=msg)
    return response


for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("human"):
            st.write(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("ai"):
            st.write(message.content)
    else:
        with st.chat_message("system"):
            st.write(message.content)

if msg := st.chat_input("Ask any Treasury Bond question"):
    st.session_state.messages.append(HumanMessage(content=msg))
    response = generate_response(msg)

    st.rerun()


st.divider()
