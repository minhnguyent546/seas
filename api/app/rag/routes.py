import json
from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    UploadFile,
)
from fastapi.responses import JSONResponse, Response

from app.core.config import timezone_vi
from app.deps import (
    AsyncSessionDep,
    get_current_superuser,
)
from app.rag.query_expansion_llm import QueryExpansionLLM
from app.rag.rag_models_manager import rag_models_manager
from app.rag.schemas import (
    SimilaritySearchParams,
    SimilaritySearchResult,
)
from app.rag.service import RagService
from app.schemas import MessageResponse

router = APIRouter(prefix="/rag", tags=["rag"])


def _get_rag_service() -> RagService:
    return RagService()


RagServiceDep = Annotated[RagService, Depends(_get_rag_service)]


@router.post(
    "/documents/upload",
    dependencies=[Depends(get_current_superuser)],
    response_model=MessageResponse,
)
async def add_document_to_database(
    file: Annotated[
        UploadFile, File(description="The document to add to the database")
    ],
    session: AsyncSessionDep,
    rag_service: RagServiceDep,
):
    """Add a document to the database(s). Requires superuser permissions."""
    return await rag_service.add_document_to_database(
        session=session, upload_file=file
    )


@router.post(
    "/documents/batch-upload",
    dependencies=[Depends(get_current_superuser)],
    response_model=MessageResponse,
)
async def add_document_to_database_in_batch(
    files: Annotated[
        list[UploadFile],
        File(description="The documents to add to the database"),
    ],
    session: AsyncSessionDep,
    rag_service: RagServiceDep,
):
    """Add a document to the database(s) in batch. Requires superuser permissions."""
    return await rag_service.add_documents_to_database_in_batch(
        session=session, upload_files=files
    )


@router.post(
    "/private/similarity-search",
    dependencies=[Depends(get_current_superuser)],
    response_model=SimilaritySearchResult,
)
async def similarity_search(
    search_params: SimilaritySearchParams,
    session: AsyncSessionDep,
    rag_service: RagServiceDep,
):
    """Similarity search for a query. Requires superuser permissions."""
    result = await rag_service.similarity_search(
        session=session, search_params=search_params
    )
    return result


@router.post(
    "/private/split-markdown-on-headers",
    dependencies=[Depends(get_current_superuser)],
    response_class=JSONResponse,
)
async def split_markdown_on_headers(
    file: Annotated[
        UploadFile, File(description="The document to split on headers")
    ],
    rag_service: RagServiceDep,
):
    """Split a document on headers. Requires superuser permissions."""
    return await rag_service.split_markdown_on_headers(upload_file=file)


@router.post(
    "/private/query-expansion",
    dependencies=[Depends(get_current_superuser)],
    response_class=JSONResponse,
)
async def query_expansion(
    query: Annotated[str, Body(description="The query to expand", embed=True)],
):
    """Query expansion. Requires superuser permissions."""
    query_expansion_llm = QueryExpansionLLM()
    queries = await query_expansion_llm.expand_query(query)
    return {
        "original_query": query,
        "num_new_queries": len(queries),
        "new_queries": queries,
    }


@router.get(
    "/private/export-document-sections-chunks",
    dependencies=[Depends(get_current_superuser)],
    response_class=Response,
)
async def export_document_sections_chunks(
    session: AsyncSessionDep,
    rag_service: RagServiceDep,
):
    """Export document sections chunks to a JSON file. Requires superuser permissions."""

    export_data = await rag_service.export_document_sections_chunks(
        session=session
    )

    json_content = json.dumps(export_data, indent=2, ensure_ascii=False)

    timestamp = datetime.now(tz=timezone_vi).strftime("%Y%m%d_%H%M%S")
    filename = f"document_sections_chunks_export_{timestamp}.json"

    return Response(
        content=json_content.encode("utf-8"),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )


@router.get(
    "/private/rag-models-status",
    dependencies=[Depends(get_current_superuser)],
    response_class=JSONResponse,
)
async def get_rag_models_status():
    """Get the status of RAG models initialization. Requires superuser permissions."""

    return {
        "status": rag_models_manager.get_status(),
        "timestamp": datetime.now().isoformat(),
    }
