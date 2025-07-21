from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from fastapi.responses import JSONResponse

from app.deps import (
    AsyncSessionDep,
    CurrentSuperuserDep,
    get_current_superuser,
)
from app.rag.schemas import (
    DocumentSectionChunkPublic,
    SimilaritySearchParams,
    SimilaritySearchResult,
)
from app.rag.service import RagService
from app.schemas import MessageResponse

router = APIRouter(prefix="/rag", tags=["rag"])


def _get_rag_service(session: AsyncSessionDep) -> RagService:
    return RagService(session=session)


RagServiceDep = Annotated[RagService, Depends(_get_rag_service)]


@router.post("/documents/upload", response_model=MessageResponse)
async def add_document_to_database(
    file: Annotated[
        UploadFile, File(description="The document to add to the database")
    ],
    rag_service: RagServiceDep,
    current_user: CurrentSuperuserDep,
):
    """Add a document to the database(s). Requires superuser permissions."""
    return await rag_service.add_document_to_database(file)


@router.post(
    "/private/similarity-search",
    dependencies=[Depends(get_current_superuser)],
    response_model=SimilaritySearchResult,
)
async def similarity_search(
    search_params: SimilaritySearchParams, rag_service: RagServiceDep
):
    """Similarity search for a query. Requires superuser permissions."""
    result = await rag_service.similarity_search(search_params)
    return SimilaritySearchResult(
        chunks=[
            DocumentSectionChunkPublic.model_validate(chunk)
            for chunk in result
        ],
        query=search_params.query,
    )


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
    return await rag_service.split_markdown_on_headers(file)
