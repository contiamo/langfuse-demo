# Workshop Demo — Rough Spec

## What it is

A simple RAG chat app participants can run locally and progressively instrument during the workshop.
Based on [`phlasse/nutrismart`](file:///Users/zastrow/code/phlasse/nutrismart) — same shape (PDF ingestion → vector search → streaming LLM → minimal web UI) but rebuilt with PydanticAI and LiteLLM.

Domain can stay nutrition or switch to something Cornelsen-adjacent (e.g. Q&A over a public textbook chapter). Domain doesn't matter — the instrumentation patterns do.

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Agent / RAG | PydanticAI | replaces nutrismart's hand-rolled pipeline |
| LLM | LiteLLM | model-agnostic; makes model-switching in experiments trivial |
| API | FastAPI | same as nutrismart |
| Frontend | Plain HTML/JS | same as nutrismart, minimal, not the point |
| Vector DB | PostgreSQL + pgvector | same as nutrismart |
| Package mgr | uv | same as nutrismart |
| Task runner | Taskfile | same as nutrismart, add regression:test |
| Eval | Langfuse SDK + RAGAS | baked in at v2/v3 |

## Three-version progressive instrumentation

This is the day's hands-on thread. Each version builds on the previous; participants start from v1 and work toward v3.

### v1 — Basic tracing (where most teams are)
- RAG retrieval logged as one top-level trace
- LLM completion logged as a separate top-level trace
- Token cost visible
- Nothing linked — no session, no spans, no scores

### v2 — Structured tracing
- One trace per user turn
- Spans inside: `retrieval` → `llm_call` (and optionally a `classifier` span to mirror the AI Chat cascade pattern)
- Session ID groups all turns of one conversation
- TTFT logged as a custom metric on the trace
- Tags: model version, document/domain tag

### v3 — Evaluation wired in
- Post-turn scoring: faithfulness (RAGAS), conversation quality (LLM-as-Judge)
- Turn count metric tracked at session level
- `task regression:test` runs `langfuse.run_experiment()` against the eval dataset and exits non-zero if faithfulness < threshold
- Langfuse LLM-as-a-Judge evaluator also configured in UI to run automatically on new traces

## Taskfile commands

```yaml
task run          # start API + frontend (docker compose up equivalent or uvicorn dev)
task stop         # stop services
task lint         # ruff check + format --check
task test         # unit + integration tests (no API key needed)
task regression:test  # run eval dataset via run_experiment(), assert score thresholds
```

## Repo structure (rough)

```
demo-rag/
├── src/
│   └── demo/
│       ├── agent.py          # PydanticAI agent definition
│       ├── pipeline.py       # RAG pipeline (retrieval + agent call)
│       ├── tracing.py        # Langfuse instrumentation (v1/v2/v3 lives here)
│       ├── ingestion/        # PDF parse + embed (reuse from nutrismart)
│       ├── retrieval/        # pgvector repository (reuse from nutrismart)
│       └── app.py            # FastAPI app
├── frontend/                 # static HTML/JS (reuse from nutrismart)
├── tests/
│   ├── test_pipeline.py      # unit tests (FakeLLM)
│   └── test_regression.py    # golden set / regression (requires Langfuse + API key)
├── data/                     # sample PDFs to ingest
├── Taskfile.yaml
├── pyproject.toml
├── uv.lock
├── docker-compose.yaml
└── .env.example
```

## Open questions

- Domain: keep nutrition or use a public Cornelsen/educational PDF? Nutrition is simpler and universally understood.
- Model default: OpenAI gpt-4o-mini (cheap, everyone has a key). LiteLLM makes it easy to switch.
- Does the repo need a pre-ingested dataset shipped with it, or do participants run `task ingest` themselves? Pre-ingested is safer for workshop timing.
- Public Contiamo GitHub org: confirm repo name before creating.
