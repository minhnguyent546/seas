import asyncio
from typing import Any

from FlagEmbedding import BGEM3FlagModel, FlagReranker
from loguru import logger

from app.core.config import settings


class RagModelsManager:
    """Manages async loading and caching of models for RAG service."""

    def __init__(self):
        # Cached model instances
        self._embeddings: BGEM3FlagModel | None = None
        self._reranker: FlagReranker | None = None

        # Locks to ensure only one concurrent initializer
        self._embeddings_lock = asyncio.Lock()
        self._reranker_lock = asyncio.Lock()

    async def get_embeddings(self) -> BGEM3FlagModel:
        """Get or initialize the embeddings model in a thread-safe way."""
        # Fast path: already loaded
        if self._embeddings is not None:
            return self._embeddings

        # Only one initializer at a time
        async with self._embeddings_lock:
            # Re-check after acquiring lock
            if self._embeddings is None:
                logger.info(
                    f"Loading embeddings model {settings.BAAI_EMBEDDING_MODEL}..."
                )
                try:
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Using device for embeddings: {device}")

                    loop = asyncio.get_event_loop()
                    embeddings = await loop.run_in_executor(
                        None,
                        lambda: BGEM3FlagModel(  # pyright: ignore[reportPossiblyUnboundVariable]
                            model_name_or_path=settings.BAAI_EMBEDDING_MODEL,
                            normalize_embeddings=True,
                            use_fp16=True,
                            device=device,
                            cache_dir=settings.HF_HOME,
                        ),  # type: ignore
                    )
                    self._embeddings = embeddings
                    logger.info("Embeddings model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load embeddings model: {e}")
                    raise
        return self._embeddings

    async def get_reranker(self) -> FlagReranker:
        """Get or initialize the reranker model in a thread-safe way."""

        if self._reranker is not None:
            return self._reranker

        async with self._reranker_lock:
            if self._reranker is None:
                logger.info(
                    f"Loading reranker model {settings.BAAI_RERANKER_MODEL}..."
                )
                try:
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Using device for reranker: {device}")

                    loop = asyncio.get_event_loop()
                    reranker = await loop.run_in_executor(
                        None,
                        lambda: FlagReranker(  # pyright: ignore[reportPossiblyUnboundVariable]
                            model_name_or_path=settings.BAAI_RERANKER_MODEL,
                            use_fp16=True,
                            device=device,
                            cache_dir=settings.HF_HOME,
                        ),  # type: ignore
                    )
                    self._reranker = reranker
                    logger.info("Reranker model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load reranker model: {e}")
                    raise
        return self._reranker  # type: ignore

    async def preload_models(self) -> None:
        """Preload embeddings and reranker concurrently."""
        tasks = [self.get_embeddings(), self.get_reranker()]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Error during preload: {res}")
        logger.info("Preloading complete.")

    def get_status(self) -> dict[str, Any]:
        """Return initialization status for each model."""
        return {
            "embeddings": self._embeddings is not None,
            "reranker": self._reranker is not None,
        }


# Single global instance
rag_models_manager = RagModelsManager()
