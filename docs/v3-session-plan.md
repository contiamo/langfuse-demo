# V3 Session Plan — Evaluation Datasets + Scoring & Experiments

Two afternoon sessions merged into one continuous block with a natural coffee break.

---

## 14:15 — Block A: Building Evaluation Datasets (45 min)

**Goal:** participants leave with a 10–15 item dataset in Langfuse, built from their morning traces.

### Hands-on flow

1. **Run `task dataset:seed`** — bulk-creates dataset items from the morning's `rag_query` traces.
   Each item carries: `input: {question}`, `output: {answer}`, `source_trace_id` back to the live trace.

2. **In Langfuse UI → Datasets → sherlock-eval:**
   - Review auto-imported items
   - Add `expected_output` to a handful of items (the ones you know the right answer to)
   - Flag bad retrievals as failure-mode examples

3. **Three sources to over-represent:**
   - Hand-curated failures — red-card questions that gave weak answers (use 👎 scores from the morning)
   - Sampled v2 session traces — `task dataset:seed` covers this
   - Synthetic edge cases — add 2–3 manually via UI (e.g. cross-story questions, negation queries)

4. **Score Configs (UI → Settings → Score Configs):**
   Define dimensions once — `faithfulness`, `completeness`, `user_feedback` — these are reused by all evaluators.

### Key principle
Over-represent failure modes. Production traffic skews happy-path; your dataset should skew hard cases.

---

## 15:00 — Coffee break (15 min)

---

## 15:15 — Block B: Scoring & Experiments (45 min)

**Goal:** wire up automatic scoring, run a model-swap experiment, see score delta side by side.

### Tier 1 — Human signals (already done)
- 👍/👎 buttons write `user_feedback` scores to Langfuse in real time
- These are ground truth — use them to calibrate automated evaluators

### Tier 2 — Heuristics (already done in v2)
- TTFT on every trace
- Turn count via session grouping
- These are free, fast, and always on

### Tier 3 — LLM-as-Judge (Langfuse native — zero code)
- UI → Evaluators → "+ Set up Evaluator"
- Pick **RAGAS Faithfulness** managed evaluator (or write a custom rubric)
- Map trace fields: `input.question` → `{{input}}`, `output.answer` → `{{output}}`, retrieval span `chunks` → `{{context}}`
- Set judge model (GPT-4o, Claude Sonnet, or Gemini Pro)
- Save → runs automatically on every new trace from this point forward

### Experiment run (code)
```bash
task experiment:run   # run dataset through current config, store named run in Langfuse
```
Opens the Langfuse Experiments view — score delta visible side by side.

### Model swap experiment
Change one variable, re-run:
```bash
LLM_MODEL=gpt-4o task experiment:run --run-name gpt-4o-baseline
LLM_MODEL=gpt-4o-mini task experiment:run --run-name gpt-4o-mini-baseline
```
Compare faithfulness scores across runs in Langfuse UI.

### Regression gate
```bash
task regression:test   # exits non-zero if avg faithfulness < 0.70
```
Plug into CI — ship with confidence.

---

## What lives where

| Concern | Where |
|---|---|
| Bulk dataset creation | `task dataset:seed` (code) |
| Item review & expected_output | Langfuse UI → Datasets |
| Score Config definition | Langfuse UI → Settings |
| Human annotation queues | Langfuse UI → Annotation Queues |
| LLM-as-Judge (production) | Langfuse UI → Evaluators (auto, scales to thousands/min) |
| LLM-as-Judge (experiment scoring) | `scripts/run_experiment.py` (sync, for threshold gates) |
| Experiment comparison | Langfuse UI → Experiments |
| RAGAS metrics | Langfuse managed evaluator (no code) |
| Regression CI gate | `task regression:test` (code) |

---

## Take-home pointers (end of session)
- RAGAS full suite: context recall, context precision, answer relevancy — all available as Langfuse managed evaluators
- `task regression:test` is the CI gate — wire it to GitHub Actions on main
- Monitors (UI → Monitors) → alert on Slack when faithfulness drops below threshold in production
