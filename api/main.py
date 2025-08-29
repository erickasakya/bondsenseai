from fastapi import FastAPI, UploadFile, File, Depends
from db.database import get_session, create_db_and_tables
import shutil
from sqlmodel import Session
from ingestions import main as ingestions
from contextlib import asynccontextmanager
from agent.main import build_graph, tools
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
import logging

logging.basicConfig(level=logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


@app.post("/upload-calendar/")
async def upload_calendar(file: UploadFile = File(...), session=Depends(get_session)):
    temp_file = f"/tmp/{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = ingestions.parse_excel(temp_file)
    ingestions.insert_calendars(session, df)
    return {"message": "Data inserted successfully", "rows": len(df)}


@app.post("/chat/")
async def chat_agent(msg: ChatRequest, db: Session = Depends(get_session)):
    """Get the chat for a given instrument."""

    # return ingestions.next_auction("Bond", 2, db)
    compiled_graph = build_graph()
    config = {"configurable": {"db_session": db}}
    resp = compiled_graph.invoke(
        {"messages": [HumanMessage(content=msg.message)]}, config=config
    )
    return AIMessage(content=resp["messages"][-1].content)
