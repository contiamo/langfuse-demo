# Gen AI Engineering for POs & PMs

_One day to define quality, read the evidence, and set a ship gate — hands-on, no code required._

**Cornelsen · Contiamo · Leipziger Straße 126, Berlin · 09:30 – 16:30**

> **The through-line:** turn "make the AI better" into a number you can defend.

This day mirrors the engineering workshop slot-for-slot — same spine (**quality criteria → dataset → score → experiment → gate**), taught from the "define and decide" side instead of the "instrument" side. All labs run on the shared Sherlock Holmes RAG demo, in the Langfuse UI, with no code.

---

## Day at a glance

**Morning**

| Time | Session | Duration | Format |
|---|---|---|---|
| 09:30 | Welcome & Framing | 15 min | Intro |
| 09:45 | GenAI in PO/PM & interfacing with GenAI-enabled engineers | 45 min | Field report |
| 10:30 | ☕ Coffee break | 15 min | |
| 10:45 | What does "good" look like? — define your quality criteria | 30 min | Working session |
| 11:15 | Langfuse for POs — a guided tour | 45 min | Instructor-led |
| 12:00 | Get into Langfuse | 15 min | Hands-on |
| 12:15 | 🍽 Lunch | 60 min | |

**Afternoon**

| Time | Session | Duration | Format |
|---|---|---|---|
| 13:15 | Reading the evidence — what a trace tells you | 15 min | Concept |
| 13:30 | Reading the evidence — hands-on | 45 min | Lab |
| 14:15 | Golden dataset, scoring & the ship/no-ship gate _(incl. ☕)_ | 90 min | Hands-on |
| 16:00 | Wrap-up: your first eval + the engineer contract, revisited | 30 min | Discussion |

---

## Sessions

### 09:30 · Welcome & Framing · 15 min · Intro

**Description:** Set the arc of the day and read the room.

**Content:**
- What to expect: define quality, read evidence, set a ship gate — hands-on, no code required
- The through-line: _"turn 'make the AI better' into a number you can defend"_
- The demo: a RAG app over Sherlock Holmes — small enough to see every part, real enough to reason about quality
- Quick round: who you are, what AI product you own, one thing you want to leave with

**Goal:** Everyone knows the shape of the day and has named a real product to apply it to.

---

### 09:45 · GenAI in PO/PM & Interfacing with GenAI-Enabled Engineers · 45 min · Field report

**Description:** How the PO/PM role shifts when engineering is agent-driven, and how to work across the handoff. The mirror of the engineering field report.

**Content** (Context · Workflow · Verification):
- **Context** — your written artifacts (PRDs, glossary, tone rules, quality criteria) are now _executable context_ the agents read; vague spec in → assumptions out
- **Workflow** — judgment moves up to spec & problem definition; review designs, not diffs; eval-first specs; cheap prototypes change how you discover
- **Verification** — you own the eval gate; traces & scores are the shared language; the demo is not the deliverable
- **The two-way contract** — what engineers now need from you vs. what you can expect from them; anti-patterns: demo-trust, velocity illusion, metric myopia

**Goal:** POs see clearly where their leverage moved, and leave with concrete practices to bring back to their team.

---

### 10:45 · What Does "Good" Look Like? — Define Your Quality Criteria · 30 min · Working session

**Description:** Turn fuzzy quality goals into measurable score dimensions — the core PM skill for AI features.

**Content:**
- Why "be more helpful" isn't shippable: you can't improve or defend what you can't measure
- Anatomy of a score dimension: name, type (numeric / boolean / categorical), what it rewards and penalizes
- Worked example on Sherlock (faithfulness, completeness, tone), then Cornelsen-flavored ones (factual accuracy, age-appropriateness, curriculum fit)
- Exercise: draft 2–3 score dimensions for your own product

**Goal:** Everyone walks out with a first-draft set of quality criteria they'll actually use in the afternoon.

---

### 11:15 · Langfuse for POs — A Guided Tour · 45 min · Instructor-led

**Description:** A tour of Langfuse from the "read and decide" side, not the "instrument" side.

**Content:**
- The three pillars reframed: Observability = evidence · Prompt Management = product config · Evaluation = your quality system
- What a trace, a session, and a score are — in plain terms, shown live on the demo
- Where POs actually work: annotation, datasets, dashboards, experiments, Playground
- What you can answer with it: is quality improving, which variant wins, how is a user's experience trending

**Goal:** POs can navigate Langfuse confidently and know which screens are theirs.

---

### 12:00 · Get Into Langfuse · 15 min · Hands-on (no code)

**Description:** Everyone logged in and oriented in the shared project before lunch.

**Content:**
- Credentials handed out; open the shared project
- Find the live Sherlock traces; open one; open a session replay
- Locate the Datasets, Score Configs, Evaluators, and Experiments tabs

**Goal:** No one is locked out or lost after lunch; everyone has clicked into a real trace.

---

### 13:15 · Reading the Evidence — What a Trace Tells You · 15 min · Concept

**Description:** How to read a trace and a session to understand what the AI actually did — debugging without code.

**Content:**
- The trace tree: question → retrieval → answer, with latency and cost at each step
- Reading a session: replay a multi-turn conversation, spot where it went wrong
- The signals a PO cares about: faithfulness, TTFT (user-perceived speed), cost per turn

**Goal:** POs can open a failure and explain it in product terms.

---

### 13:30 · Reading the Evidence — Hands-On · 45 min · Lab (no code)

**Description:** Find and diagnose real failures in the demo's traces; read the cost/latency story.

**Content:**
- Browse sessions, find a weak or wrong answer, trace it to the cause (bad retrieval vs. bad generation)
- Read cost & latency: what a slow TTFT means for UX, what a model choice costs per 1,000 questions
- Flag 3–5 failures you'd want fixed — these become dataset candidates

**Goal:** Each attendee has hands-on found a failure and a short list of items to seed a dataset.

---

### 14:15 · Golden Dataset, Scoring & the Ship/No-Ship Gate · 90 min (incl. ☕) · Hands-on

**Description:** The centerpiece — build a golden dataset by annotation, score it, and run the experiment that decides ship/no-ship.

**Content:**
- **Block A — Build the dataset:** seed items from traces, annotate against your quality criteria, add expected outputs, add a few synthetic edge cases
- Set up an LLM-as-Judge evaluator (no code) and watch scores attach automatically
- **Block B — Run an experiment:** compare two variants (model A vs. B, or prompt v1 vs. v2) side by side on faithfulness
- **The gate:** pick a threshold as a _product decision_ ("within 5% → ship the cheaper model"); watch the regression gate pass or fail

**Goal:** Everyone has run the full loop end-to-end and set a defensible ship criterion for a real feature.

---

### 16:00 · Wrap-Up: Your First Eval + The Engineer Contract, Revisited · 30 min · Discussion

**Description:** Consolidate the loop and close the arc the morning field report opened.

**Content:**
- The loop, recapped: quality criteria → dataset → score → experiment → gate
- Revisit the two-way contract now that you've felt it: what you'll ask engineers for, what you'll own
- Open floor: the first eval you'll add this week and your biggest blocker

**Goal:** Each attendee leaves with a concrete first eval to build and a clear next step with their team.
