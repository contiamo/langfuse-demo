"""Langfuse instrumentation — v2: one trace per turn, child spans, latency, tags.

Structure per turn:
  trace "rag_query"  (session_id, tags: [model, "sherlock-holmes"])
    ├── span  "retrieval"   — latency_ms, num_chunks, sources
    └── generation (litellm) — input messages, output, tokens, cost, TTFT
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


def start_trace(question: str, session_id: str | None, model: str, user: str = ""):
    if not _langfuse:
        return None
    tags = [model, "sherlock-holmes"]
    if user:
        tags.append(user)
    return _langfuse.trace(
        name="rag_query",
        input={"question": question},
        session_id=session_id,
        user_id=user or None,
        tags=tags,
    )


def record_retrieval(trace, chunks: list[Chunk], start_time, end_time) -> None:
    if not trace:
        return
    latency_ms = (end_time - start_time).total_seconds() * 1000
    span = trace.span(name="retrieval", start_time=start_time, end_time=end_time)
    span.update(
        output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]},
        metadata={"latency_ms": round(latency_ms, 1)},
    )


def end_trace(trace, ttft_ms: float | None, total_ms: float, answer: str = "") -> None:
    if not trace:
        return
    trace.update(
        output={"answer": answer} if answer else None,
        metadata={
            "ttft_ms": round(ttft_ms, 1) if ttft_ms else None,
            "total_latency_ms": round(total_ms, 1),
        }
    )
