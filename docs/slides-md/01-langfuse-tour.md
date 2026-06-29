---
title: Langfuse Feature Tour — Gen AI Engineering · Cornelsen
description: 45-minute tour of Langfuse — Observability, Prompt Management, Evaluation
---

# Langfuse Feature Tour

_11:15 · 45 min · Instructor-led concept_

Three pillars: **Observability · Prompt Management · Evaluation**

---

## One platform, three pillars

**Observability**
- Tracing — per-request logs of every LLM call
- Sessions — full conversation replay
- Users — per-user cost & feedback
- Dashboards — aggregated metrics & trends
- Monitors — threshold alerts → Slack / webhook

**Prompt Management**
- Prompts — versioned, deployed without redeploy
- Playground — test & refine in the browser

**Evaluation**
- Scores — structured quality annotations
- Evaluators — LLM-as-Judge at scale
- Human Annotation — structured reviewer workflow
- Datasets — versioned test suites for experiments

> The loop: trace → observe issues → build dataset → score → run experiment → ship with confidence

---

# Observability

_Pillar 1 of 3_

Tracing · Sessions · Users · Dashboards · Monitors

---

## Tracing

**The problem:** AI is non-deterministic — without a trace you can't reproduce a failure, find where latency spiked, or know exactly what prompt was sent.

**The concept:** A trace records one full request: prompt, model response, token counts, latency at each step, and any tool calls or retrieval steps. Traces send asynchronously — zero latency impact.

**How to use it:**
- Decorate functions with `@observe()` — auto-captures prompts, completions, token usage
- Tag traces with `environment`, `user_id`, and custom metadata for filtering
- View the trace tree: expand any span to inspect prompt, model params, latency, cost
- Use custom `trace_id` to correlate with your own distributed tracing systems

**Key terms:** `trace` · `span / observation` · `generation` · `@observe()` · `async flush`

---

## Sessions

**The problem:** Multi-turn conversations produce separate traces — you can't replay a conversation or understand why turn 4 failed given turns 1–3.

**The concept:** A session is a named group of traces linked by a shared `session_id` string. Langfuse renders them as a conversation replay in order.

**How to use it:**
- Pass `session_id` via `propagate_attributes()` — all nested observations inherit it
- The ID is any US-ASCII string under 200 chars — your existing chat/thread ID works
- Add session-level scores via SDK/API (e.g. end-of-conversation user feedback)
- Share a public session link for async review with teammates

**Key terms:** `session_id` · `session replay` · `propagate_attributes()` · `multi-turn`

---

## Users

**The problem:** Without user tracking you can't answer: which user is driving cost? Who gives negative feedback? How is a specific user's experience trending?

**The concept:** Set `user_id` on traces via `propagate_attributes()`. Langfuse auto-aggregates token cost, trace count, and scores per user.

**How to use it:**
- `propagate_attributes(user_id="...")` inside any `@observe()`-decorated function
- Open the Users list to rank by total token cost, trace volume, or quality score
- Click any user to see their full trace history — filter by time range or score
- Query per-user metrics via the Metrics API for custom dashboards

**Key terms:** `user_id` · `propagate_attributes()` · `per-user cost` · `Metrics API`

---

## Dashboards & Metrics

**The problem:** Raw traces tell you what happened on one request — not whether quality is improving or which model costs the most.

**The concept:** Langfuse Metrics derive structured analytics from traces: quality scores, cost and latency per user/session/model, volume trends. All sliceable by trace name, userId, tags, release string.

**How to use it:**
- Add a `name` field to traces to differentiate features — primary slice dimension in dashboards
- Add `tags` to group experiments, prompt variants, or deployment environments
- Set `release` version strings to compare metric trends across prompt or model changes
- Use the Metrics API to pull data into your own tooling

**Key terms:** `trace name` · `tags` · `release / version` · `Metrics API` · `PostHog export`

---

## Monitors _(Beta)_

**The problem:** Cost spikes and quality regressions are usually discovered by users before engineers.

**The concept:** A Monitor evaluates a metric query on a rolling time window and compares it against thresholds. Severity transitions (OK → WARNING → ALERT) fire linked Automations — Slack, webhook, or GitHub Actions.

**How to set up:**
1. Define the metric: data source, aggregation (avg/count/p95), filters
2. Set thresholds: warning level, alert level, evaluation window
3. Create an Automation (Slack/webhook/GitHub) and link it to the monitor
4. Save — monitor goes ACTIVE immediately

**Key terms:** `Monitor` · `Severity (OK/WARNING/ALERT)` · `Automation` · `Evaluation window`

---

# Prompt Management

_Pillar 2 of 3_

Prompts · Playground

---

## Prompts

**The problem:** Prompts hardcoded in source code require a deploy to change. No audit trail: who changed it, when, what did it say before?

**The concept:** Prompts are versioned in Langfuse with a name, type (`text` or `chat`), and `{{variable}}` template syntax. The `production` label marks the active version. SDK fetches it at runtime.

**How to use it:**
```python
# Create
langfuse.create_prompt(name="rag-answer", prompt="Answer {{question}}...", labels=["production"])

# Fetch at runtime (returns production version by default)
prompt = langfuse.get_prompt("rag-answer")

# Compile
compiled = prompt.compile(question="Why is the sky blue?")

# Pin a version for reproducible experiments
prompt = langfuse.get_prompt("rag-answer", version=3)
```

**Key terms:** `prompt version` · `label: production` · `compile()` · `get_prompt()`

---

## Playground

**The problem:** Iterating on prompts means switching between code editors, API clients, and observability tools — slow feedback loops.

**The concept:** Edit prompt text, set variables, adjust model params, and test tool-calling — all in the browser. Pull a failing trace directly into the Playground, tweak the prompt, immediately see the result.

**How to use it:**
- Import a versioned prompt, or open a failing generation directly from a trace
- Set prompt variables to simulate different inputs
- Compare multiple variants side-by-side — different model, temperature, system prompt
- Define tool schemas in JSON and test tool-calling behavior interactively
- Export the finalized prompt back to Prompt Management to version and deploy

**Key terms:** `prompt variables` · `side-by-side comparison` · `tool calling` · `structured output`

---

# Evaluation

_Pillar 3 of 3_

Scores · Evaluators · Human Annotation · Datasets

---

## Scores

**The problem:** Without a scoring layer, LLM quality is invisible. You can't tell if a prompt change helped or hurt, or catch regressions before shipping.

**The concept:** A Score is a named, typed value on a trace or observation — from a human annotator, a code check, or an LLM judge. All three sources write to the same Score table. Score Configs define dimensions and value ranges.

**How to use it:**
```python
# Define Score Configs once (UI → Settings → Score Configs)
# Then write scores from anywhere:
client.score.create(trace_id=..., name="faithfulness", value=0.85)
```

**Key terms:** `Score` · `Score Config` · `numeric / boolean / categorical` · `Score Analytics`

---

## Evaluators — LLM-as-Judge

**The problem:** Manual evaluation doesn't scale. String-match metrics miss nuanced dimensions like faithfulness or tone.

**The concept:** A judge LLM receives: input, output, optional reference, and a scoring rubric. Returns a score plus a reasoning trace. Runs automatically on new observations — every judge run is a debuggable trace.

**How to set up:**
1. UI → Evaluators → "+ Set up Evaluator" — choose Managed (incl. RAGAS) or Custom
2. Set judge model under LLM Connections (GPT-4o, Claude Sonnet, Gemini Pro)
3. Map trace fields to prompt variables with JSONPath — use live preview to verify
4. Debug via Tracing filtered to `environment: langfuse-llm-as-a-judge`

**Key terms:** `LLM-as-Judge` · `scoring rubric` · `RAGAS` · `reasoning trace`

---

## Human Annotation

**The problem:** Automated metrics can't capture judgments needing domain expertise or business context.

**The concept:** Annotators assign scores using predefined Score Configs. Annotation Queues let you work through large batches systematically. Human scores land in the same Score table as automated scores — directly comparable.

**Annotation workflow:**
1. Create Score Configs (e.g. "correctness", "tone") — sets evaluation dimensions
2. Open any trace → click Annotate → select Score Configs to apply
3. Set score values, optionally add a free-text comment
4. Use Annotation Queues to batch-route traces to reviewers for systematic coverage

**Key terms:** `Score Config` · `Annotation Queue` · `human baseline` · `ground truth`

---

## Datasets

**The problem:** Without shared datasets, regressions go unnoticed and you can't reproduce last week's experiment results.

**The concept:** A dataset item has an `input` and optional `expected_output`. Items come from real production failures (linked via `source_trace_id`), synthetic examples, or manual entry. Datasets are versioned.

**How to use it:**
```python
langfuse.create_dataset("rag-failures")

langfuse.create_dataset_item(
    dataset_name="rag-failures",
    input={"question": "..."},
    expected_output={"answer": "..."},
    source_trace_id="trace-abc123",
)

# Run an experiment
dataset.run_experiment(name="v2-test", task=my_llm_fn)
```

**Key terms:** `dataset item` · `expected_output` · `dataset version` · `experiment run` · `source_trace_id`

---

# The Full Loop

**Trace → Dataset → Score → Experiment → Ship**

---

## Glossary

| Term | Definition |
|---|---|
| `@observe()` | Decorator that auto-captures inputs, outputs, and timing as a Langfuse span |
| `Annotation Queue` | Batched list of traces routed to human reviewers for systematic scoring |
| `async flush` | SDK mechanism sending trace data in background threads — zero latency impact |
| `compile()` | SDK method substituting `{{variable}}` placeholders in a prompt template |
| `dataset item` | One row in a Dataset: input, optional expected_output, optional source_trace_id |
| `dataset version` | Point-in-time snapshot of dataset items — enables reproducible re-runs |
| `experiment run` | One execution of your task function against all dataset items |
| `generation` | Span type wrapping a single LLM call — auto-captures model, prompt, tokens, cost |
| `get_prompt()` | SDK method fetching a prompt; returns production version by default |
| `ground truth` | Human-verified expected output used to calibrate automated evaluators |
| `LLM-as-Judge` | Using a capable LLM to evaluate another LLM's output against a rubric |
| `Monitor` | Evaluates a metric query on a rolling window and fires Automations on threshold cross |
| `RAGAS` | Open-source RAG evaluation metrics available as Langfuse managed evaluators |
| `Score` | Named, typed value attached to a trace — universal output of all evaluation methods |
| `Score Config` | Reusable schema defining a score's name, type, and value range |
| `scoring rubric` | Criteria prompt given to an LLM judge defining what scores mean |
| `session_id` | String grouping multiple traces into one Session — any stable identifier |
| `source_trace_id` | Dataset item field linking it to the production trace it came from |
| `span / observation` | Single step inside a trace: LLM call, retrieval, tool invocation, or custom function |
| `trace` | Top-level record for one complete request — the fundamental unit of observability |
| `user_id` | Maps a trace to a specific end user — Langfuse aggregates cost and scores per user |
