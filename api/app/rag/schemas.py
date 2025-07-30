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
    expand_query: Annotated[
        bool,
        Field(
            description="Whether to expand the query using LLM and apply query fusion with Reciprocal Rank Fusion (RRF)"
        ),
    ] = True
    rerank: Annotated[
        bool, Field(description="Whether to rerank the retrieved chunks")
    ] = True
    sort_by_score: Annotated[
        bool,
        Field(description="Whether to sort the retrieved chunks by score"),
    ] = True


class SimilaritySearchResult(BaseModel):
    num_chunks: int
    reranked: bool
    query: str
    expanded_queries: list[str] | None = None
    chunks: list[DocumentSectionChunkPublic]

    query_expansion_time: Annotated[
        float | None,
        Field(description="Time taken to expand the query using LLM"),
    ] = None
    embedding_time: Annotated[
        float | None,
        Field(description="Time taken to embed the query using LLM"),
    ] = None
    similarity_search_time: Annotated[
        float | None,
        Field(
            description="Time taken to search for similar chunks in the database"
        ),
    ] = None
    chunk_retrieval_time: Annotated[
        float | None,
        Field(
            description="Time taken to retrieve the chunks from the database"
        ),
    ] = None
    rerank_time: Annotated[
        float | None, Field(description="Time taken to rerank the chunks")
    ] = None
    total_time: Annotated[
        float, Field(description="Total time taken to process the query")
    ]
