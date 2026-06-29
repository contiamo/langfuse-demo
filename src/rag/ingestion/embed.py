import litellm


async def embed(texts: list[str], model: str, trace_id: str | None = None) -> list[list[float]]:
    metadata = {"existing_trace_id": trace_id} if trace_id else {}
    response = await litellm.aembedding(model=model, input=texts, metadata=metadata)
    return [item["embedding"] for item in response.data]


class FakeEmbeddingService:
    """Deterministic fake for tests — no API calls."""

    def __init__(self, dims: int = 1536) -> None:
        self._dims = dims

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 1000) / 1000] + [0.0] * (self._dims - 1) for t in texts]
