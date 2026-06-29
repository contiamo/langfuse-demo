# RAG Demo — Langfuse Workshop

A minimal RAG chat app used in the Contiamo × Cornelsen Gen AI Engineering workshop.
Ask questions about a document corpus; every component is traced to Langfuse.

## What it does

- **Chat** — streaming question-answer interface served at `http://localhost:7932`
- **RAG** — embeds the question, finds the most relevant passages from the vector DB, feeds them as context to the LLM
- **Langfuse tracing** — two separate top-level traces per turn:
  - `retrieval` — logged via the Langfuse SDK: question in, chunk count and source files out
  - LLM call — logged automatically by litellm: full messages, response, token counts, cost

The workshop progresses from this baseline (v1) toward structured, linked traces (v2) and automated evaluation (v3).

## Stack

| Layer | Choice |
|---|---|
| LLM + embeddings | litellm (OpenAI by default, swap via `LLM_MODEL` env var) |
| Vector DB | PostgreSQL + pgvector |
| API | FastAPI (SSE streaming) |
| Tracing | Langfuse SDK + litellm callback |
| Runtime | Docker Compose |

## Setup

### 1. Prerequisites

- Docker + Docker Compose
- [Task](https://taskfile.dev) (`brew install go-task`)
- An OpenAI API key (or any litellm-compatible provider)

### 2. Configure

```bash
cp .env.example .env
# Fill in:
#   OPENAI_API_KEY=sk-...
#   LANGFUSE_PUBLIC_KEY=...   (get from cloud.langfuse.com)
#   LANGFUSE_SECRET_KEY=...
```

### 3. Start and ingest

```bash
task run        # build image + start DB and app

task migrate    # create DB schema (first time only)

# Download the demo dataset (Sherlock Holmes, public domain)
curl -o data/adventures-of-sherlock-holmes.txt \
  https://www.gutenberg.org/files/1661/1661-0.txt

task ingest     # embed and store — takes ~2 min
```

Open **http://localhost:7932** and start asking questions.

## Tasks

| Command | What it does |
|---|---|
| `task run` | Build image and start everything in Docker |
| `task stop` | Stop all containers |
| `task dev` | Run locally with hot-reload (needs DB running) |
| `task migrate` | Apply DB migrations |
| `task ingest` | Embed and store documents from `data/` |
| `task test` | Run unit tests (no API key needed) |
| `task lint` | Ruff check + format |

## Changing the model

Set `LLM_MODEL` in `.env` to any litellm-supported model string, then restart:

```
LLM_MODEL=gpt-4o-mini                                      # OpenAI (default)
LLM_MODEL=bedrock/anthropic.claude-3-sonnet-20240229-v1:0  # AWS Bedrock
LLM_MODEL=anthropic/claude-sonnet-4-6                       # Anthropic direct
```

No code changes needed — litellm routes automatically.

## Adding your own documents

Drop any `.pdf` or `.txt` file into `data/` and run `task ingest`.
The ingestion pipeline chunks, embeds, and upserts — re-running is safe (upsert on conflict).
