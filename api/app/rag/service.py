import os
import uuid
from typing import Any

import frontmatter
from fastapi import HTTPException, UploadFile, status
from langchain_core.documents import Document as LangchainDocument
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSession
from app.rag.models import (
    DocumentSection,
    DocumentSectionChunk,
)
from app.rag.schemas import DocumentSectionChunkPublic, SimilaritySearchParams
from app.schemas import MessageResponse
from app.utils import save_uploaded_file


class RagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.__qdrant_client: AsyncQdrantClient | None = None
        self.__embeddings: Embeddings | None = None
        self.__vector_store: QdrantVectorStore | None = None

    @property
    def _qdrant_client(self) -> AsyncQdrantClient:
        if self.__qdrant_client is None:
            self.__qdrant_client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
            )
        return self.__qdrant_client

    @property
    def _embeddings(self) -> Embeddings:
        if self.__embeddings is None:
            self.__embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,  # pyright: ignore[reportArgumentType]
            )
        return self.__embeddings

    async def _initialize_qdrant_collection(self) -> bool:
        try:
            collections = await self._qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                await self._qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}"
                )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            return False

    def _split_markdown_on_header(
        self, md_file_path: str
    ) -> list[LangchainDocument]:
        """Split document based on markdown headers."""
        headers = [
            ("#", "header_1"),
            ("##", "header_2"),
            ("###", "header_3"),
            ("####", "header_4"),
            ("#####", "header_5"),
            ("######", "header_6"),
        ]
        md_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers, strip_headers=False
        )
        # TODO: consider prepend all headers to the content

        with open(md_file_path, "r", encoding="utf-8") as f:
            md_content = frontmatter.load(f)

        metadata = {
            "title": md_content.get("title"),
            "url": md_content.get("url")
            or md_content.get("source")
            or md_content.get("sourceURL"),
            "description": md_content.get("description"),
        }
        content = md_content.content

        docs = md_header_splitter.split_text(content)
        for doc in docs:
            doc.metadata.update(metadata)

        return docs

    def _split_document_recursive(
        self, content: str, metadata: dict[str, Any]
    ) -> list[LangchainDocument]:
        """Split document using recursive character text splitter."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

        docs = text_splitter.create_documents(
            texts=[content], metadatas=[metadata]
        )
        return docs

    async def similarity_search(
        self, search_params: SimilaritySearchParams
    ) -> list[DocumentSectionChunkPublic]:
        try:
            # search in Qdrant
            query_vector = await self._embeddings.aembed_query(
                search_params.query
            )
            search_results = await self._qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                limit=search_params.limit,
                score_threshold=search_params.threshold,
            )

            # get chunk
            chunk_ids = [result.id for result in search_results]
            if not chunk_ids:
                return []

            document_section_chunks_result = await self.session.execute(
                select(DocumentSectionChunk).where(
                    DocumentSectionChunk.qdrant_point_id.in_(chunk_ids)
                )
            )
            document_section_chunks = (
                document_section_chunks_result.scalars().all()
            )
            document_section_chunks_public = [
                DocumentSectionChunkPublic.model_validate(chunk)
                for chunk in document_section_chunks
            ]
            for i, chunk in enumerate(document_section_chunks_public):
                chunk.similarity_score = search_results[i].score

            return document_section_chunks_public

        except Exception as err:
            logger.debug("Error during performing similarity search: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during performing similarity search: {err}",
            ) from err

    async def add_document_to_database(
        self, upload_file: UploadFile
    ) -> MessageResponse:
        if upload_file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing fielname in the uploaded file",
            )
        if not upload_file.filename.endswith((".md", ".markdown")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a markdown file",
            )

        saved_file_path = None
        try:
            saved_file_path = save_uploaded_file(file=upload_file)
            doc_sections = self._split_markdown_on_header(
                md_file_path=saved_file_path
            )

            # initialize Qdrant collection if not exists
            is_collection_created = await self._initialize_qdrant_collection()
            if not is_collection_created:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create Qdrant collection",
                )

            qdrant_points = []
            doc_section_chunk_dbs: list[DocumentSectionChunk] = []
            for doc_section in doc_sections:
                doc_section_id = str(uuid.uuid4())
                document_section_db = DocumentSection(
                    id=doc_section_id,
                    title=doc_section.metadata.get("title"),
                    url=doc_section.metadata.get("url"),
                    description=doc_section.metadata.get("description"),
                )
                self.session.add(document_section_db)

                doc_section_chunks = self._split_document_recursive(
                    content=doc_section.page_content,
                    metadata=doc_section.metadata,
                )
                for i, doc_section_chunk in enumerate(doc_section_chunks):
                    chunk_id = str(uuid.uuid4())
                    document_section_chunk_db = DocumentSectionChunk(
                        id=chunk_id,
                        document_section_id=doc_section_id,
                        content=doc_section_chunk.page_content,
                        chunk_index=i,
                        qdrant_point_id=chunk_id,
                        metadata={},  # TODO: where should we store all the metadata? DocumentSection or DocumentSectionChunk?
                    )
                    doc_section_chunk_dbs.append(document_section_chunk_db)

                    # embeddings and qdrants points
                    # TODO: consider embedding in batch
                    embedding = await self._embeddings.aembed_query(
                        doc_section_chunk.page_content
                    )
                    qdrant_points.append(
                        PointStruct(id=chunk_id, vector=embedding, payload={})
                    )

            # batch upsert to Qdrant
            if qdrant_points:
                logger.debug("Adding points to Qdrant...")
                await self._qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=qdrant_points,
                )
                # TODO: how to rollback if upsert fails?
                logger.debug(f"Added {len(qdrant_points)} points to Qdrant")

            self.session.add_all(doc_section_chunk_dbs)
            await self.session.commit()

            return MessageResponse(
                message=f"Document {upload_file.filename} added to the databases",
                extra={
                    "config": {
                        "chunk_size": settings.CHUNK_SIZE,
                        "chunk_overlap": settings.CHUNK_OVERLAP,
                    },
                    "num_doc_sections": len(doc_sections),
                    "num_doc_section_chunks": len(doc_section_chunk_dbs),
                    "num_qdrant_points": len(qdrant_points),
                },
            )
        except Exception as err:
            if saved_file_path is not None and os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            logger.error(f"Failed to add document: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add document: {err}",
            ) from err
