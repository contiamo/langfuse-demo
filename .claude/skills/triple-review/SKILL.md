---
name: triple-review
description: Comprehensive PR review using three AI models (Claude, Gemini, GPT-5) in parallel. Use when the user asks for a triple review, multi-model review, or wants a thorough PR analysis from multiple perspectives.
---

# Triple Review

A comprehensive PR review process that leverages three AI models in parallel to provide thorough code analysis.

## Overview

This skill orchestrates a multi-model PR review by:
1. Fetching PR details and checking out the branch locally
2. Spawning three review agents in parallel (Claude, Gemini via gemini-delegator, GPT-5 via codex-delegator)
3. Consolidating findings, separating legitimate concerns from overstated issues
4. Presenting a narrative summary followed by a structured issue table
5. (On request) Posting selected issues as inline PR comments

## Invocation

User provides a PR URL or number:
- "Triple review PR #42"
- "Triple review https://github.com/org/repo/pull/42"

## Phase 1: Setup

1. Extract PR number from user input
2. Fetch PR details using `gh pr view {number} --json title,body,headRefName,baseRefName,files,author`
3. Fetch the diff using `gh pr diff {number}`
4. Checkout the PR branch locally: `git fetch origin {branch} && git checkout {branch}`

## Phase 2: Parallel Review

Spawn three agents in parallel using the Task tool in a single message:

### Claude Agent (subagent_type: general-purpose)
```
Review PR #{number} "{title}". Analyze:
- Code quality and best practices
- Security issues
- Error handling
- Test coverage
- Bugs or logic issues
- Performance concerns

Provide findings with file:line references.
```

### Gemini Agent (subagent_type: gemini-delegator)
```
Review PR #{number} "{title}" at {repo_path}. Analyze code quality, security,
error handling, tests, performance, and RAG/ML best practices if applicable.
Provide findings with file:line references.
```

### GPT-5 Agent (subagent_type: codex-delegator)
```
Review PR #{number} "{title}" at {repo_path}. Analyze code quality, security,
error handling, tests, performance. Provide findings with file:line references.
```

## Phase 3: Consolidate and Analyze

After all agents complete:
1. Parse each agent's output for issues
2. Deduplicate similar findings (one row per unique issue)
3. Categorize by severity: Critical, High, Medium, Low
4. Note which models flagged each issue (multiple flags suggests higher importance)
5. Distinguish between legitimate concerns vs overstated issues (consider threat model, dev tools vs production code, etc.)

## Phase 4: Present Analysis to User

Present a comprehensive analysis in two parts:

### Part 1: Free Text Summary (~400 words)

Write a narrative summary covering:

1. **What the PR does** - The actual intent and main changes, not just the title
2. **Why** - The motivation, problem being solved, or feature being added
3. **Structure** - How the changes are organized, key files, architecture decisions
4. **PR hygiene** (only if glaring issues) - Is the title accurate? Is it atomic or overloaded? Multiple PRs smashed together?
5. **Legitimate concerns** - Real issues that should be addressed
6. **Overstated concerns** - Issues flagged by reviewers that aren't actually problems (e.g., "security issues" in dev scripts that assume attacker has filesystem access)
7. **Bottom line** - Overall assessment and what actually matters

Be direct and opinionated. Call out when reviewer findings miss the threat model or when the PR title undersells/oversells the changes.

### Part 2: Issue Table

Present a table of all unique issues:

| # | Severity | File:Line | Issue | Flagged By |
|---|----------|-----------|-------|------------|
| 1 | Critical | `path/file.py:42` | Single sentence describing the issue | Claude, Gemini |
| 2 | High | `path/other.py:100` | Single sentence describing the issue | GPT-5 |

**Severity guidelines:**
- **Critical**: Security vulnerabilities, data loss, production outages
- **High**: Bugs, GDPR violations, missing required functionality
- **Medium**: Performance issues, code quality, missing validation
- **Low**: Style, minor improvements, nice-to-haves

**Note:** Issues flagged by multiple models are likely more important. Issues only one model caught may be either insightful or false positives - use judgment.

Do NOT ask the user which issues to post as comments. If they want to post comments, they will tell you.

## Phase 5: Post Comments (On User Request Only)

Only execute this phase if the user explicitly asks to post comments.

### Comment Style Guide

Comments must be:
- Brief and tight (no purple prose)
- Phrased as questions with humility
- No emojis

**Good examples:**
```
When force_reingest=True, are existing chunks deleted before re-running
the pipeline? If not, this could accumulate duplicate embeddings.
```

```
Should this use validation_alias instead of alias? As-is, I don't think
the env var will bind correctly. Could be wrong though.
```

```
Is logging document content here intentional? Wondering if this could be
a GDPR/PII concern. Maybe just log source and score?
```

**Bad examples (avoid):**
```
This is a critical bug that must be fixed immediately!
```

```
Great code! Just one small suggestion...
```

### Posting Process

1. Verify each issue's line is in the PR diff
   - Use `gh pr diff {number}` to check hunk ranges
   - Only lines in `+` sections of the diff can have inline comments
   - For issues on pre-existing code, mention in the review body instead

2. Build review JSON:
```json
{
  "commit_id": "{head_sha}",
  "body": "Review summary. Note: Some issues affect pre-existing code not in this PR.",
  "event": "REQUEST_CHANGES",
  "comments": [
    {
      "path": "path/to/file.py",
      "line": 42,
      "body": "Comment text in question format..."
    }
  ]
}
```

3. Post review:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --method POST \
  --input /tmp/pr_review.json
```

4. Assign to PR author:
```bash
AUTHOR=$(gh pr view {number} --json author -q .author.login)
gh api repos/{owner}/{repo}/issues/{number} \
  --method PATCH \
  -f "assignees[]=$AUTHOR"
```

## Error Handling

- If a reviewer agent fails, continue with results from others
- If no issues found, note this in the summary
- When posting comments: if line not in diff, mention in review body instead
- If gh commands fail, report error and suggest manual action

## Reference Files

See [comment-examples.md](comment-examples.md) for more comment style examples.