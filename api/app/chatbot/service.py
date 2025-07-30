import asyncio
import time
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.chatbot.rag_chat_llm import RagChatLLM
from app.chatbot.schemas import (
    ChatEvaluationResponse,
    ChatQuery,
)
from app.core.database import AsyncSession
from app.users.models import User
from app.utils import extract_content_from_base_message


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
                    chunk_content = extract_content_from_base_message(chunk)
                    if not chunk_content:
                        continue
                    yield chunk_content

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


async def process_query_for_evaluation(
    chat_query: ChatQuery,
    session: AsyncSession,
    current_user: User,
) -> ChatEvaluationResponse:
    human_message = chat_query.query.strip()
    if not human_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    start_time = time.perf_counter()

    try:
        chat_llm = RagChatLLM()

        # Stream response while collecting metadata
        (
            similarity_search_result,
            complete_response,
            _llm_response_time,
            time_to_first_chunk,
        ) = await chat_llm.astream_for_evaluation(
            session=session, query=human_message
        )

        end_time = time.perf_counter()
        total_response_time = end_time - start_time

        return ChatEvaluationResponse(
            query=human_message,
            response=complete_response,
            retrieved_chunks=similarity_search_result.chunks,
            num_chunks_retrieved=len(similarity_search_result.chunks),
            reranked=similarity_search_result.reranked,
            response_time=total_response_time,
            time_to_first_chunk=time_to_first_chunk,
            query_expansion_time=similarity_search_result.query_expansion_time,
            embedding_time=similarity_search_result.embedding_time,
            similarity_search_time=similarity_search_result.similarity_search_time,
            chunk_retrieval_time=similarity_search_result.chunk_retrieval_time,
            rerank_time=similarity_search_result.rerank_time,
            success=True,
        )

    except asyncio.TimeoutError:
        logger.error("Evaluation timeout")
        return ChatEvaluationResponse(
            query=human_message,
            response="",
            retrieved_chunks=[],
            num_chunks_retrieved=0,
            reranked=False,
            response_time=time.perf_counter() - start_time,
            success=False,
            error="Request timeout. Please try again.",
        )
    except Exception as err:
        logger.error(f"Error in evaluation: {err}")
        return ChatEvaluationResponse(
            query=human_message,
            response="",
            retrieved_chunks=[],
            num_chunks_retrieved=0,
            reranked=False,
            response_time=time.perf_counter() - start_time,
            success=False,
            error=str(err),
        )
