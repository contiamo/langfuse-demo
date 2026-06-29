"""Core RAG logic: embed → retrieve → stream LLM response."""
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


async def stream_answer(question: str, repo: ChunkRepository) -> AsyncIterator[str]:
    settings = get_settings()

    [vec] = await embed([question], settings.embedding_model)
    chunks = await repo.similarity_search(vec, top_k=settings.retrieval_top_k)

    tracing.trace_retrieval(question, chunks)

    response = await litellm.acompletion(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\nContext:\n{_context(chunks)}"},
            {"role": "user", "content": question},
        ],
        stream=True,
    )
    async for chunk in response:
        if delta := chunk.choices[0].delta.content:
            yield delta
