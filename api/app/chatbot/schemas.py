from html import escape as html_escape
from typing import Annotated

from pydantic import BaseModel, Field

from app.rag.schemas import DocumentSectionChunkPublic


class ChatQuery(BaseModel):
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


class DocumentTag(BaseModel):
    title: str
    url: str
    description: str
    content: str

    def to_html(self) -> str:
        return f'<Document title="{html_escape(self.title)}" url="{html_escape(self.url)}" description="{html_escape(self.description)}">{html_escape(self.content)}</Document>'


class ChatEvaluationResponse(BaseModel):
    query: str
    response: str
    retrieved_chunks: list[DocumentSectionChunkPublic]
    num_chunks_retrieved: int
    reranked: bool

    response_time: Annotated[
        float,
        Field(description="Total time taken to process the query"),
    ]
    time_to_first_chunk: Annotated[
        float | None,
        Field(description="Time taken to get the first chunk of the response"),
    ] = None
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

    success: bool
    error: str | None = None
