import time
from collections.abc import AsyncIterator
from datetime import datetime

from langchain_core.messages import (
    BaseMessageChunk,
    HumanMessage,
    SystemMessage,
)
from loguru import logger

import app.utils as app_utils
from app.chatbot.schemas import DocumentTag
from app.core.config import settings
from app.core.database import AsyncSession
from app.rag.schemas import SimilaritySearchParams
from app.rag.service import RagService


class RagChatLLM:
    def __init__(self):
        self.llm = app_utils.get_langchain_llm(
            model_name=settings.CHAT_MODEL,
            temperature=0,
        )
        self._rag_service: RagService | None = None

        self.system_prompt = app_utils.get_prompt(
            template_name="chat_system_prompt.j2",
            currentDateTime=datetime.now().strftime("ngày %d tháng %m năm %Y"),
            currentYear=datetime.now().year,
        )
        self.human_prompt_template = app_utils.get_prompt_template(
            template_name="chat_human_prompt.j2"
        )

    @property
    def rag_service(self) -> RagService:
        if self._rag_service is None:
            self._rag_service = RagService()
        return self._rag_service

    async def astream(
        self,
        session: AsyncSession,
        query: str,
    ) -> AsyncIterator[BaseMessageChunk]:
        similarity_search_result = await self.rag_service.similarity_search(
            session=session,
            search_params=SimilaritySearchParams(
                query=query,
                limit=settings.SIMILARITY_SEARCH_TOP_K,
                threshold=settings.SIMILARITY_SEARCH_THRESHOLD,
                rerank=settings.RERANK_ENABLED,
                sort_by_score=True,
            ),
        )

        document_tags = [
            DocumentTag(
                title=chunk.chunk_metadata.get("title") or "",
                url=chunk.chunk_metadata.get("url") or "",
                description=chunk.chunk_metadata.get("description") or "",
                content=chunk.content,
            )
            for chunk in similarity_search_result.chunks
        ]
        context_str = "\n".join([
            doc_tag.to_html() for doc_tag in document_tags
        ])

        human_prompt = self.human_prompt_template.render(
            context=context_str,
            query=query,
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt),
        ]

        _start_response_time = time.perf_counter()
        _time_to_first_chunk = None
        async for chunk in self.llm.astream(input=messages):
            if _time_to_first_chunk is None:
                _time_to_first_chunk = (
                    time.perf_counter() - _start_response_time
                )
                logger.debug(
                    f"Time to first chunk: {_time_to_first_chunk:.2f} seconds"
                )
                logger.debug(f"{chunk = }")
            yield chunk
