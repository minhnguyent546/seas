from fastapi import APIRouter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from app.chatbot.schemas import ChatQuery
from app.core.config import settings
from app.deps import AsyncSessionDep, CurrentActiveUserDep

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


llm = ChatGoogleGenerativeAI(
    model=settings.MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0,
)


@router.post("/query")
async def query(
    chat_query: ChatQuery,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    logger.info(f"Query: {chat_query.query}")
    prompt = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=chat_query.query),
    ]
    response = await llm.ainvoke(prompt)
    if isinstance(response.content, list):
        response.content = response.content[0].text()
    return response.content
