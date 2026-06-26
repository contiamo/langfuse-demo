"""Unit tests — no API keys, no real DB needed."""
from uuid import uuid4

import pytest

from rag.ingestion.embed import FakeEmbeddingService
from rag.ingestion.parse import _chunk
from rag.pipeline import _build_messages
from rag.retrieval.repository import Chunk


def fake_chunk(content: str) -> Chunk:
    return Chunk(id=uuid4(), source="test.txt", page=1, chunk_index=0, content=content, metadata={})


# --- parse ---

def test_chunk_splits_long_text():
    text = "word " * 400  # ~2000 chars
    parts = _chunk(text)
    assert len(parts) > 1
    assert all(len(p) > 50 for p in parts)


def test_chunk_skips_short_text():
    assert _chunk("hi") == []


# --- pipeline messages ---

def test_build_messages_includes_context():
    chunks = [fake_chunk("Holmes lit his pipe.")]
    messages = _build_messages("Who lit the pipe?", chunks)
    combined = " ".join(m["content"] for m in messages)
    assert "Holmes lit his pipe." in combined
    assert "Who lit the pipe?" in combined


def test_build_messages_structure():
    msgs = _build_messages("q", [])
    roles = [m["role"] for m in msgs]
    assert roles == ["system", "user"]


# --- fake embedder ---

@pytest.mark.asyncio
async def test_fake_embedder_returns_correct_shape():
    svc = FakeEmbeddingService(dims=8)
    result = await svc.embed(["hello", "world"])
    assert len(result) == 2
    assert all(len(v) == 8 for v in result)
