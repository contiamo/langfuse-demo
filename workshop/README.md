# workshop/ — PO/PM day toolkit

Parallel, additive tooling for the **PO/PM** variant of the workshop. Nothing here
imports from or modifies the application in `src/` — the generator drives the
running app purely over its HTTP API, so a PO/PM audience never touches code.

| File | What it is |
|---|---|
| `generate_traffic.py` | Black-box traffic generator — drives `/chat` + `/feedback` on the running app to populate a Langfuse project with realistic, partly-flawed data. Standard library only. |
| `questions.json` | The question bank: healthy · hard · out-of-corpus · multilingual · starved, some multi-turn. Editable without touching code. |
| `RUNBOOK.md` | Facilitator sequence to take an **empty** Langfuse project to fully populated before the day starts (~15 min). |

## Quick start

```bash
# 1. App running and pointed at your (empty) Langfuse project — see RUNBOOK.md §1
curl -s localhost:7932/health

# 2. Preview what will be sent (sends nothing)
python3 workshop/generate_traffic.py --list

# 3. Populate the project
python3 workshop/generate_traffic.py
```

Then `task dataset:seed` builds the eval dataset from the traces you just created.
See `RUNBOOK.md` for the full pre-workshop checklist, contrast passes, and the
optional v1-vs-v2 instrumentation demo.

## Why over HTTP?

- **Zero app changes** — the app runs exactly as shipped; this lives alongside it.
- **Real traces** — going through the real endpoints produces the same spans,
  sessions, tags, cost and latency a genuine user would, so `task dataset:seed`
  and the Langfuse UI behave identically to production.
- **No dependencies** — runs with system `python3`; no `uv sync`, no keys of its
  own (the app holds the credentials and does the tracing).
