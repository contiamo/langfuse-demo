---
title: Tracing v2 — Taking Tracing to Another Level
description: 45-min hands-on — spans, session ID, TTFT, linked traces
---

# Taking Tracing to Another Level

_13:30 · 45 min · Hands-on_

**Repo:** `langfuse-demo` · branch: `v1-baseline-tracing` → `v2-linked-traces`

---

## What tracing looks like right now

- **Two orphaned traces per turn** — litellm auto-creates one trace for the LLM call. We manually create another for retrieval. They are unrelated — no parent-child link.
- **No conversation view** — without a `session_id`, each turn is isolated. You cannot replay a conversation or see how turn 3 relates to turn 1.
- **No latency data** — we know the LLM's token count but not how long retrieval took, when the first token arrived (TTFT), or the total turn time.
- **No tags** — can't filter traces by model version, dataset, or experiment name.

> Result: traces you can't filter, link, or score. Hard to improve what you can't navigate.

---

## Five changes, one coherent trace

| # | Change | What it gives you |
|---|---|---|
| 01 | `session_id` — conversation grouping | Thread a stable session ID from the UI through every turn → full conversation replay in Langfuse |
| 02 | `start_trace()` — one parent per turn | Explicitly create a `rag_query` trace per turn. Everything else hangs off it. |
| 03 | `trace.span()` — retrieval as child span | Retrieval becomes a child span, not a top-level trace. Latency and chunk count recorded. |
| 04 | `existing_trace_id` — link LLM calls | Pass `metadata={"existing_trace_id": trace.id}` to litellm → generation attaches to parent. |
| 05 | TTFT + total latency | Measure time-to-first-token and full turn latency with `time.monotonic()`. |

---

## Change 01 — `session_id`: link turns into a conversation

_`app.py` · `pipeline.py`_

**Why:** without a `session_id`, each user turn is an isolated event. Langfuse can't group them into a conversation replay.

**What:** the UI generates a stable ID per chat session (`crypto.randomUUID()`) and sends it with every request. The pipeline threads it to the trace.

**Result in Langfuse:** Sessions view shows every turn in order — fully replayable and scoreable as a unit.

```python
# app.py — add to request model
class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None  # ← new


# pipeline.py — accept and forward
async def stream_answer(
    question: str,
    repo: ChunkRepository,
    session_id: str | None = None,  # ← new
) -> AsyncIterator[str]:
    ...
    trace = tracing.start_trace(
        question,
        session_id,     # ← passed through
        settings.llm_model,
    )
```

---

## Change 02 — `start_trace()`: one parent trace per turn

_`tracing.py`_

**v1:** litellm auto-creates a trace for the LLM call. Retrieval creates another. Both are top-level — unrelated.

**v2:** we explicitly create one `rag_query` trace per turn and get its ID. Everything else becomes a child of this parent.

**Also added:** `tags` let you filter by model or dataset in Langfuse dashboards.

```python
# tracing.py
def start_trace(question, session_id, model):
    if not _langfuse:
        return None
    return _langfuse.trace(
        name="rag_query",
        input={"question": question},
        session_id=session_id,         # ← groups turns
        tags=[model, "sherlock-holmes"],  # ← filterable
    )

# pipeline.py
trace = tracing.start_trace(question, session_id, settings.llm_model)
trace_id = trace.id if trace else None
```

---

## Change 03 — `trace.span()`: retrieval as a child span

_`tracing.py` · `pipeline.py`_

**v1:** retrieval is a top-level trace — not connected to the LLM call.

**v2:** retrieval becomes a child span of the parent trace. You see retrieval latency, chunk count, and source files — nested inside the turn.

**In Langfuse:** Trace tree: `rag_query` → `retrieval` span → `generation`. Click any span to inspect.

```python
# tracing.py
def record_retrieval(trace, chunks, start_time, end_time):
    if not trace:
        return
    latency_ms = (end_time - start_time).total_seconds() * 1000
    span = trace.span(name="retrieval", start_time=start_time, end_time=end_time)
    span.update(
        output={"num_chunks": len(chunks), "sources": [c.source for c in chunks]},
        metadata={"latency_ms": round(latency_ms, 1)},
    )

# pipeline.py
t_search_start = datetime.now(UTC)
chunks = await repo.similarity_search(vec, ...)
t_search_end = datetime.now(UTC)
tracing.record_retrieval(trace, chunks, t_search_start, t_search_end)
```

---

## Change 04 — `existing_trace_id`: link litellm calls to parent

_`embed.py` · `pipeline.py`_

**The trick:** litellm auto-traces every LLM call as a new top-level event. Passing `existing_trace_id` in the metadata dict tells it to attach this generation to our parent trace instead.

**Applies to both:** the embedding call (in `embed.py`) and the chat completion (in `pipeline.py`) — otherwise they float as separate top-level traces.

```python
# embed.py — link embedding to parent trace
async def embed(texts, model, trace_id=None):
    metadata = {"existing_trace_id": trace_id} if trace_id else {}
    response = await litellm.aembedding(model=model, input=texts, metadata=metadata)
    ...

# pipeline.py — link completion to parent trace
metadata = {"existing_trace_id": trace.id} if trace else {}
response = await litellm.acompletion(
    model=settings.llm_model,
    messages=[...],
    stream=True,
    metadata=metadata,  # ← attaches to parent
)
```

---

## Change 05 — TTFT + total latency

_`pipeline.py` · `tracing.py`_

**TTFT:** time-to-first-token is the most user-visible latency signal. Detected when the first streaming delta arrives.

**Total latency:** a single clock started at the top of the turn covers embed → retrieve → generate → last token.

**In Langfuse:** both values appear in `trace.metadata` — filterable in dashboards and usable as heuristic score dimensions.

```python
# pipeline.py
t0 = time.monotonic()           # turn starts

[vec] = await embed([question], ...)
# ... retrieval ...

t1 = time.monotonic()           # LLM starts
ttft_ms: float | None = None

async for chunk in response:
    if delta := chunk.choices[0].delta.content:
        if ttft_ms is None:
            ttft_ms = (time.monotonic() - t1) * 1000  # ← TTFT
        yield delta

tracing.end_trace(trace, ttft_ms, total_ms=(time.monotonic() - t0) * 1000)

# tracing.py
def end_trace(trace, ttft_ms, total_ms, answer=""):
    trace.update(
        output={"answer": answer} if answer else None,
        metadata={"ttft_ms": round(ttft_ms, 1) if ttft_ms else None,
                  "total_latency_ms": round(total_ms, 1)},
    )
```

---

## Lab · ~15 minutes

**Your turn.**

Switch to the `v2-linked-traces` branch and run the app.

Send a few questions, then open Langfuse and verify:

- → Each turn creates a single `rag_query` trace with a `retrieval` child span
- → All turns share the same `session_id` — visible in the Sessions view
- → TTFT and total latency appear in `trace.metadata`
