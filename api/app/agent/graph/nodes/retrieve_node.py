from html import escape as html_escape
from typing import Any

from loguru import logger

from app.agent.graph.state import GraphState
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.rag.schemas import SimilaritySearchParams
from app.rag.service import RagService


async def retrieve_node(state: GraphState) -> dict[str, Any]:
    try:
        async with AsyncSessionLocal() as session:
            rag_service = RagService(session=session)
            question = state["question"]

            doc_section_chunks = await rag_service.similarity_search(
                search_params=SimilaritySearchParams(
                    query=question,
                    limit=settings.SIMILARITY_SEARCH_TOP_K,
                    threshold=settings.SIMILARITY_SEARCH_THRESHOLD,
                )
            )

            formatted_docs: list[str] = [
                f'<Document title="{html_escape(chunk.chunk_metadata.get("title") or "")}" url="{html_escape(chunk.chunk_metadata.get("url") or "")}">{html_escape(chunk.content)}</Document>\n'
                for chunk in doc_section_chunks
            ]
            return {"documents": formatted_docs}
    except Exception as err:
        logger.error(f"Error during document retrieval: {err}")
        raise err
