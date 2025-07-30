import os
import time
import uuid
from datetime import datetime
from typing import Any

import frontmatter
import qdrant_client.models as qdrant_models
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
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.utils as app_utils
from app.core.config import settings, timezone_vi
from app.core.database import AsyncSession
from app.rag.models import (
    DocumentSection,
    DocumentSectionChunk,
)
from app.rag.query_expansion_llm import QueryExpansionLLM
from app.rag.schemas import (
    DocumentSectionChunkPublic,
    SimilaritySearchParams,
    SimilaritySearchResult,
)
from app.schemas import MessageResponse

# Optional import for FlagEmbedding (reranking functionality)
try:
    from FlagEmbedding import FlagReranker

    _has_reranker = True
except ImportError:
    FlagReranker = None  # type: ignore
    _has_reranker = False


class RagService:
    def __init__(self) -> None:
        self.__qdrant_client: AsyncQdrantClient | None = None
        self.__embeddings: Embeddings | None = None
        self.__reranker: Any = None

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

    @property
    def _reranker(self) -> Any:
        if not _has_reranker:
            return None

        if self.__reranker is None:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.__reranker = FlagReranker(  # type: ignore
                model_name_or_path=settings.BAAI_RERANKER_MODEL,
                use_fp16=True,
                device=device,
            )
        return self.__reranker

    async def _initialize_qdrant_collection(self) -> bool:
        try:
            collections = await self._qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                await self._qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=qdrant_models.Distance.COSINE,
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
            try:
                md_content = frontmatter.load(f)
                metadata = {
                    "title": md_content.get("title"),
                    "url": md_content.get("url")
                    or md_content.get("source")
                    or md_content.get("sourceURL"),
                    "description": md_content.get("description"),
                }
                content = md_content.content
            except Exception as frontmatter_err:
                logger.error(
                    f"Failed to parse frontmatter in {md_file_path}: {frontmatter_err}. Treating as plain markdown."
                )
                raise RuntimeError(
                    f"Failed to parse frontmatter in {md_file_path}: {frontmatter_err}."
                ) from frontmatter_err

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
                    # Skip None values and ensure header_value is a string
                    if header_value is None:
                        continue
                    if not isinstance(header_value, str):
                        header_value = str(header_value)

                    header_value = header_value.strip()[
                        :256
                    ]  # incase the header value is too long
                    if header_key in self.header_to_symbol and header_value:
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
        prompt = app_utils.get_prompt(
            template_name="table_description.j2",
            tableContent=table_md_content,
        )
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
        if not summarized_table:
            return "", ""

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

    def _apply_reciprocal_rank_fusion(
        self,
        search_results_list: list[list[qdrant_models.ScoredPoint]],
        k: int = 60,
    ) -> list[qdrant_models.ScoredPoint]:
        """Apply Reciprocal Rank Fusion to combine multiple search result lists."""
        # Handle edge case: no results from any query
        if not search_results_list or all(
            not results for results in search_results_list
        ):
            return []

        rrf_scores: dict[str, dict[str, Any]] = {}

        for search_results in search_results_list:
            for rank, result in enumerate(search_results, start=1):
                doc_id = str(result.id)
                rrf_score = 1 / (k + rank)

                if doc_id in rrf_scores:
                    rrf_scores[doc_id]["score"] += rrf_score  # pyright: ignore[reportOperatorIssue]
                else:
                    rrf_scores[doc_id] = {  # pyright: ignore[reportArgumentType]
                        "score": rrf_score,
                        "result": result,
                    }

        # Sort by RRF score and return results
        sorted_results = sorted(
            rrf_scores.items(), key=lambda x: x[1]["score"], reverse=True
        )

        # Create result objects with RRF scores
        fused_results = []
        for _doc_id, data in sorted_results:
            result: qdrant_models.ScoredPoint = data["result"]
            # Update the score to be the RRF score
            result.score = data["score"]
            fused_results.append(result)

        return fused_results

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
            saved_file_path = app_utils.save_uploaded_document(
                file=upload_file
            )
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
        self, session: AsyncSession, search_params: SimilaritySearchParams
    ) -> SimilaritySearchResult:
        _time_dict: dict[str, Any] = {
            "query_expansion_time": None,
            "embedding_time": None,
            "similarity_search_time": None,
            "chunk_retrieval_time": None,
            "rerank_time": None,
            "total_time": None,
        }
        expanded_queries: list[str] | None = None
        try:
            _time_dict["total_time"] = time.perf_counter()
            logger.debug(f"{search_params = }")

            queries = [search_params.query]  # include the original query

            if (
                search_params.expand_query
                and settings.QUERY_EXPANSION_NUM_NEW_QUERIES > 0
            ):
                _time_dict["query_expansion_time"] = time.perf_counter()
                query_expansion_llm = QueryExpansionLLM()
                logger.info(
                    f"Expanding to {settings.QUERY_EXPANSION_NUM_NEW_QUERIES} for query: {search_params.query}"
                )
                expanded_queries = await query_expansion_llm.expand_query(
                    search_params.query
                )
                _time_dict["query_expansion_time"] = (
                    time.perf_counter() - _time_dict["query_expansion_time"]
                )
                if expanded_queries:
                    queries.extend(expanded_queries)
                    logger.debug(
                        f"Expanded {len(expanded_queries)} additional queries:"
                    )
                    for i, expanded_query in enumerate(expanded_queries):
                        logger.debug(f"{i + 1}. {expanded_query}")
                else:
                    logger.warning(
                        f"No expanded queries provided for {search_params.query}"
                    )

            # IMPORTANT:
            # For gemini embeddings, the vector produced by aembed_query is the same as the vector produced by aembed_documents
            # So, we can improve the performance by using aembed_documents instead of aembed_query
            # However, for other embeddings, this might not be the case!
            _time_dict["embedding_time"] = time.perf_counter()
            query_vectors = await self._embeddings.aembed_documents(queries)
            _time_dict["embedding_time"] = (
                time.perf_counter() - _time_dict["embedding_time"]
            )

            _time_dict["similarity_search_time"] = time.perf_counter()
            qdrant_search_results = await self._qdrant_client.search_batch(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                requests=[
                    qdrant_models.SearchRequest(
                        vector=query_vector,
                        limit=search_params.limit * 2,
                        score_threshold=search_params.threshold,
                    )
                    for query_vector in query_vectors
                ],
            )
            _time_dict["similarity_search_time"] = (
                time.perf_counter() - _time_dict["similarity_search_time"]
            )

            # Apply Reciprocal Rank Fusion (RRF) to combine results
            fused_qdrant_search_results = self._apply_reciprocal_rank_fusion(
                qdrant_search_results
            )

            # Limit to requested number of results
            fused_qdrant_search_results = fused_qdrant_search_results[
                : search_params.limit
            ]

            chunk_ids = [
                str(result.id) for result in fused_qdrant_search_results
            ]
            if not chunk_ids:
                _time_dict["total_time"] = (
                    time.perf_counter() - _time_dict["total_time"]
                )
                return SimilaritySearchResult(
                    num_chunks=0,
                    reranked=False,
                    chunks=[],
                    query=search_params.query,
                    **_time_dict,
                )

            _time_dict["chunk_retrieval_time"] = time.perf_counter()
            document_section_chunks_result = await session.execute(
                select(DocumentSectionChunk)
                .where(DocumentSectionChunk.qdrant_point_id.in_(chunk_ids))
                .options(selectinload(DocumentSectionChunk.document_section))
            )
            document_section_chunks = (
                document_section_chunks_result.scalars().all()
            )
            _time_dict["chunk_retrieval_time"] = (
                time.perf_counter() - _time_dict["chunk_retrieval_time"]
            )

            # Check if we got all expected chunks
            retrieved_chunk_ids = {
                str(chunk.qdrant_point_id) for chunk in document_section_chunks
            }
            missing_chunks = set(chunk_ids) - retrieved_chunk_ids
            if missing_chunks:
                logger.warning(f"Missing chunks in database: {missing_chunks}")

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

            score_map = {
                str(result.id): result.score
                for result in fused_qdrant_search_results
            }

            # reranking
            rerank_applied = False
            if search_params.rerank and settings.RERANK_ENABLED:
                reranker = self._reranker
                if reranker is not None:
                    _time_dict["rerank_time"] = time.perf_counter()
                    logger.debug(
                        f"Reranking {len(document_section_chunks_public)} chunks..."
                    )
                    rerank_docs = [
                        (search_params.query, chunk.content)
                        for chunk in document_section_chunks_public
                    ]
                    rerank_results = reranker.compute_score(
                        rerank_docs, batch_size=8, normalize=True
                    )
                    _time_dict["rerank_time"] = (
                        time.perf_counter() - _time_dict["rerank_time"]
                    )
                    assert rerank_results is not None
                    for i, chunk in enumerate(document_section_chunks_public):
                        chunk.similarity_score = rerank_results[i]

                    rerank_applied = True
                else:
                    logger.warning(
                        "Reranking requested but FlagEmbedding not available. "
                        "Install with: uv add --group rerank FlagEmbedding. "
                        "Falling back to fusion scores."
                    )
                    for chunk in document_section_chunks_public:
                        chunk.similarity_score = score_map.get(chunk.id, 0.0)
            else:
                # Use fusion scores (no reranking)
                for chunk in document_section_chunks_public:
                    chunk.similarity_score = score_map.get(chunk.id, 0.0)

            if search_params.sort_by_score:
                document_section_chunks_public.sort(
                    key=lambda doc_section_chunk: doc_section_chunk.similarity_score,  # pyright: ignore[reportArgumentType]
                    reverse=True,
                )

            _time_dict["total_time"] = (
                time.perf_counter() - _time_dict["total_time"]
            )
            return SimilaritySearchResult(
                num_chunks=len(document_section_chunks_public),
                reranked=rerank_applied,
                query=search_params.query,
                expanded_queries=expanded_queries,
                chunks=document_section_chunks_public,
                **_time_dict,
            )

        except Exception as err:
            logger.debug(f"Error during performing similarity search: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during performing similarity search: {err}",
            ) from err

    async def add_document_to_database(
        self, session: AsyncSession, upload_file: UploadFile
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
            saved_file_path = app_utils.save_uploaded_document(
                file=upload_file
            )
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

            doc_section_chunk_dbs: list[DocumentSectionChunk] = []
            doc_section_dbs: list[DocumentSection] = []
            for doc_section in doc_sections:
                doc_section_id = str(uuid.uuid4())
                doc_section_db = DocumentSection(
                    id=doc_section_id,
                    title=doc_section.metadata.get("title"),
                    url=doc_section.metadata.get("url"),
                    description=doc_section.metadata.get("description"),
                )
                doc_section_dbs.append(doc_section_db)

                doc_section_chunks = self._split_document_recursive(
                    content=doc_section.page_content,
                    metadata=doc_section.metadata,
                    prepend_headers=True,
                )
                for i, doc_section_chunk in enumerate(doc_section_chunks):
                    chunk_id = str(uuid.uuid4())
                    doc_section_chunk_db = DocumentSectionChunk(
                        id=chunk_id,
                        document_section_id=doc_section_id,
                        content=doc_section_chunk.page_content,
                        chunk_index=i,
                        qdrant_point_id=chunk_id,
                        chunk_metadata={},
                    )
                    doc_section_chunk_dbs.append(doc_section_chunk_db)

            # compute embeddings for all chunks
            doc_section_chunk_vectors = (
                await self._embeddings.aembed_documents(
                    [
                        doc_section_chunk.content
                        for doc_section_chunk in doc_section_chunk_dbs
                    ],
                )
            )

            # compute qdrant points
            qdrant_points: list[qdrant_models.PointStruct] = []
            for (
                doc_section_chunk_db,
                doc_section_chunk_vector,
            ) in zip(
                doc_section_chunk_dbs, doc_section_chunk_vectors, strict=True
            ):
                assert doc_section_chunk_db.qdrant_point_id is not None
                qdrant_points.append(
                    qdrant_models.PointStruct(
                        id=str(doc_section_chunk_db.qdrant_point_id),
                        vector=doc_section_chunk_vector,
                        payload={},
                    )
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

            session.add_all(doc_section_dbs)
            session.add_all(doc_section_chunk_dbs)
            await session.commit()

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

    async def add_documents_to_database_in_batch(
        self, session: AsyncSession, upload_files: list[UploadFile]
    ) -> JSONResponse:
        """Add multiple documents to the database in batch."""
        if not upload_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided",
            )

        if len(upload_files) > settings.BATCH_DOCUMENT_UPLOAD_MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size too large. Maximum {settings.BATCH_DOCUMENT_UPLOAD_MAX_BATCH_SIZE} files allowed per batch.",
            )

        # Track temporary files for cleanup
        saved_file_paths: list[str] = []
        successful_files: list[dict[str, Any]] = []
        failed_files: list[dict[str, Any]] = []

        try:
            # Step 1: Validate and save all files first
            valid_doc_sections: list[tuple[str, list[LangchainDocument]]] = []

            for upload_file in upload_files:
                file_result = {
                    "filename": upload_file.filename,
                    "error": None,
                    "details": {},
                }

                try:
                    # Validate individual file
                    if upload_file.filename is None:
                        file_result["error"] = (
                            "Missing filename in the uploaded file"
                        )
                        failed_files.append(file_result)
                        continue

                    if not upload_file.filename.endswith((".md", ".markdown")):
                        file_result["error"] = "File must be a markdown file"
                        failed_files.append(file_result)
                        continue

                    # Save and process file
                    saved_file_path = app_utils.save_uploaded_document(
                        file=upload_file
                    )
                    saved_file_paths.append(saved_file_path)

                    doc_sections = self._split_markdown_on_header(
                        md_file_path=saved_file_path
                    )

                    if not doc_sections:
                        file_result["error"] = (
                            "No document sections found in file"
                        )
                        failed_files.append(file_result)
                        continue

                    valid_doc_sections.append((
                        upload_file.filename,
                        doc_sections,
                    ))

                except Exception as err:
                    file_result["error"] = (
                        f"Failed to process file: {str(err)}"
                    )
                    failed_files.append(file_result)
                    logger.error(
                        f"Failed to process file {upload_file.filename}: {err}"
                    )
                    continue

            # If no valid files, return early
            if not valid_doc_sections:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "message": "No valid files to process",
                        "successful_files": successful_files,
                        "failed_files": failed_files,
                        "summary": {
                            "total_files": len(upload_files),
                            "successful_count": 0,
                            "failed_count": len(failed_files),
                        },
                    },
                )

            # Step 2: Initialize Qdrant collection
            is_collection_created = await self._initialize_qdrant_collection()
            if not is_collection_created:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create Qdrant collection",
                )

            # Step 3: Process all valid files and prepare data for batch operations
            all_qdrant_points: list[qdrant_models.PointStruct] = []
            all_doc_section_chunk_dbs: list[DocumentSectionChunk] = []
            all_doc_sections: list[DocumentSection] = []

            # Track total chunks to prevent memory issues
            total_estimated_chunks = 0

            for _, doc_sections in valid_doc_sections:
                # Estimate chunks for memory check
                for doc_section in doc_sections:
                    content_length = len(doc_section.page_content)
                    if content_length <= settings.CHUNK_SIZE:
                        estimated_chunks = 1
                    else:
                        # Account for overlap: each chunk after the first starts at (chunk_size - overlap)
                        effective_chunk_size = (
                            settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
                        )
                        if effective_chunk_size <= 0:
                            estimated_chunks = 1
                        else:
                            # First chunk takes CHUNK_SIZE, remaining chunks take effective_chunk_size each
                            remaining_content = (
                                content_length - settings.CHUNK_SIZE
                            )
                            estimated_chunks = 1 + max(
                                0,
                                (remaining_content + effective_chunk_size - 1)
                                // effective_chunk_size,
                            )
                    total_estimated_chunks += estimated_chunks

            if (
                total_estimated_chunks
                > settings.BATCH_DOCUMENT_UPLOAD_MAX_TOTAL_CHUNKS
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estimated total chunks ({total_estimated_chunks}) exceeds limit ({settings.BATCH_DOCUMENT_UPLOAD_MAX_TOTAL_CHUNKS}). Please reduce batch size.",
                )

            for filename, doc_sections in valid_doc_sections:
                file_result: dict[str, Any] = {
                    "filename": filename,
                    "error": None,
                    "details": {
                        "num_doc_sections": len(doc_sections),
                        "num_doc_section_chunks": 0,
                        "num_qdrant_points": 0,
                    },
                }

                try:
                    file_doc_section_chunk_dbs: list[DocumentSectionChunk] = []
                    file_doc_section_dbs: list[DocumentSection] = []

                    for doc_section in doc_sections:
                        doc_section_id = str(uuid.uuid4())
                        doc_section_db = DocumentSection(
                            id=doc_section_id,
                            title=doc_section.metadata.get("title"),
                            url=doc_section.metadata.get("url"),
                            description=doc_section.metadata.get(
                                "description"
                            ),
                        )
                        file_doc_section_dbs.append(doc_section_db)

                        doc_section_chunks = self._split_document_recursive(
                            content=doc_section.page_content,
                            metadata=doc_section.metadata,
                            prepend_headers=True,
                        )

                        for i, doc_section_chunk in enumerate(
                            doc_section_chunks
                        ):
                            chunk_id = str(uuid.uuid4())
                            doc_section_chunk_db = DocumentSectionChunk(
                                id=chunk_id,
                                document_section_id=doc_section_id,
                                content=doc_section_chunk.page_content,
                                chunk_index=i,
                                qdrant_point_id=chunk_id,
                                chunk_metadata={},
                            )
                            file_doc_section_chunk_dbs.append(
                                doc_section_chunk_db
                            )

                    # compute embeddings for all chunks of this file
                    file_doc_section_chunk_vectors = await self._embeddings.aembed_documents(
                        [
                            doc_section_chunk.content
                            for doc_section_chunk in file_doc_section_chunk_dbs
                        ],
                    )

                    # compute qdrant points for this file
                    file_qdrant_points: list[qdrant_models.PointStruct] = []
                    for (
                        doc_section_chunk_db,
                        doc_section_chunk_vector,
                    ) in zip(
                        file_doc_section_chunk_dbs,
                        file_doc_section_chunk_vectors,
                        strict=True,
                    ):
                        assert doc_section_chunk_db.qdrant_point_id is not None
                        file_qdrant_points.append(
                            qdrant_models.PointStruct(
                                id=str(doc_section_chunk_db.qdrant_point_id),
                                vector=doc_section_chunk_vector,
                                payload={},
                            )
                        )
                    # Update file results
                    file_result["details"]["num_doc_section_chunks"] = len(
                        file_doc_section_chunk_dbs
                    )
                    file_result["details"]["num_qdrant_points"] = len(
                        file_qdrant_points
                    )

                    # Add to batch collections
                    all_doc_sections.extend(file_doc_section_dbs)
                    all_doc_section_chunk_dbs.extend(
                        file_doc_section_chunk_dbs
                    )
                    all_qdrant_points.extend(file_qdrant_points)

                    successful_files.append(file_result)

                except Exception as err:
                    file_result["error"] = (
                        f"Failed to prepare data for file: {str(err)}"
                    )
                    failed_files.append(file_result)
                    logger.error(
                        f"Failed to prepare data for file {filename}: {err}"
                    )
                    continue

            # Step 4: Batch operations (all or nothing for data consistency)
            try:
                # Add document sections to session first
                session.add_all(all_doc_sections)

                # Add all chunks to session
                session.add_all(all_doc_section_chunk_dbs)

                # Commit database transaction first to ensure data consistency
                await session.commit()

                # Batch upsert to Qdrant after successful database commit
                if all_qdrant_points:
                    logger.debug(
                        f"Adding {len(all_qdrant_points)} points to Qdrant..."
                    )
                    try:
                        await self._qdrant_client.upsert(
                            collection_name=settings.QDRANT_COLLECTION_NAME,
                            points=all_qdrant_points,
                        )
                        logger.debug(
                            f"Successfully added {len(all_qdrant_points)} points to Qdrant"
                        )
                    except Exception as qdrant_err:
                        logger.error(
                            f"Qdrant upsert failed after successful database commit: {qdrant_err}"
                        )
                        # Database changes are already committed, but Qdrant failed
                        # Log this as a warning since data is partially consistent
                        logger.warning(
                            "Database records created successfully, but vector search may be incomplete. "
                            "Manual Qdrant cleanup may be required."
                        )
                        # Don't raise the exception - database operations succeeded

                logger.info(
                    f"Successfully processed {len(successful_files)} files in batch"
                )

            except Exception as err:
                logger.error(f"Batch operation failed: {err}")

                # Rollback database transaction
                await session.rollback()

                # Move all successful files to failed
                for file_result in successful_files:
                    file_result["error"] = (
                        f"Batch operation failed: {str(err)}"
                    )
                    failed_files.append(file_result)
                successful_files.clear()

            return JSONResponse(
                content={
                    "message": f"Batch processing completed. {len(successful_files)} successful, {len(failed_files)} failed.",
                    "successful_files": successful_files,
                    "failed_files": failed_files,
                    "summary": {
                        "total_files": len(upload_files),
                        "successful_count": len(successful_files),
                        "failed_count": len(failed_files),
                        "total_doc_sections": sum(
                            f["details"]["num_doc_sections"]
                            for f in successful_files
                        ),
                        "total_doc_section_chunks": len(
                            all_doc_section_chunk_dbs
                        )
                        if successful_files
                        else 0,
                        "total_qdrant_points": len(all_qdrant_points)
                        if successful_files
                        else 0,
                        "config": {
                            "chunk_size": settings.CHUNK_SIZE,
                            "chunk_overlap": settings.CHUNK_OVERLAP,
                        },
                    },
                }
            )

        except Exception as err:
            logger.error(
                f"Unexpected error in batch processing: {err}",
                extra={
                    "error_type": type(err).__name__,
                    "total_files": len(upload_files),
                    "saved_files_count": len(saved_file_paths),
                    "successful_files_count": len(successful_files),
                    "failed_files_count": len(failed_files),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error in batch processing: {err}",
            ) from err

        finally:
            # Clean up all temporary files regardless of success/failure
            for saved_file_path in saved_file_paths:
                try:
                    if os.path.exists(saved_file_path):
                        os.remove(saved_file_path)
                except Exception as cleanup_err:
                    logger.warning(
                        f"Failed to clean up temporary file {saved_file_path}: {cleanup_err}"
                    )

    async def export_document_sections_chunks(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            result = await session.execute(
                select(DocumentSection)
                .options(selectinload(DocumentSection.document_section_chunks))
                .order_by(DocumentSection.created_at)
            )
            document_sections = result.scalars().all()

            sections_list: list[dict[str, Any]] = []
            export_data: dict[str, Any] = {
                "exported_at": datetime.now(tz=timezone_vi).isoformat(),
                "total_sections": len(document_sections),
                "total_chunks": sum(
                    len(section.document_section_chunks)
                    for section in document_sections
                ),
                "sections": sections_list,
            }

            for section in document_sections:
                chunks_list: list[dict[str, Any]] = []
                section_data: dict[str, Any] = {
                    "id": str(section.id),
                    "title": section.title,
                    "url": section.url,
                    "description": section.description,
                    "created_at": section.created_at.isoformat()
                    if section.created_at
                    else None,
                    "chunks": chunks_list,
                }

                for chunk in section.document_section_chunks:
                    chunk_data: dict[str, Any] = {
                        "id": str(chunk.id),
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "chunk_metadata": chunk.chunk_metadata,
                        "qdrant_point_id": str(chunk.qdrant_point_id)
                        if chunk.qdrant_point_id
                        else None,
                        "created_at": chunk.created_at.isoformat()
                        if chunk.created_at
                        else None,
                    }
                    chunks_list.append(chunk_data)

                sections_list.append(section_data)

            return export_data

        except Exception as err:
            logger.error(f"Error exporting document sections chunks: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export document sections chunks: {err}",
            ) from err
