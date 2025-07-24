from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentSectionChunkPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    chunk_index: int
    chunk_metadata: dict[str, Any]
    similarity_score: float | None = None


class SimilaritySearchParams(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=2048)]
    limit: Annotated[int, Field(ge=1, le=100)] = 3
    threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.6


class SimilaritySearchResult(BaseModel):
    num_chunks: int
    chunks: list[DocumentSectionChunkPublic]
    query: str
