from collections.abc import AsyncIterator
from datetime import datetime

from langchain_core.messages import (
    BaseMessageChunk,
    HumanMessage,
    SystemMessage,
)

import app.utils as app_utils
from app.chatbot.schemas import DocumentTag
from app.core.config import settings
from app.rag.schemas import SimilaritySearchParams
from app.rag.service import RagService


class RagChatLLM:
    def __init__(self, rag_service: RagService):
        self.llm = app_utils.get_langchain_llm(
            model_name=settings.CHAT_MODEL,
            temperature=0,
        )
        self.rag_service = rag_service

        self.system_prompt = app_utils.get_prompt(
            template_name="system_prompt_vi.j2",
            currentDateTime=datetime.now().strftime("ngày %d tháng %m năm %Y"),
            currentYear=datetime.now().year,
        )
        self.chat_prompt_template = app_utils.get_prompt_template(
            template_name="chat_prompt.j2"
        )

    async def astream(
        self,
        query: str,
    ) -> AsyncIterator[BaseMessageChunk]:
        context_chunks = await self.rag_service.similarity_search(
            search_params=SimilaritySearchParams(
                query=query,
                limit=settings.SIMILARITY_SEARCH_TOP_K,
                threshold=settings.SIMILARITY_SEARCH_THRESHOLD,
                rerank=settings.RERANK_ENABLED,
                sort_by_score=True,
            )
        )

        document_tags = [
            DocumentTag(
                title=chunk.chunk_metadata.get("title") or "",
                url=chunk.chunk_metadata.get("url") or "",
                description=chunk.chunk_metadata.get("description") or "",
                content=chunk.content,
            )
            for chunk in context_chunks
        ]
        context_str = "\n".join([
            doc_tag.to_html() for doc_tag in document_tags
        ])

        chat_prompt = self.chat_prompt_template.render(
            context=context_str,
            query=query,
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=chat_prompt),
        ]

        async for chunk in self.llm.astream(input=messages):
            yield chunk
