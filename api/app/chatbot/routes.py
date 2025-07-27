from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import app.chatbot.service as chatbot_service
from app.chatbot.schemas import ChatQuery
from app.deps import AsyncSessionDep, CurrentActiveUserDep

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_class=StreamingResponse)
async def query(
    chat_query: ChatQuery,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Process a chat query and return a streaming response."""

    streaming_response = await chatbot_service.process_query(
        chat_query=chat_query,
        session=session,
        current_user=current_user,
    )
    return streaming_response


@router.post("/query-with-agent", response_class=StreamingResponse)
async def query_with_agent(
    chat_query: ChatQuery,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Process a chat query with agent and return a streaming response."""

    streaming_response = await chatbot_service.process_query_with_agent(
        chat_query=chat_query,
        session=session,
        current_user=current_user,
    )
    return streaming_response
