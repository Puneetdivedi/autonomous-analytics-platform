"""Long-term semantic memory backed by Qdrant.

Stores text with metadata as embedded vectors and recalls them by semantic
similarity. Embeddings are produced by OpenAI (via ``langchain_openai``) when an
API key is configured, otherwise a deterministic hash-based fallback vector is
used so the feature works fully offline. Every Qdrant interaction degrades
gracefully to a no-op / empty result when the service is unavailable.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import TYPE_CHECKING, Any

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from qdrant_client import AsyncQdrantClient

logger = get_logger(__name__)

#: Dimensionality of the deterministic offline fallback embedding.
_FALLBACK_DIM = 256
#: Dimensionality of OpenAI ``text-embedding-3-small`` (and -ada-002).
_OPENAI_DIM = 1536


class LongTermMemory:
    """Semantic store over Qdrant with a graceful offline fallback."""

    def __init__(self, collection: str = "long_term_memory") -> None:
        self._collection = collection
        self._use_openai = bool(settings.openai_api_key)
        self._dim = _OPENAI_DIM if self._use_openai else _FALLBACK_DIM
        self._client: "AsyncQdrantClient | None" = None
        self._embedder: Any | None = None
        self._collection_ready = False

    # --- Client / collection ------------------------------------------------

    def _get_client(self) -> "AsyncQdrantClient | None":
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import AsyncQdrantClient

            self._client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=5,
            )
            return self._client
        except Exception as exc:  # noqa: BLE001
            logger.warning("qdrant_client_unavailable", error=str(exc))
            return None

    async def _ensure_collection(self, client: "AsyncQdrantClient") -> bool:
        if self._collection_ready:
            return True
        try:
            from qdrant_client.http import models as qmodels

            exists = await client.collection_exists(self._collection)
            if not exists:
                await client.create_collection(
                    collection_name=self._collection,
                    vectors_config=qmodels.VectorParams(
                        size=self._dim, distance=qmodels.Distance.COSINE
                    ),
                )
                logger.info("qdrant_collection_created", collection=self._collection)
            self._collection_ready = True
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("qdrant_ensure_collection_failed", error=str(exc))
            return False

    # --- Embeddings ----------------------------------------------------------

    def _fallback_embedding(self, text: str) -> list[float]:
        """Deterministic, normalized pseudo-embedding derived from a hash."""
        vector = [0.0] * self._dim
        # Expand a SHA-256 digest into ``_dim`` float components.
        for i in range(self._dim):
            digest = hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
            # Map first 4 bytes to a float in [-1, 1).
            raw = int.from_bytes(digest[:4], "big")
            vector[i] = (raw / 0xFFFFFFFF) * 2.0 - 1.0
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    async def _embed(self, text: str) -> list[float]:
        if not self._use_openai:
            return self._fallback_embedding(text)
        try:
            if self._embedder is None:
                from langchain_openai import OpenAIEmbeddings

                self._embedder = OpenAIEmbeddings(
                    model=settings.embedding_model,
                    api_key=settings.openai_api_key,
                )
            return await self._embedder.aembed_query(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("openai_embed_failed_fallback", error=str(exc))
            # Fall back to the offline embedding; keep dims consistent.
            self._use_openai = False
            self._dim = _FALLBACK_DIM
            self._collection_ready = False
            return self._fallback_embedding(text)

    # --- Public API ----------------------------------------------------------

    async def add(
        self, namespace: str, text: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Embed and store ``text`` under ``namespace``. Returns success."""
        if not text or not text.strip():
            return False
        client = self._get_client()
        if client is None:
            return False
        try:
            from qdrant_client.http import models as qmodels

            vector = await self._embed(text)
            if not await self._ensure_collection(client):
                return False
            payload = {"namespace": namespace, "text": text, **(metadata or {})}
            await client.upsert(
                collection_name=self._collection,
                points=[
                    qmodels.PointStruct(
                        id=str(uuid.uuid4()), vector=vector, payload=payload
                    )
                ],
            )
            logger.info("memory_added", namespace=namespace)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("memory_add_failed", namespace=namespace, error=str(exc))
            return False

    async def search(
        self, namespace: str, query: str, k: int = 5
    ) -> list[dict[str, Any]]:
        """Return up to ``k`` items in ``namespace`` similar to ``query``."""
        if not query or not query.strip():
            return []
        client = self._get_client()
        if client is None:
            return []
        try:
            from qdrant_client.http import models as qmodels

            vector = await self._embed(query)
            if not await self._ensure_collection(client):
                return []
            flt = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="namespace",
                        match=qmodels.MatchValue(value=namespace),
                    )
                ]
            )
            hits = await client.search(
                collection_name=self._collection,
                query_vector=vector,
                query_filter=flt,
                limit=k,
            )
            results: list[dict[str, Any]] = []
            for hit in hits:
                payload = dict(hit.payload or {})
                text = payload.pop("text", "")
                payload.pop("namespace", None)
                results.append(
                    {"text": text, "metadata": payload, "score": float(hit.score)}
                )
            logger.info("memory_search", namespace=namespace, hits=len(results))
            return results
        except Exception as exc:  # noqa: BLE001
            logger.warning("memory_search_failed", namespace=namespace, error=str(exc))
            return []


__all__ = ["LongTermMemory"]
