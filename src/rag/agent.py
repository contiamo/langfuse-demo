"""RAG agent — retrieval as a tool, served via PydanticAI's built-in web UI.

Run with:  task run  →  http://localhost:7932
       or:  task dev  (local hot-reload, requires running DB)
"""
import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from rag import tracing
from rag.config import get_settings
from rag.ingestion.embed import embed
from rag.retrieval.repository import ChunkRepository

settings = get_settings()

if key := settings.openai_api_key.get_secret_value():
    os.environ.setdefault("OPENAI_API_KEY", key)

tracing.init(settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host)

# Use Langfuse-wrapped OpenAI client if available, plain OpenAI otherwise.
# This gives automatic per-request traces with input messages, output, tokens, and cost.
_lf_client = tracing.get_openai_client()
_provider = OpenAIProvider(openai_client=_lf_client) if _lf_client else OpenAIProvider()
_model = OpenAIChatModel(settings.llm_model, provider=_provider)

_repo: ChunkRepository | None = None


async def _get_repo() -> ChunkRepository:
    global _repo
    if _repo is None:
        _repo = await ChunkRepository.create(settings.database_url)
    return _repo


agent = Agent(
    _model,
    instructions="""\
You are a literary assistant specializing in the Sherlock Holmes stories by Arthur Conan Doyle.
Always call search_documents first — answers must come from the retrieved passages only.
If the retrieved context doesn't contain enough information, say so honestly.
Be concise and quote directly from the text when helpful.
Respond in the same language as the user's question.
""",
)


@agent.tool_plain
async def search_documents(query: str) -> str:
    """Search the Sherlock Holmes knowledge base for relevant passages."""
    repo = await _get_repo()
    [vec] = await embed([query], settings.embedding_model)
    chunks = await repo.similarity_search(vec, top_k=settings.retrieval_top_k)

    tracing.trace_retrieval(query, chunks)

    return "\n\n---\n\n".join(f"[{c.source}, p.{c.page}]\n{c.content}" for c in chunks)


app = agent.to_web()
