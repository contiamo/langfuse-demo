---
title: Evaluation Datasets, Scoring & Experiments
description: 90-min hands-on — dataset curation, LLM-as-Judge, model swap experiment
---

# The Evaluation Loop

_14:15 – 16:00 · 90 min · Hands-on · `v3-evaluation-datasets`_

**Block A:** Building Evaluation Datasets · ☕ Break · **Block B:** Scoring & Experiments

---

# Block A: Building Evaluation Datasets from Your Traces

_14:15 · 45 min · Hands-on_

Branch: `v3-evaluation-datasets`
Scripts: `scripts/seed_dataset.py`

---

## Anatomy of a dataset item

_For a RAG application_

| Field | Required | Description | Example |
|---|---|---|---|
| `input` | ✓ | User question — re-run against every experiment | `"Where does Holmes live?"` |
| `expected_output` | optional | Reference answer for LLM judge comparison | `"221B Baker Street, with Dr. Watson"` |
| Retrieved context | optional | Chunks that came back — needed for faithfulness scoring | `"[study.txt, p.3]\nWe met next day..."` |
| `source_trace_id` | optional | Links item to the production trace it came from | `"trace-abc123"` |

---

## Three sources for dataset items

_Over-represent failure modes — production traffic skews happy-path_

**01 — Hand-curated failures** _(highest signal)_
- Browse your v2 session traces, flag responses that are wrong, vague, or hallucinated
- Add via UI or SDK with `source_trace_id`
- Production traffic skews happy-path — hunting failures corrects this bias

**02 — Sampled traces via seed** _(covered by `task dataset:seed`)_
- Pulls all traces tagged "sherlock-holmes", filters for complete input + output
- Links each item to its source trace — represents real usage

**03 — Synthetic edge cases** _(add manually in UI)_
- Questions outside the corpus, cross-story chains, questions in another language
- Generate with LLM: _"Write 5 questions the corpus probably can't answer."_

---

## `task dataset:seed` — bulk-create from traces

_`scripts/seed_dataset.py`_

**What it does:** fetches all traces tagged "sherlock-holmes" (up to 50), filters for ones with both input and output, creates dataset items — each linked to its source trace via `source_trace_id`.

**After running:** open Langfuse → Datasets → `sherlock-eval`. Items appear with the question, the model's answer, and a link back to the original trace. `expected_output` is blank — you fill that in for items you know the right answer to.

```python
lf = Langfuse(public_key=..., secret_key=...)

# 1. Pull recent traces with question + answer
traces = lf.get_traces(tags=["sherlock-holmes"], limit=50)
candidates = [t for t in traces.data if t.input and t.output]

# 2. Create dataset if it doesn't exist (idempotent)
lf.create_dataset(name="sherlock-eval")

# 3. Add one item per trace — linked to source
for trace in candidates:
    lf.create_dataset_item(
        dataset_name="sherlock-eval",
        input={"question": trace.input["question"]},
        expected_output=None,      # ← you fill this in
        source_trace_id=trace.id,  # ← links to live trace
    )
    print(f"  + {trace.input['question'][:70]}")
```

---

## Score Configs — define your dimensions once

_UI → Settings → Score Configs_

| Config | Type | Description |
|---|---|---|
| `faithfulness` | numeric 0–1 | Does the answer contain only information supported by the retrieved context? |
| `completeness` | numeric 0–1 | Does the answer address the full question, or does it dodge parts of it? |
| `user_feedback` | numeric 0 or 1 | Written by the 👍/👎 buttons in the frontend — already flowing into Langfuse |
| `retrieval_quality` | categorical: good/partial/poor | Manually annotated when reviewing dataset items |

> Define these now — every evaluator in Block B writes to the same Score Config names, making all sources directly comparable in Score Analytics.

---

## Lab A · ~15 minutes

**Build your dataset.**

1. Run `task dataset:seed` — watch items appear in Langfuse → Datasets → `sherlock-eval`
2. Open 3–5 items where the answer looks weak. Add `expected_output` for items you know the right answer to.
3. Add 2–3 synthetic edge cases manually via Langfuse UI (Datasets → + New item)
4. Create Score Configs: UI → Settings → Score Configs → add `faithfulness`, `user_feedback`

---

# ☕ Coffee Break

_Back at 15:15_

---

# Block B: Scoring & Experiments

_15:15 · 45 min · Hands-on_

Scripts: `scripts/run_experiment.py`
Tasks: `experiment:run` · `regression:test`

---

## Scoring: three tiers, one Score table

**T1 — Human signals** ✓ _already done_
- 👍/👎 in the frontend writes `user_feedback` scores
- Ground truth — use to calibrate automated judges
- Zero cost, real signal

**T2 — Heuristics** ✓ _already done (v2)_
- TTFT on every trace
- Turn count via session grouping
- Free, always on, no model cost
- Slow TTFT or high turn count often correlates with quality issues

**T3 — LLM-as-Judge** ← _wiring up now_
- Langfuse UI → Evaluators (auto, zero code)
- RAGAS managed evaluators (faithfulness, context recall)
- Custom rubric evaluators
- Runs asynchronously on every new trace — scales to thousands per minute

---

## Tier 3 — LLM-as-Judge: zero code required

_UI → Evaluators → + Set up Evaluator_

1. **Choose evaluator** — pick RAGAS Faithfulness (managed, no prompt writing) or write a Custom one with `{{variable}}` placeholders
2. **Set judge model** — under LLM Connections, pick a model supporting structured output: GPT-4o, Claude Sonnet, or Gemini Pro
3. **Map trace fields** — JSONPath: `input.question` → `{{input}}`, `output.answer` → `{{output}}`, retrieval span → `{{context}}`; use live preview to verify
4. **Save & watch** — activates immediately; every new trace gets a faithfulness score attached

> No deploy needed. The evaluator runs in Langfuse's cloud, not yours.

---

## `task experiment:run` — run dataset through live pipeline

_`scripts/run_experiment.py`_

**What it does:** pulls each dataset item, runs the question through the live RAG pipeline, stores results as a named experiment run in Langfuse, scores faithfulness synchronously.

**`item.observe()`** creates a trace linked to the dataset item and the run name. All child spans hang off it. The Langfuse UI shows runs side by side under the dataset.

```python
dataset = lf.get_dataset("sherlock-eval")

for item in dataset.items:
    question = item.input["question"]

    # observe() links trace to dataset item + run
    with item.observe(run_name=run_name) as trace:
        trace.update(tags=[settings.llm_model, "experiment"])

        answer_parts = []
        async for token in stream_answer(question, repo, trace, settings):
            answer_parts.append(token)
        answer = "".join(answer_parts)
        trace.update(output={"answer": answer})

    # synchronous faithfulness judge
    faith = await judge_faithfulness(question, context, answer, model)
    lf.score(trace_id=trace.id, name="faithfulness", value=faith)
    print(f"  {'✓' if faith else '✗'} {question[:65]}")
```

---

## Model comparison — change one variable

_`Taskfile.yaml` · UI → Experiments_

**The principle:** a valid experiment changes exactly one variable — the model — against a fixed dataset with a fixed score. Everything else stays constant.

```bash
# Run gpt-4o baseline
LLM_MODEL=gpt-4o task experiment:run -- --run-name gpt-4o-baseline

# Run gpt-4o-mini — same dataset, one variable changed
LLM_MODEL=gpt-4o-mini task experiment:run -- --run-name gpt-4o-mini-baseline
```

**In Langfuse UI:** Datasets → `sherlock-eval` → Experiments tab. Both runs appear side by side — per-item faithfulness scores, directly comparable.

**What to look for:** if `gpt-4o-mini` is within 5% faithfulness of `gpt-4o`, the cost saving is worth it. A 20%+ drop means it isn't.

---

## `task regression:test` — CI quality gate

_`scripts/run_experiment.py --threshold 0.70`_

**Same script, one flag:** `task regression:test` calls `run_experiment.py --threshold 0.70`. If average faithfulness falls below the threshold, the process exits 1 — blocking CI.

```python
# scripts/run_experiment.py (end of run())
avg = sum(scores) / len(scores)
if threshold is not None and avg < threshold:
    print(f"FAIL — {avg:.2f} below {threshold:.2f}")
    sys.exit(1)  # ← CI sees non-zero → blocks merge
```

```yaml
# GitHub Actions example
- name: Regression gate
  run: task regression:test
  env:
    LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
    LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Take-home:** RAGAS full suite (context recall, precision, answer relevancy) available as Langfuse managed evaluators. Monitors (UI → Monitors) can alert on Slack when faithfulness drops in production.

---

## Lab B · ~15 minutes

**Run the loop.**

1. UI → Evaluators → set up a RAGAS Faithfulness evaluator. Ask one question — verify the score appears.
2. Run `task experiment:run` — watch the experiment run appear in Langfuse Datasets → `sherlock-eval` → Experiments.
3. Change `LLM_MODEL=gpt-4o-mini` in `.env`, run again with a different `--run-name`. Compare faithfulness side by side.
4. Run `task regression:test` — see it pass or fail against the 0.70 threshold.

---

## Three ways to improve retrieval quality

_Now you have the evaluation loop to measure them_

**HyDE — embed a fake answer**
Ask the LLM to write a short hypothetical answer first, then embed that instead of the raw question. A fake answer uses the vocabulary of the source text and lands much closer to the real passage in embedding space.

**Query rewriting — match the corpus**
Ask the LLM to rephrase the question as keywords or a declarative statement matching the language of the source text. Cheaper than HyDE — good first A/B candidate.

**Multi-query retrieval — cast a wider net**
Generate 2–3 alternative phrasings, run each through the vector search, deduplicate and merge the results. Multiple retrieval spans visible in Langfuse per turn.

> Your dataset + regression gate is already in place — run any of these ideas through `task regression:test` to measure whether they actually help.
