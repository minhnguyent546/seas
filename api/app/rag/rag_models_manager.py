import asyncio
import os
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from app.core.config import settings

# Optional import for FlagEmbedding (reranking functionality)
try:
    from FlagEmbedding import (  # pyright: ignore[reportMissingImports]
        FlagReranker,
    )

    _has_reranker = True
except ImportError:
    _has_reranker = False


class RagModelsManager:
    """Manages async loading and caching of models for RAG service."""

    def __init__(self):
        # Cached model instances
        self._embeddings: Embeddings | None = None
        self._reranker: Any = None

        # Locks to ensure only one concurrent initializer
        self._embeddings_lock = asyncio.Lock()
        self._reranker_lock = asyncio.Lock()

    async def get_embeddings(self) -> Embeddings:
        """Get or initialize the embeddings model in a thread-safe way."""
        # Fast path: already loaded
        if self._embeddings is not None:
            return self._embeddings

        # Only one initializer at a time
        async with self._embeddings_lock:
            # Re-check after acquiring lock
            if self._embeddings is None:
                logger.info("Loading embeddings model...")
                try:
                    model = GoogleGenerativeAIEmbeddings(
                        model=settings.EMBEDDING_MODEL,
                        google_api_key=settings.GOOGLE_API_KEY,  # pyright: ignore[reportArgumentType]
                    )
                    self._embeddings = model
                    logger.info("Embeddings model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load embeddings model: {e}")
                    raise
        return self._embeddings

    async def get_reranker(self) -> Any:
        """Get or initialize the reranker model in a thread-safe way."""
        if not _has_reranker or not settings.RERANK_ENABLED:
            return None

        if self._reranker is not None:
            return self._reranker

        async with self._reranker_lock:
            if self._reranker is None:
                logger.info("Loading reranker model...")
                try:
                    import torch  # pyright: ignore[reportMissingImports]

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Using device for reranker: {device}")

                    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
                    os.environ["TOKENIZERS_PARALLELISM"] = "false"

                    loop = asyncio.get_event_loop()
                    reranker = await loop.run_in_executor(
                        None,
                        lambda: FlagReranker(  # pyright: ignore[reportPossiblyUnboundVariable]
                            model_name_or_path=settings.BAAI_RERANKER_MODEL,
                            use_fp16=True,
                            device=device,
                        ),  # type: ignore
                    )
                    self._reranker = reranker
                    logger.info("Reranker model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load reranker model: {e}")
                    raise
        return self._reranker  # type: ignore

    async def preload_models(self) -> None:
        """Preload embeddings and reranker concurrently at startup."""
        tasks = [self.get_embeddings()]
        if _has_reranker and settings.RERANK_ENABLED:
            tasks.append(self.get_reranker())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Error during preload: {res}")
        logger.info("Preloading complete.")

    def get_status(self) -> dict[str, Any]:
        """Return initialization status for each model."""
        return {
            "embeddings": bool(self._embeddings),
            "reranker": bool(self._reranker)
            if _has_reranker and settings.RERANK_ENABLED
            else None,
        }


# Single global instance
rag_models_manager = RagModelsManager()
