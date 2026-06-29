---
title: Tracing v1 — What Basic Tracing Looks Like
description: 15-min concept session — v1 baseline, two unlinked traces
---

# What Basic Tracing Looks Like

_13:15 · 15 min · Concept_

**Repo:** `langfuse-demo` · branch: `v1-baseline-tracing`

---

## How v1 instruments Langfuse

_`tracing.py`_

**Two-line setup**
A Langfuse client is created on startup. Then one line does all the LLM tracing: `litellm.success_callback = ["langfuse"]`. litellm fires this after every completion — it automatically captures model, prompt, response, tokens, and cost.

**Manual retrieval trace**
`trace_retrieval()` creates a separate top-level trace recording the question and the chunks that came back.

**What's not here**
No session ID. No parent trace. No timing. No tags. The embedding call is invisible.

```python
# tracing.py — the entire v1 instrumentation

def init(public_key, secret_key, host):
    _langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
    # one line auto-traces every LLM call:
    # input, output, tokens, cost — for free
    litellm.success_callback = ["langfuse"]  # ← magic line


def trace_retrieval(question, chunks):
    if not _langfuse:
        return
    t = _langfuse.trace(
        name="retrieval",
        input={"question": question},
    )
    t.update(output={
        "num_chunks": len(chunks),
        "sources": [c.source for c in chunks],
    })
```

---

## What one user turn actually runs

_`pipeline.py`_

**Step by step:**
1. Embed the question — not traced
2. Similarity search — not traced
3. `trace_retrieval()` — creates a top-level "retrieval" trace. No timing.
4. `litellm.acompletion()` — auto-creates a separate top-level trace. No link to step 3.

**Net result:** Two unrelated traces per turn land in Langfuse. You can't tell which retrieval fed which LLM call.

```python
async def stream_answer(question, repo):
    settings = get_settings()

    # 1. embed — completely invisible in Langfuse
    [vec] = await embed([question], settings.embedding_model)

    # 2. search — completely invisible in Langfuse
    chunks = await repo.similarity_search(vec, ...)

    # 3. manual trace — top-level "retrieval" trace
    #    no parent, no timing, no session
    tracing.trace_retrieval(question, chunks)  # ← orphan

    # 4. LLM call — litellm auto-creates its OWN trace
    #    no link to the retrieval trace above
    response = await litellm.acompletion(
        model=settings.llm_model,
        messages=[...],
        stream=True,
        # no metadata= → floats as a new top-level event
    )                                          # ← orphan
    async for chunk in response:
        yield chunk
```

---

## What Langfuse shows after 2 turns

**Langfuse traces list — 4 events, 0 structure:**

| Trace | Turn | Tokens | Cost | Link |
|---|---|---|---|---|
| LLM · gpt-4o-mini _(auto)_ | 2 | 312 | $0.0021 | ✗ not linked |
| retrieval _(manual)_ | 2 | 4 chunks | — | ✗ not linked |
| LLM · gpt-4o-mini _(auto)_ | 1 | 287 | $0.0018 | ✗ not linked |
| retrieval _(manual)_ | 1 | 3 chunks | — | ✗ not linked |

**What you can answer:**
- ✓ Token count, cost, and exact prompt/response for each LLM call
- ✓ Which chunks were retrieved and from which source files

**What's missing:**
- ✗ Which retrieval fed which LLM call — 4 rows in random order, no parent-child link
- ✗ Conversation view — no `session_id` means turns 1 and 2 look like unrelated requests
- ✗ Latency — you see tokens but not how long retrieval took or when the first token arrived

---

## You can't score what you can't see

| Gap | Impact |
|---|---|
| **Embedding — invisible** | The vector search is the first place retrieval can fail. If the embedding is off, every chunk that follows is wrong. Zero signal today. |
| **Retrieval latency — unknown** | The LLM call has a token count. But if retrieval is slow, you'll never know — no timing was recorded. |
| **TTFT — not captured** | Time-to-first-token is the most user-visible quality signal. Without it you're blind to the latency your users actually experience. |
| **Conversations — fragmented** | 5 follow-up questions = 10 orphaned traces. You cannot replay the conversation or evaluate it end-to-end. |

> A span you didn't emit is a signal you'll never get. → This is what the next 45 minutes fixes.
