---
title: Workshop Overview — Gen AI Engineering · Cornelsen
description: MC deck — full day overview, session dividers, support slides
---

# From Traces to Evals.

One day to instrument, evaluate, and run experiments — hands-on.

**Cornelsen Engineering**
Contiamo · Leipziger Straße 126, Berlin · 09:30 – 16:30

---

# Day at a glance

**Morning**

| Time | Session | Duration |
|---|---|---|
| 09:30 | Welcome & Framing | 15 min |
| 09:45 | AI-Assisted Coding for GenAI Engineering | 45 min |
| 10:30 | ☕ Coffee break | 15 min |
| 10:45 | What Does Success Look Like for Your Product? | 30 min |
| 11:15 | Langfuse Feature Tour | 45 min |
| 12:00 | Demo Setup | 15 min |
| 12:15 | 🍽 Lunch | 60 min |

**Afternoon**

| Time | Session | Duration |
|---|---|---|
| 13:15 | What Basic Tracing Looks Like | 15 min |
| 13:30 | Taking Tracing to Another Level | 45 min |
| 14:15 | Evaluation Datasets, Scoring & Experiments | 90 min |
| 16:00 | Wrap-up | 30 min |

---

# Welcome & Framing

_09:30 · 15 min · Intro_

---

## Welcome — quick round of introductions

- **What you can expect:** hands-on tracing, evaluation, and experiments — all on a shared demo app we extend together
- **Agenda:** Langfuse tour → demo setup → tracing v1 → v2 → evaluation datasets → scoring & experiments
- **The demo:** a RAG app over Sherlock Holmes — simple enough to see every moving part, real enough to instrument properly
- **Format:** concept slides → hands-on labs alternating — you'll leave with code you wrote yourself
- **Quick round:** who are you, what AI product are you working on, what's one thing you want to take away?

> No prior Langfuse experience needed. Bring curiosity and your product context.

---

# AI-Assisted Coding for GenAI Engineering

_09:45 · 45 min · Field report_

→ **Breakout deck:** `05-ai-assisted-coding`

---

# ☕ Coffee Break

_Back at 10:45_

---

# What Does Success Look Like for Your Product?

_10:45 · 30 min · Facilitated discussion_

---

## How do we know the AI is getting better?

- **The core question:** what would need to be measurably true for you to say "we improved the AI this sprint"?
- **Signal, not feeling** — a metric you can track over time: faithfulness score, error rate, TTFT, turns to resolution
- **Catching regressions** — how do you know a prompt change didn't silently make things worse?
- **Comparing variants** — model A vs. model B, prompt v1 vs. v2: what's your decision criterion?
- **Exercise:** each team names 1–2 quality signals for their product. What would you put on a dashboard?

> These signals become your dataset rubric and your experiment gate later today.

---

# Langfuse Feature Tour

_11:15 · 45 min · Instructor-led concept_

→ **Breakout deck:** `01-langfuse-tour`

---

# Demo Setup

_12:00 · 15 min · Hands-on_

---

## Get the demo running

| Step | Action | Note |
|---|---|---|
| **Repo** | `github.com/contiamo/langfuse-demo` → branch `v1-baseline-tracing` | VPN required |
| **API key** | OpenAI key — bring your own | via VPN if needed |
| **Langfuse creds** | public key + secret key — provided by us today | |
| **Start** | `cp .env.example .env` → `task run` → `task migrate` → `task ingest` | ~2 min |
| **Verify** | Open `http://localhost:7932`, ask a question, check Langfuse → Tracing | before lunch |

---

# 🍽 Lunch

_Back at 13:15_

---

# What Basic Tracing Looks Like

_13:15 · 15 min · Concept_

→ **Breakout deck:** `02-tracing-v1`

---

# Taking Tracing to Another Level

_13:30 · 45 min · Hands-on_

→ **Breakout deck:** `03-tracing-v2`

---

# Evaluation Datasets, Scoring & Experiments

_14:15 · 90 min (incl. ☕ at 15:00) · Hands-on_

→ **Breakout deck:** `04-evaluation-datasets`

---

# Wrap-up: What Did You Take Away?

_16:00 · 30 min · Open discussion_

---

## What did you take away?

- The loop: **trace** → **dataset** → **score** → **experiment** → ship with a regression gate
- **Cosmo:** what's the first eval you'll add this week? What's your blocker?
- **AI Chat:** did retrieval pull the right page? Did the answer stay faithful to the source?
- Multi-step systems: per-step scores vs. end-to-end score — which matters for your rollout decision?
- **Open floor:** what's the first eval you'd add to your product? What's the biggest obstacle?

> The demo repo stays public — take the patterns, adapt them to your stack.
