from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import app.chatbot.service as chatbot_service
from app.deps import AsyncSessionDep, CurrentActiveUserDep
from app.rag.schemas import QueryParams

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_class=StreamingResponse)
async def query(
    query_params: QueryParams,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Process a chat query and return a streaming response."""

    streaming_response = await chatbot_service.process_query(
        query_params=query_params,
        session=session,
        current_user=current_user,
    )
    return streaming_response


@router.post("/query-eval")
async def query_eval(
    query_params: QueryParams,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Process a chat query and return complete response with evaluation metadata."""

    eval_response = await chatbot_service.process_query_for_evaluation(
        query_params=query_params,
        session=session,
        current_user=current_user,
    )
    return eval_response
