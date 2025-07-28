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
    get_current_superuser,
)
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
