import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import litellm
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import tracing
from rag.config import get_settings
from rag.ingestion.embed import LiteLLMEmbeddingService
from rag.pipeline import RAGPipeline
from rag.retrieval.repository import ChunkRepository


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


def create_app() -> FastAPI:
    settings = get_settings()

    import os

    litellm.set_verbose = False
    if key := settings.openai_api_key.get_secret_value():
        os.environ.setdefault("OPENAI_API_KEY", key)

    tracing.init(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repo = await ChunkRepository.create(settings.database_url)
        embedder = LiteLLMEmbeddingService(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )
        app.state.pipeline = RAGPipeline(
            embedder=embedder,
            repo=repo,
            model=settings.llm_model,
            top_k=settings.retrieval_top_k,
        )
        yield
        await repo.close()

    app = FastAPI(title="RAG Demo", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/chat")
    async def chat(request: ChatRequest) -> StreamingResponse:
        pipeline: RAGPipeline = app.state.pipeline

        async def event_stream() -> AsyncIterator[str]:
            async for token in pipeline.stream_answer(request.question):
                yield f"data: {json.dumps({'delta': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app
