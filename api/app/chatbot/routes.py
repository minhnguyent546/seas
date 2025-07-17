from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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


@router.post("/query", response_class=StreamingResponse)
async def query(
    chat_query: ChatQuery,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """ "Process a chat query and return a streaming response."""

    # streaming response with custom callback handler: https://gist.github.com/ninely/88485b2e265d852d3feb8bd115065b1a
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=chat_query.query),
    ]
    logger.debug(f"Processing query: {chat_query.query = }")

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in llm.astream(input=messages):
                if not hasattr(chunk, "content") or not chunk.content:
                    continue

                if isinstance(chunk.content, str):
                    yield chunk.content
                elif isinstance(chunk.content, list):  # pyright: ignore[reportUnnecessaryIsInstance]
                    for item in chunk.content:
                        if isinstance(item, str):
                            yield item
                        elif isinstance(item, dict) and "text" in item:  # pyright: ignore[reportUnnecessaryIsInstance]
                            yield item["text"]
                        else:
                            raise AssertionError(
                                f"Unexpected item type in chunk.content: {type(item)}. Expected str or dict with 'text' key."
                            )
                else:
                    raise AssertionError(
                        f"Unexpected chunk type: {type(chunk.content)}. Expected str or list of str/dict."
                    )

        except Exception as err:
            logger.error(f"Error in streaming: {err}")
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing your request: {str(err)}",
            ) from err

    return StreamingResponse(stream_generator(), media_type="text/plain")
