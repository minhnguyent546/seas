import uuid
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field
from qdrant_client import models as qdrant_models


class DocumentSectionChunkPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    chunk_index: int
    chunk_metadata: dict[str, Any]
    similarity_score: float | None = None


class QueryParams(BaseModel):
    query: Annotated[
        str,
        Field(
            min_length=1,
            max_length=2048,
            description="The user's chat query",
            examples=[
                "Thời gian đăng ký xét tuyển đại học chính quy năm 2025 là khi nào?"
            ],
        ),
    ]
    limit: Annotated[
        int, Field(ge=1, le=100, description="Number of chunks to retrieve")
    ] = 10
    threshold: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Threshold for similarity search"),
    ] = 0.4
    num_new_queries: Annotated[
        int,
        Field(
            description="Number of new queries to expand the query. Less than 1 means no expansion."
        ),
    ] = 3
    rerank: Annotated[
        bool, Field(description="Whether to rerank the retrieved chunks")
    ] = True
    chat_session_id: Annotated[
        uuid.UUID | None,
        Field(
            description="The ID of the chat session. If provided, the query and response will be added to the chat session as new messages."
        ),
    ] = None


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
    total_sim_search_time: Annotated[
        float, Field(description="Total time taken to process the query")
    ]


class RecomputeEmbeddingsParams(BaseModel):
    qdrant_db_name: Annotated[
        str,
        Field(
            description="The name of the Qdrant database to compute embeddings for"
        ),
    ]
    embeddings_size: Annotated[
        int,
        Field(description="The size of the embeddings to compute"),
    ]
    distance_function: Annotated[
        qdrant_models.Distance,
        Field(description="The distance function to use for the embeddings"),
    ]
