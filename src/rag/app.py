"""FastAPI app — serves the chat API and the frontend."""
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from rag import tracing
from rag.config import get_settings
from rag.pipeline import stream_answer
from rag.retrieval.repository import ChunkRepository


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    trace_id: str
    value: int  # 1 = good, -1 = bad


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if key := settings.openai_api_key.get_secret_value():
        os.environ.setdefault("OPENAI_API_KEY", key)
    tracing.init(settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host)
    app.state.repo = await ChunkRepository.create(settings.database_url)
    yield
    await app.state.repo.close()


app = FastAPI(lifespan=lifespan)

FRONTEND = Path(__file__).parent.parent.parent / "frontend" / "index.html"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND)


@app.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    settings = get_settings()
    trace = tracing.start_trace(req.question, req.session_id, settings.llm_model)

    # Mirror what item.observe() does in the experiment runner:
    # set the Langfuse ContextVar so litellm's callback registers the generation
    # in a way the UI evaluator can pick up — not just via existing_trace_id metadata.
    if trace:
        from langfuse.decorators import langfuse_context
        langfuse_context._set_root_trace_id(trace.id)

    async def events() -> AsyncIterator[str]:
        if trace:
            yield f"data: {json.dumps({'trace_id': trace.id})}\n\n"
        async for token in stream_answer(req.question, app.state.repo, trace, settings):
            yield f"data: {json.dumps({'delta': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/feedback")
async def feedback(req: FeedbackRequest) -> dict:
    tracing.score_feedback(req.trace_id, req.value)
    return {"ok": True}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
