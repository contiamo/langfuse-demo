# Facilitator Run-Book — PO/PM Workshop Data Setup

How to take a **brand-new, empty Langfuse project** and populate it with rich,
realistic, deliberately-flawed data before the PO/PM day starts — without
touching the application.

Everything here is **parallel and additive**: the app runs exactly as shipped;
`workshop/generate_traffic.py` only drives it over HTTP (`/chat`, `/feedback`).
Nothing in `src/` changes.

> **Time budget:** ~15 min for the main path. Do it before participants arrive.

---

## 0 · Prerequisites

- Docker running (for `task run`) — or the app already up on `http://localhost:7932`
- OpenAI API key
- A **new, empty Langfuse project** → copy its **public + secret keys**
- `python3` (standard library only — no install needed for the generator)

---

## 1 · Point the app at the empty project

Edit `.env` (copy from `.env.example` if needn't exist yet):

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...      # the NEW project
LANGFUSE_SECRET_KEY=sk-lf-...      # the NEW project
LANGFUSE_HOST=https://cloud.langfuse.com
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini              # default model for the main pass
WORKSHOP_USER=demo                 # optional: shows up as a user_id in Langfuse
```

Start (or restart) the app and confirm it's healthy:

```bash
task run          # build + start DB + app, auto-migrates
task setup        # one-time: download corpus + ingest (~2 min) — skip if data already ingested
curl -s localhost:7932/health   # -> {"status":"ok"}
```

---

## 2 · Main populate pass

Drive normal traffic through the running app. ~14 sessions, mix of good / hard /
out-of-corpus / German, with a realistic spread of 👍/👎:

```bash
python3 workshop/generate_traffic.py
```

Preview first without sending anything: `python3 workshop/generate_traffic.py --list`

**What lands in Langfuse:**
- Multi-turn **sessions** (`meeting`, `irene-adler`) → Sessions replay is meaningful
- Confident **failures to find**: `reichenbach`, `baskervilles`, `mycroft`, `anachronism` are outside the two ingested books → hallucination / refusal
- **Feedback** scores (`user_feedback`) on the flagged turns → dashboards show a 👍/👎 distribution
- German turns → language-robustness examples (relevant for Cornelsen)

Give the async flush a few seconds, then open Langfuse → **Tracing** to confirm rows appear.

---

## 3 · Optional contrast passes

Each pass = restart the app with different env, then run a labelled subset. The
`--session-prefix` keeps the batches identifiable in the Sessions view; the model
shows up automatically as a trace **tag**.

**a) Starved retrieval** (thin context → vague answers → 👎):

```bash
# restart app with a high similarity floor so few/no chunks come back
RETRIEVAL_MIN_SIMILARITY=0.9 task run
python3 workshop/generate_traffic.py --only starved --session-prefix "starved-"
# then restore normal retrieval for the rest of the day
task run
```

**b) Second model for a cost/latency story** (optional):

```bash
LLM_MODEL=gpt-4o task run
python3 workshop/generate_traffic.py --only healthy --session-prefix "gpt4o-"
LLM_MODEL=gpt-4o-mini task run    # restore default
```

**c) Multiple users** for a populated Users view (optional): run the main pass
2–3× with different `WORKSHOP_USER=alice` / `=bob` in `.env` between runs.

---

## 4 · Eval scaffolding

Now that traces exist, build the dataset and the experiment runs the afternoon
sessions read from:

```bash
task dataset:seed                                        # dataset "sherlock-eval" from tagged traces
task experiment:run -- --run-name gpt-4o-mini-baseline   # run 1
LLM_MODEL=gpt-4o task experiment:run -- --run-name gpt-4o-baseline   # run 2 (one variable changed)
```

Then set up the LLM-as-Judge **in the UI** (no code):

1. **Settings → Score Configs** — add `faithfulness` (numeric 0–1) and `tone` (categorical) so annotators and judges share dimensions
2. **Evaluators → + Set up Evaluator** — pick RAGAS Faithfulness (managed)
3. Under **LLM Connections**, set a judge model (e.g. GPT-4o)
4. Map fields: `input.question → {{input}}`, `output.answer → {{output}}`, retrieval span → `{{context}}`; verify with live preview
5. **Save** — new traces get scored automatically

---

## 5 · Participant access

POs need **browser logins to this one project only** — no Docker, no keys, no repo.

- Invite each attendee to the project (Settings → Members), or share a common login
- The "Get into Langfuse" 15-min slot is just: log in, open a trace, open a session

---

## 6 · The instrumentation progression — v1 → v2 → v3 (facilitator-driven)

Mirror the engineering workshop's step-by-step instrumentation — but as a **demo
POs watch**, not a coding lab. The **same generator runs unchanged on every
branch**; richer instrumentation simply lights up more of the trace. Use a
per-level `--session-prefix` so the three batches stay distinguishable in one
project (or point `.env` at a separate project per level).

```bash
# v1 — baseline: two orphan traces per turn, no grouping
git checkout v1-baseline-tracing && task run
python3 workshop/generate_traffic.py --only healthy --session-prefix "v1-"

# v2 — linked: one parent trace + retrieval span + session replay + TTFT
git checkout v2-linked-traces && task run
python3 workshop/generate_traffic.py --only healthy --session-prefix "v2-"

# v3 — full: + 👍/👎 feedback + full answer/context on the trace (dataset-ready)
git checkout v3-evaluation-datasets && task run     # or: main
python3 workshop/generate_traffic.py --session-prefix "v3-"

git checkout main   # full app for the rest of the day
```

**What the same traffic produces at each level** — the generator degrades
gracefully, and the gaps *are* the lesson:

| Branch | session grouping | trace shape | session replay | 👍/👎 feedback |
|---|---|---|---|---|
| v1 | — (session_id ignored) | two orphan traces / turn | ✗ | ✗ (auto-skipped) |
| v2 | ✓ | parent + retrieval span + TTFT | ✓ | ✗ (auto-skipped) |
| v3 / main | ✓ | + full answer & context on trace | ✓ | ✓ |

> On v1/v2 the generator's feedback simply doesn't attach — those branches have no
> `/feedback` endpoint and emit no `trace_id`, so it's skipped with no error. That
> is the very same reason those branches can't show a feedback dashboard.

**PO framing:** *how well a system is instrumented decides which product questions
you can even ask.* At v1 you can't tell which retrieval fed an answer or replay a
conversation; v2 unlocks both; v3 unlocks the feedback and full output that make
datasets, scoring, and experiments possible.

---

## 7 · Reset / re-run

- Re-running the generator **adds more** traffic (safe). To start clean, use a fresh Langfuse project (fastest) or clear data in the project settings.
- Full app reset: `docker compose down -v && rm -f data/*.txt && ./start.sh`

---

## Timing checklist (morning-of)

| When | Do |
|---|---|
| T-30 min | `.env` → new project keys · `task run` · `curl /health` |
| T-25 min | `python3 workshop/generate_traffic.py` (main pass) |
| T-20 min | (optional) starved + second-model passes |
| T-15 min | `task dataset:seed` · two `experiment:run`s |
| T-10 min | UI → Score Configs + RAGAS evaluator |
| T-5 min  | Confirm Tracing / Sessions / Datasets / Experiments all show data |
