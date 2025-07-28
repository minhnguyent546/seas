import asyncio
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.chatbot.rag_chat_llm import RagChatLLM
from app.chatbot.schemas import ChatQuery
from app.core.database import AsyncSession
from app.users.models import User


async def process_query(
    chat_query: ChatQuery,
    session: AsyncSession,
    current_user: User,
) -> StreamingResponse:
    human_message = chat_query.query.strip()
    if not human_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )
    chat_llm = RagChatLLM()

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            async with asyncio.timeout(120):  # 2 minutes timeout
                async for chunk in chat_llm.astream(
                    session=session, query=human_message
                ):
                    if isinstance(chunk, str):
                        yield chunk
                        continue

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
        except asyncio.TimeoutError as timeout_err:
            logger.error("Streaming timeout")
            raise HTTPException(
                status_code=504,
                detail="Request timeout. Please try again.",
            ) from timeout_err
        except Exception as err:
            logger.error(f"Error in streaming: {err}")
            # More specific error handling
            if "quota" in str(err).lower():
                raise HTTPException(
                    status_code=429,
                    detail="API quota exceeded. Please try again later.",
                ) from err
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request.",
            ) from err

    return StreamingResponse(stream_generator(), media_type="text/plain")
