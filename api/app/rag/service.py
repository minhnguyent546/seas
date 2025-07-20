import os
import uuid
from typing import Any

import frontmatter
from fastapi import HTTPException, UploadFile, status
from langchain_core.documents import Document as LangchainDocument
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.core.database import AsyncSession
from app.rag.models import (
    DocumentSection,
    DocumentSectionChunk,
)
from app.schemas import MessageResponse
from app.utils import save_uploaded_file


class RagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.__qdrant_client: QdrantClient | None = None
        self.__embeddings: Embeddings | None = None
        self.__vector_store: QdrantVectorStore | None = None

    @property
    def _qdrant_client(self) -> QdrantClient:
        if self.__qdrant_client is None:
            self.__qdrant_client = QdrantClient(
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
                google_api_key=settings.GOOGLE_API_KEY,
            )
        return self.__embeddings

    @property
    def _vector_store(self) -> QdrantVectorStore:
        if self.__vector_store is None:
            self.__vector_store = QdrantVectorStore(
                client=self._qdrant_client,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                retrieval_model=RetrievalMode.DENSE,  # TODO: change me
                embedding=self._embeddings,
            )
        return self.__vector_store

    def _initialize_qdrant_collection(self) -> bool:
        try:
            collections = self._qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                self._qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=Distance.DOT,
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

    async def add_document_to_database(
        self, upload_file: UploadFile
    ) -> MessageResponse:
        if not upload_file.filename.endswith((".md", ".markdown")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a markdown file",
            )

        try:
            saved_file_path = save_uploaded_file(file=upload_file)
            doc_sections = self._split_markdown_on_header(
                md_file_path=saved_file_path
            )

            # initialize Qdrant collection if not exists
            is_collection_created = self._initialize_qdrant_collection()
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
                self._qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=qdrant_points,
                )
                # TODO: how to rollback if upsert fails?
                logger.debug(f"Added {len(qdrant_points)} points to Qdrant")

            self.session.add_all(doc_section_chunk_dbs)
            await self.session.commit()
            await self.session.refresh(document_section_db)

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
            os.remove(saved_file_path)
            logger.error(f"Failed to add document: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add document: {err}",
            ) from err
