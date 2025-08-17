import asyncio
import json
import time
from collections.abc import AsyncGenerator
from io import StringIO

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.chatbot.rag_chat_llm import RagChatLLM
from app.chatbot.schemas import (
    ChatEvaluationResponse,
)
from app.chats.schemas import ChatMessageCreate
from app.chats.service import create_new_message
from app.core.database import AsyncSession
from app.rag.schemas import QueryParams
from app.schemas import Sender
from app.users.models import User
from app.utils import extract_content_from_base_message


async def process_query(
    query_params: QueryParams,
    session: AsyncSession,
    current_user: User,
) -> StreamingResponse:
    query_params.query = query_params.query.strip()
    if not query_params.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    if query_params.chat_session_id is not None:
        await create_new_message(
            session=session,
            chat_session_id=str(query_params.chat_session_id),
            chat_message_create=ChatMessageCreate(
                sender=Sender.USER, content=query_params.query
            ),
            user_id=str(current_user.id),
        )

    chat_llm = RagChatLLM()

    async def stream_generator() -> AsyncGenerator[str, None]:
        response_buffer = StringIO()
        try:
            async with asyncio.timeout(120):  # 2 minutes timeout
                async for chunk in chat_llm.astream(
                    session=session, query_params=query_params
                ):
                    chunk_content = extract_content_from_base_message(chunk)
                    if not chunk_content:
                        continue
                    yield chunk_content

                    response_buffer.write(chunk_content)

            final_response = response_buffer.getvalue()
            if (
                query_params.chat_session_id is not None
                and final_response.strip()
            ):
                response_message_db = await create_new_message(
                    session=session,
                    chat_session_id=str(query_params.chat_session_id),
                    chat_message_create=ChatMessageCreate(
                        sender=Sender.BOT, content=final_response
                    ),
                    user_id=str(current_user.id),
                )
                yield f"<metadata>{json.dumps({'message_id': str(response_message_db.id)})}</metadata>"

        except asyncio.TimeoutError as timeout_err:
            logger.error("Streaming timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request timeout. Please try again.",
            ) from timeout_err
        except Exception as err:
            logger.error(f"Error in streaming: {err}")
            # More specific error handling
            if "quota" in str(err).lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API quota exceeded. Please try again later.",
                ) from err
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your request.",
            ) from err
        finally:
            response_buffer.close()

    return StreamingResponse(stream_generator(), media_type="text/plain")


async def process_query_for_evaluation(
    query_params: QueryParams,
    session: AsyncSession,
    current_user: User,
) -> ChatEvaluationResponse:
    query_params.query = query_params.query.strip()
    if not query_params.query:
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
            session=session, query_params=query_params
        )

        end_time = time.perf_counter()
        total_response_time = end_time - start_time

        return ChatEvaluationResponse(
            query=query_params.query,
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
            query=query_params.query,
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
            query=query_params.query,
            response="",
            retrieved_chunks=[],
            num_chunks_retrieved=0,
            reranked=False,
            response_time=time.perf_counter() - start_time,
            success=False,
            error=str(err),
        )
