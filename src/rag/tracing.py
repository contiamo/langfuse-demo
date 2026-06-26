"""Langfuse instrumentation — v1: single retrieval trace per question.

v1 is intentionally minimal so participants can see the "before" state
and progressively add structure in v2/v3.
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


def trace_retrieval(question: str, chunks: list[Chunk]) -> None:
    if not _langfuse:
        return
    trace = _langfuse.trace(name="retrieval", input={"question": question})
    trace.update(output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]})
