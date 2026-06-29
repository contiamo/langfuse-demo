"""Langfuse instrumentation — v1: two separate top-level traces, nothing linked.

This is the starting point. Participants will progressively improve this
toward a single structured trace per turn in v2.
"""
import litellm

from rag.retrieval.repository import Chunk

_langfuse = None


def init(public_key: str, secret_key: str, host: str) -> None:
    global _langfuse
    if not public_key or not secret_key:
        return
    import os

    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", secret_key)
    os.environ.setdefault("LANGFUSE_HOST", host)

    from langfuse import Langfuse

    _langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    # auto-traces every LLM call: input, output, tokens, cost
    litellm.success_callback = ["langfuse"]


def trace_retrieval(question: str, chunks: list[Chunk]) -> None:
    if not _langfuse:
        return
    t = _langfuse.trace(name="retrieval", input={"question": question})
    t.update(output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]})
