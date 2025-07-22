import os
import uuid
from typing import Any

import frontmatter
from fastapi import HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from langchain_core.documents import Document as LangchainDocument
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.utils as app_utils
from app.core.config import settings
from app.core.database import AsyncSession
from app.rag.models import (
    DocumentSection,
    DocumentSectionChunk,
)
from app.rag.schemas import DocumentSectionChunkPublic, SimilaritySearchParams
from app.schemas import MessageResponse
from app.templates import prompt_templates


class RagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.__qdrant_client: AsyncQdrantClient | None = None
        self.__embeddings: Embeddings | None = None

        self.TABLE_TOK = "<table_title>"
        self.TABLE_HEADER_SYMBOL = "#######"
        self.header_mapping = [
            ("#", "<header_1>"),
            ("##", "<header_2>"),
            ("###", "<header_3>"),
            ("####", "<header_4>"),
            ("#####", "<header_5>"),
            ("######", "<header_6>"),
            (self.TABLE_HEADER_SYMBOL, self.TABLE_TOK),
        ]
        self.header_to_symbol = {
            header[1]: header[0] for header in self.header_mapping
        }

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
        """Split document based on markdown headers. Return list of document sections."""

        md_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.header_mapping
        )

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

        # process table in each document sections, treat table as separate document sections
        sections = md_header_splitter.split_text(content)
        return_sections: list[LangchainDocument] = []
        for section in sections:
            section.metadata.update(metadata)
            new_sections = self._process_table_in_document_section(section)
            return_sections.extend(new_sections)

        return return_sections

    def _split_document_recursive(
        self,
        content: str,
        metadata: dict[str, Any],
        prepend_headers: bool = True,
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

        if prepend_headers:
            # prepend headers to the content
            for doc in docs:
                header_content: list[str] = []
                for header_key, header_value in doc.metadata.items():
                    header_value = header_value.strip()[
                        :256
                    ]  # incase the header value is too long
                    if header_key in self.header_to_symbol:
                        header_content.append(
                            f"{self.header_to_symbol[header_key]} {header_value}"
                        )

                if header_content:
                    doc.page_content = (
                        "\n\n".join(header_content) + "\n\n" + doc.page_content
                    )

        return docs

    def _summarize_table(self, table_md_content: str, retries: int = 3) -> str:
        table_summary_llm = app_utils.get_langchain_llm(
            model_name=settings.TABLE_SUMMARY_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

        retry_remaining = retries
        prompt_template = prompt_templates.get_template("table_description.j2")
        prompt = prompt_template.render(tableContent=table_md_content)
        while True:
            try:
                response = table_summary_llm.invoke(prompt)
                if isinstance(response, str):
                    return response
                elif hasattr(response, "content") and isinstance(
                    response.content, str
                ):
                    return response.content
                else:
                    raise RuntimeError(
                        f"Unable to infer response content from {response}"
                    )
            except Exception as err:
                if retry_remaining > 0:
                    retry_remaining -= 1
                    continue
                else:
                    logger.error(
                        f"Failed to get table description after {retries} retries"
                    )
                    raise err

    def _extract_table_title(self, summarized_table: str) -> tuple[str, str]:
        lines = summarized_table.strip().split("\n")
        if lines and lines[0].startswith(self.TABLE_HEADER_SYMBOL):
            # Remove the ####### prefix and strip whitespace
            title = lines[0].replace(self.TABLE_HEADER_SYMBOL, "").strip()
            return title, "\n".join(lines[1:])
        return "", summarized_table

    def _process_table_in_document_section(
        self, document_section: LangchainDocument
    ) -> list[LangchainDocument]:
        """Treat table in document section as a new document section. Return list of new document sections."""
        try:
            section_metadata = document_section.metadata
            new_document_sections: list[LangchainDocument] = []
            new_content, table_contents = app_utils.extract_markdown_tables(
                document_section.page_content, remove_tables=True
            )
            new_document_sections.append(
                LangchainDocument(
                    page_content=new_content, metadata=section_metadata
                )
            )

            if table_contents:
                for table_content in table_contents:
                    summarized_table = self._summarize_table(table_content)

                    table_title, summarized_table = self._extract_table_title(
                        summarized_table
                    )
                    table_mdatadata = section_metadata
                    if table_title:
                        table_mdatadata[self.TABLE_TOK] = table_title
                    new_document_sections.append(
                        LangchainDocument(
                            page_content=summarized_table,
                            metadata=table_mdatadata,
                        )
                    )

            return new_document_sections

        except Exception as err:
            logger.error(f"Failed to process table in document section: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process table in document section: {err}",
            ) from err

    async def split_markdown_on_headers(self, upload_file: UploadFile):
        if upload_file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing filename in the uploaded file",
            )
        if not upload_file.filename.endswith((".md", ".markdown")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a markdown file",
            )

        saved_file_path = None
        try:
            saved_file_path = app_utils.save_uploaded_file(file=upload_file)
            docs = self._split_markdown_on_header(md_file_path=saved_file_path)

            return_docs = []
            for doc in docs:
                return_docs.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                })

            return JSONResponse(
                content={
                    "num_docs": len(docs),
                    "docs": return_docs,
                }
            )
        except Exception as err:
            logger.error(f"Failed to split markdown on headers: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to split markdown on headers: {err}",
            ) from err
        finally:
            if saved_file_path is not None and os.path.exists(saved_file_path):
                os.remove(saved_file_path)

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
                select(DocumentSectionChunk)
                .where(DocumentSectionChunk.qdrant_point_id.in_(chunk_ids))
                .options(selectinload(DocumentSectionChunk.document_section))
            )
            document_section_chunks = (
                document_section_chunks_result.scalars().all()
            )
            for document_section_chunk in document_section_chunks:
                document_section_chunk.chunk_metadata.update({
                    "title": document_section_chunk.document_section.title,
                    "url": document_section_chunk.document_section.url,
                    "description": document_section_chunk.document_section.description,
                })
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
                detail="Missing filename in the uploaded file",
            )
        if not upload_file.filename.endswith((".md", ".markdown")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a markdown file",
            )

        saved_file_path = None
        try:
            saved_file_path = app_utils.save_uploaded_file(file=upload_file)
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
                    prepend_headers=True,
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
