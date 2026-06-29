"""Core RAG logic: embed → retrieve → stream LLM response."""
import time
from collections.abc import AsyncIterator

import litellm

from rag import tracing
from rag.config import get_settings
from rag.ingestion.embed import embed
from rag.retrieval.repository import Chunk, ChunkRepository

SYSTEM_PROMPT = """\
You are a literary assistant specializing in the Sherlock Holmes stories by Arthur Conan Doyle.
Answer based solely on the provided context. If it does not contain the answer, say so.
Be concise and quote the text directly when helpful.
Respond in the same language as the user's question.
"""


def _context(chunks: list[Chunk]) -> str:
    return "\n\n---\n\n".join(f"[{c.source}, p.{c.page}]\n{c.content}" for c in chunks)


async def stream_answer(
    question: str, repo: ChunkRepository, session_id: str | None = None
) -> AsyncIterator[str]:
    settings = get_settings()
    t0 = time.monotonic()

    trace = tracing.start_trace(question, session_id, settings.llm_model)
    trace_id = trace.id if trace else None

    [vec] = await embed([question], settings.embedding_model, trace_id=trace_id)
    chunks = await repo.similarity_search(
        vec, top_k=settings.retrieval_top_k, min_similarity=settings.retrieval_min_similarity
    )
    retrieval_ms = (time.monotonic() - t0) * 1000
    tracing.record_retrieval(trace, chunks, retrieval_ms)

    metadata = {"existing_trace_id": trace.id} if trace else {}

    t1 = time.monotonic()
    ttft_ms: float | None = None

    response = await litellm.acompletion(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\nContext:\n{_context(chunks)}"},
            {"role": "user", "content": question},
        ],
        stream=True,
        metadata=metadata,
    )
    async for chunk in response:
        if delta := chunk.choices[0].delta.content:
            if ttft_ms is None:
                ttft_ms = (time.monotonic() - t1) * 1000
            yield delta

    tracing.end_trace(trace, ttft_ms, (time.monotonic() - t0) * 1000)
