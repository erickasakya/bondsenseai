from fastapi import FastAPI, UploadFile, File, Depends
from db.database import get_session, create_db_and_tables
import shutil
from ingestions import main as ingestions
from contextlib import asynccontextmanager
from agent.main import build_graph
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
import logging
from langgraph.checkpoint.memory import MemorySaver

logging.basicConfig(level=logging.ERROR)

memory_db = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    app.state.compiled_graph = build_graph()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str | None = "default_user"


@app.post("/upload-calendar/")
async def upload_calendar(file: UploadFile = File(...), session=Depends(get_session)):
    temp_file = f"/tmp/{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = ingestions.parse_excel(temp_file)
    if "competitive_offer" in df:
        print(df)
        ingestions.insert_auction_result(session, df)
    else:
        ingestions.insert_calendars(session, df)
    return {"message": "Data inserted successfully", "rows": len(df)}


@app.post("/chat/")
async def chat_agent(msg: ChatRequest):
    """Get the chat for a given instrument."""
    user_id = msg.user_id or "default_user"

    if user_id not in memory_db:
        memory_db[user_id] = MemorySaver()

    compiled_graph = app.state.compiled_graph

    config = {"checkpoint": memory_db[user_id]}
    resp = compiled_graph.invoke(
        {"messages": [HumanMessage(content=msg.message)]}, config=config
    )
    return AIMessage(content=resp["messages"][-1].content)
