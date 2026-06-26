"""RAG pipeline: embed query → retrieve chunks → stream LLM response via litellm."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

import litellm

from rag import tracing
from rag.retrieval.repository import Chunk, ChunkRepository

SYSTEM_PROMPT = """\
You are a literary assistant specializing in the Sherlock Holmes stories by Arthur Conan Doyle.
Answer questions based solely on the provided context excerpts from the text.
If the context does not contain enough information to answer, say so honestly.
Be concise and quote directly from the text when helpful.
Respond in the same language as the user's question.
"""


class EmbeddingService(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


def _build_messages(question: str, chunks: list[Chunk]) -> list[dict]:
    context = "\n\n---\n\n".join(
        f"[{c.source}, p.{c.page}]\n{c.content}" for c in chunks
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nContext:\n{context}"},
        {"role": "user", "content": question},
    ]


class RAGPipeline:
    def __init__(
        self,
        embedder: EmbeddingService,
        repo: ChunkRepository,
        model: str,
        top_k: int = 5,
    ) -> None:
        self._embedder = embedder
        self._repo = repo
        self._model = model
        self._top_k = top_k

    async def stream_answer(self, question: str) -> AsyncIterator[str]:
        [query_vec] = await self._embedder.embed([question])
        chunks = await self._repo.similarity_search(query_vec, top_k=self._top_k)

        # v1 tracing: two separate top-level traces, nothing linked
        tracing.trace_retrieval(question, chunks)
        tracing.trace_llm_call(question, self._model)

        response = await litellm.acompletion(
            model=self._model,
            messages=_build_messages(question, chunks),
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
