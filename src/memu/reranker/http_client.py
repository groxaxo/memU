from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RerankerHTTPClient:
    """HTTP client for cross-encoder reranking APIs (e.g. vLLM /v1/rerank, Cohere-compatible).

    Supports any reranking endpoint that follows the Cohere rerank API format,
    including vLLM's built-in reranker endpoint served by cross-encoder models
    such as Qwen3-Reranker.

    Example vLLM launch::

        vllm serve Qwen/Qwen3-Reranker-0.6B --port 8002 --task score

    Example usage::

        client = RerankerHTTPClient(
            base_url="http://localhost:8002/v1",
            api_key="EMPTY",
            model="Qwen/Qwen3-Reranker-0.6B",
        )
        ranked = await client.rerank("What is Python?", ["Python is a language", "Java is compiled"])
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "EMPTY",
        model: str,
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "EMPTY"
        self.model = model
        self.timeout = timeout

    async def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        top_n: int | None = None,
    ) -> list[tuple[int, float]]:
        """Rerank documents by relevance to a query.

        Sends a request to the ``/v1/rerank`` endpoint and returns a list of
        ``(original_index, relevance_score)`` tuples sorted by score descending.

        Args:
            query: The query string.
            documents: List of document texts to rerank.
            top_n: If set, only return the top *n* results.  When ``None``
                all documents are returned (sorted by score).

        Returns:
            List of ``(original_index, relevance_score)`` tuples, highest
            score first.
        """
        if not documents:
            return []

        payload: dict[str, Any] = {
            "model": self.model,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/v1/rerank", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        logger.debug("Reranker response: %s", data)

        results: list[tuple[int, float]] = []
        for item in data.get("results", []):
            idx = int(item["index"])
            score = float(item["relevance_score"])
            results.append((idx, score))

        # Ensure descending order by score (API should already return this, but be defensive)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
