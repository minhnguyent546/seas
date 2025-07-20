from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from app.deps import AsyncSessionDep, CurrentSuperuserDep
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
