"""PydanticAI agent — used for structured queries and unit testing via TestModel."""
from pydantic_ai import Agent

from rag.retrieval.repository import Chunk

SYSTEM_PROMPT = """\
You are a literary assistant specializing in the Sherlock Holmes stories by Arthur Conan Doyle.
Answer questions based solely on the provided context excerpts from the text.
If the context does not contain enough information to answer, say so honestly.
Be concise and quote directly from the text when helpful.
Respond in the same language as the user's question.
"""

# deps_type=list[Chunk] lets tests inject a FakeModel without real API calls
agent: Agent[list[Chunk], str] = Agent("openai:gpt-4o-mini", deps_type=list[Chunk])


@agent.system_prompt
def build_system_prompt(ctx) -> str:  # type: ignore[override]
    chunks = ctx.deps
    context = "\n\n---\n\n".join(
        f"[{c.source}, p.{c.page}]\n{c.content}" for c in chunks
    )
    return SYSTEM_PROMPT + f"\n\nContext:\n{context}"
