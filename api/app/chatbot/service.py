import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

import app.utils as app_utils
from app.chatbot.schemas import ChatQuery
from app.core.config import settings
from app.core.database import AsyncSession
from app.rag.schemas import SimilaritySearchParams
from app.rag.service import RagService
from app.templates import prompt_templates
from app.users.models import User

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


async def process_query(
    chat_query: ChatQuery,
    session: AsyncSession,
    current_user: User,
) -> StreamingResponse:
    llm = app_utils.get_langchain_llm(
        model_name=settings.CHAT_MODEL,
        temperature=0,
    )

    human_message = chat_query.query.strip()
    if not human_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    # get prompt templates
    system_prompt_template = prompt_templates.get_template(
        "system_prompt_vi.j2"
    )
    chat_prompt_template = prompt_templates.get_template("chat_prompt.j2")
    system_prompt = system_prompt_template.render(
        currentDateTime=datetime.now().strftime("ngày %d tháng %m năm %Y"),
        currentYear=datetime.now().year,
    )

    # similarity search
    rag_service = RagService(session=session)
    context = await rag_service.similarity_search(
        search_params=SimilaritySearchParams(
            query=human_message,
            limit=settings.SIMILARITY_SEARCH_TOP_K,
            threshold=settings.SIMILARITY_SEARCH_THRESHOLD,
        )
    )
    context_str = "\n".join([
        f"{i + 1}. {chunk.content}\n" for i, chunk in enumerate(context)
    ])
    chat_prompt = chat_prompt_template.render(
        context=context_str,
        query=human_message,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=chat_prompt),
    ]
    logger.debug(f"Processing query: {human_message = }")

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            async with asyncio.timeout(120):  # 2 minutes timeout
                async for chunk in llm.astream(input=messages):
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
