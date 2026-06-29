---
title: AI-Assisted Coding for GenAI Engineering
description: Field report — how we build software with coding agents at Contiamo: context, workflow, verification
---

# How We Build With AI

AI-assisted coding for GenAI engineering — the practices we've converged on at Contiamo, and why.

**Gen AI Engineering Workshop · Cornelsen**
09:45 · Leipziger Straße 126, Berlin

---

# A field report, not a tutorial

_You already use these tools every day. So this is simply how we build software with coding agents at Contiamo — the practices we've converged on, and the ones we're convinced of._

---

# Context

_Part one of three · What the agent can see before it writes a line of code_

---

## Context, in layers

| Layer | Source | What it gives the agent |
|---|---|---|
| **All** | `contiamo-context` plugin | A short shared baseline injected into every session — who we are, how we work |
| **Repo** | `CLAUDE.md` / `AGENTS.md` | Per-project manual: conventions, architecture, commands — auto-loaded |
| **Team** | Skills marketplace | Our own GitHub repo; expert-owned skills for conventions, deployment, secrets |
| **Live** | Connected systems | Tasks → Linear · Knowledge → Notion · Discussions → Slack |
| **Task** | Docs & references | Docs for libraries we use, relevant GitHub repos, whatever the task needs |

---

# Workflow

_Part two of three · Align on the plan, then let it build_

---

## Decide the design. Delegate the build.

- **Plan → review → iterate, then implement in auto mode** — once the plan is agreed, implementation runs unsupervised, start to finish
- **Design docs for anything new** — implementation is cheap, so the discussion lives at the design level
- **Parallel sessions and subagents** — investigate across many; subagents report back just the conclusion, not the noise
- **The right model for the job** — Opus for hard design and review, faster models for mechanical work
- **Sandboxed where security is crucial** — on sensitive projects, agents run isolated from the host

> The expensive judgement moved up to design — that's where our attention goes.

---

# Verification

_Part three of three · Nothing ships unseen_

---

## Autonomy is safe because checking is built in

- **One command to run, test, lint, format** — so the agent can prove its change works; that's its feedback loop
- **Each agent gets its own running stack** — Compose boots parallel instances; validate live UI, API, DB; pairs with worktrees
- **Langfuse as a verification source** — agents read the traces and run tests against datasets to check real behaviour
- **Cross-model review before every PR** — Claude, Codex and Gemini review the change before a human opens it
- **Human author review owns the merge** — a person stays accountable for what ships

> Unsupervised building only works because verification is layered and never skipped.

---

## What you might take from this

_If you try one thing:_

- **A short shared context baseline** — one small file, injected into every session
- **A `CLAUDE.md` in your main repo** — conventions and commands the agent can read
- **`run` / `test` / `lint` as one command each** — give the agent a way to check itself
- **An agent review step before PRs** — a second set of eyes that never gets tired
