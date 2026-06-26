from typing import Protocol

import litellm


class EmbeddingService(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class LiteLLMEmbeddingService:
    """Model-agnostic embeddings via litellm (OpenAI, Bedrock, etc.)."""

    def __init__(self, model: str = "text-embedding-3-small", dimensions: int = 1536) -> None:
        self._model = model
        self._dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await litellm.aembedding(model=self._model, input=texts)
        return [item["embedding"] for item in response.data]


class FakeEmbeddingService:
    """Deterministic fake for tests — no API calls."""

    def __init__(self, dims: int = 1536) -> None:
        self._dims = dims

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 1000) / 1000] + [0.0] * (self._dims - 1) for t in texts]
