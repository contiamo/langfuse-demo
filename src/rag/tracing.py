"""Langfuse instrumentation — v1: two separate, unlinked top-level traces.

v1 intentionally keeps retrieval and LLM as separate traces so participants can
see the "before" state and progressively wire them together in v2/v3.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.retrieval.repository import Chunk

_langfuse = None


def init(public_key: str, secret_key: str, host: str) -> None:
    global _langfuse
    if not public_key or not secret_key:
        return
    from langfuse import Langfuse

    _langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)


# --- v1 helpers: call these from pipeline.py ---


def trace_retrieval(question: str, chunks: list[Chunk]) -> None:
    if not _langfuse:
        return
    trace = _langfuse.trace(name="retrieval", input={"question": question})
    trace.update(output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]})


def trace_llm_call(question: str, model: str) -> None:
    if not _langfuse:
        return
    # ponytail: v1 — no output logged here because we stream; link spans added in v2
    _langfuse.trace(name="llm_call", input={"question": question}, metadata={"model": model})
