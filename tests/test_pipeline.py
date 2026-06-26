"""Unit tests — no API keys, no real DB needed."""
import pytest

from rag.ingestion.embed import FakeEmbeddingService
from rag.ingestion.parse import _chunk


def test_chunk_splits_long_text():
    text = "word " * 400  # ~2000 chars
    parts = _chunk(text)
    assert len(parts) > 1
    assert all(len(p) > 50 for p in parts)


def test_chunk_skips_short_text():
    assert _chunk("hi") == []


@pytest.mark.asyncio
async def test_fake_embedder_returns_correct_shape():
    svc = FakeEmbeddingService(dims=8)
    result = await svc.embed(["hello", "world"])
    assert len(result) == 2
    assert all(len(v) == 8 for v in result)
