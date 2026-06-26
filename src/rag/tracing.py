"""Langfuse instrumentation — v1: retrieval trace + automatic LLM generation tracking.

LLM calls are traced automatically via langfuse.openai injected into PydanticAI's
provider — gives input messages, output, token counts, and cost out of the box.
Retrieval is traced explicitly via the Langfuse SDK.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rag.retrieval.repository import Chunk

_langfuse = None
_openai_client: Any = None


def init(public_key: str, secret_key: str, host: str) -> None:
    global _langfuse, _openai_client
    if not public_key or not secret_key:
        return
    import os

    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", secret_key)
    os.environ.setdefault("LANGFUSE_HOST", host)

    from langfuse import Langfuse
    from langfuse.openai import AsyncOpenAI

    _langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    _openai_client = AsyncOpenAI()  # Langfuse-wrapped client — tracks input, output, tokens, cost


def get_openai_client() -> Any:
    """Return Langfuse-wrapped AsyncOpenAI if configured, None otherwise."""
    return _openai_client


def trace_retrieval(question: str, chunks: list[Chunk]) -> None:
    if not _langfuse:
        return
    trace = _langfuse.trace(name="retrieval", input={"question": question})
    trace.update(output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]})
