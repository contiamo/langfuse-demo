# RAG Demo — Langfuse Workshop

A minimal RAG chat app used in the Contiamo × Cornelsen Gen AI Engineering workshop.
Ask questions about a Sherlock Holmes corpus; every component is traced to Langfuse.

## Workshop branches

| Branch | What participants start with |
|---|---|
| `v1-baseline-tracing` | Two separate, unlinked top-level traces per turn |
| `v2-linked-traces` | One parent trace per turn with child spans, session ID, latency |
| `v3-evaluation-datasets` | Full answer on trace, 👍/👎 feedback, dataset seeding, experiment runner |

## What it does

- **Chat** — streaming Q&A interface at `http://localhost:7932`, sidebar with sample questions
- **RAG** — embeds the question, finds the top-K passages from pgvector, feeds them as context to the LLM
- **Langfuse tracing** — per turn:
  - `litellm-aembedding` — embedding call with token count
  - `retrieval` span — chunk content, source files, latency
  - `litellm-acompletion` — full messages, response, tokens, cost
- **Feedback** — 👍/👎 buttons write `user_feedback` scores to Langfuse
- **Evaluation** — `task dataset:seed`, `task experiment:run`, `task regression:test`

## Stack

| Layer | Choice |
|---|---|
| LLM + embeddings | litellm (OpenAI by default, swap via `LLM_MODEL`) |
| Vector DB | PostgreSQL + pgvector |
| API | FastAPI (SSE streaming) |
| Tracing | Langfuse SDK + litellm callback |
| Runtime | Docker Compose |

## Setup

### 1. Prerequisites

- Docker + Docker Compose
- [Task](https://taskfile.dev) (`brew install go-task`) or [other installation method](https://taskfile.dev/docs/installation)
- [UV](https://docs.astral.sh/uv/) (`brew install uv`) or [other installation method](https://docs.astral.sh/uv/#installation)
- An OpenAI API key (or any litellm-compatible provider)

### 2. Configure

```bash
cp .env.example .env
# Fill in:
#   OPENAI_API_KEY=sk-...
#   LANGFUSE_PUBLIC_KEY=...
#   LANGFUSE_SECRET_KEY=...
```

### 3. Start and ingest

```bash
task run        # build image + start DB and app

task migrate    # create DB schema (first time only)

# Download the demo dataset (Sherlock Holmes, public domain)
curl -o data/a-study-in-scarlet.txt \
  https://www.gutenberg.org/files/244/244-0.txt

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
| `task migrate` | Apply DB migrations (first time only) |
| `task ingest` | Embed and store documents from `data/` |
| `task test` | Run unit tests (no API key needed) |
| `task lint` | Ruff check + format |
| `task dataset:seed` | Bulk-create Langfuse dataset items from recent traces |
| `task experiment:run` | Run dataset through live pipeline, store named run in Langfuse |
| `task regression:test` | Run experiment and exit non-zero if faithfulness < 0.70 |

## Changing the model

Set `LLM_MODEL` in `.env` to any litellm-supported model string, then `task run`:

```
LLM_MODEL=gpt-4o-mini                                      # OpenAI (default)
LLM_MODEL=bedrock/anthropic.claude-3-sonnet-20240229-v1:0  # AWS Bedrock
LLM_MODEL=anthropic/claude-sonnet-4-6                       # Anthropic direct
```

Model swap experiment — run the same dataset through two models and compare in Langfuse UI → Experiments:

```bash
LLM_MODEL=gpt-4o task experiment:run --run-name gpt-4o-test
LLM_MODEL=gpt-4o-mini task experiment:run --run-name mini-test
```

## Tuning retrieval

Two knobs in `.env`, no code changes:

| Variable | Default | Effect |
|---|---|---|
| `RETRIEVAL_TOP_K` | `5` | Number of chunks passed to the LLM as context |
| `RETRIEVAL_MIN_SIMILARITY` | `0.0` | Cosine similarity threshold (0–1). Raise to e.g. `0.75` to drop weakly-matching chunks. |

## Adding your own documents

Drop any `.pdf` or `.txt` file into `data/` and run `task ingest`.
Re-running is safe — ingestion upserts on `(source, chunk_index)`.

## Evaluation workflow (v3)

```
morning  → ask questions, click 👎 on bad answers
14:15    → task dataset:seed        # bulk-create dataset items from traces
           Langfuse UI → review items, add expected_output, tag failures
           Langfuse UI → Evaluators → set up LLM-as-Judge (RAGAS Faithfulness)
15:15    → task experiment:run      # run dataset, see score in Langfuse Experiments
           task regression:test     # CI gate — exits non-zero if score < 0.70
```

See `docs/v3-session-plan.md` for the full session plan.
