"""Langfuse instrumentation — v1: two separate top-level traces, nothing linked.

This is the starting point. Participants will progressively improve this
toward a single structured trace per turn in v2.
"""
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
    t = _langfuse.trace(name="retrieval", input={"question": question})
    t.update(output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]})


def trace_llm_call(question: str, model: str) -> None:
    if not _langfuse:
        return
    _langfuse.trace(name="llm_call", input={"question": question}, metadata={"model": model})
