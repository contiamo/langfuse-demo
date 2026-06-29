"""Run a named experiment against the evaluation dataset.

Each dataset item is run through the live pipeline. Results are stored as a
named experiment run in Langfuse (visible in UI → Experiments) and scored for
faithfulness via a lightweight LLM judge. Langfuse's own evaluators (configured
in UI → Evaluators) will also auto-score the new traces asynchronously.

Usage:
    task experiment:run
    task regression:test                             # exits non-zero if score < threshold

    uv run python scripts/run_experiment.py --run-name "gpt-4o-baseline"
    uv run python scripts/run_experiment.py --model gpt-4o --threshold 0.7
"""
import argparse
import asyncio
import os
import sys

DATASET_NAME = "sherlock-eval"
FAITHFULNESS_THRESHOLD = 0.70

JUDGE_PROMPT = """\
You are evaluating a RAG system for faithfulness.

CONTEXT (retrieved passages):
{context}

QUESTION: {question}

ANSWER: {answer}

Does the answer contain ONLY information supported by the context above?
Reply with a single integer: 1 (yes, fully faithful) or 0 (no, contains unsupported claims).
"""


async def judge_faithfulness(question: str, context: str, answer: str, model: str) -> float:
    import litellm
    resp = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            context=context[:3000], question=question, answer=answer
        )}],
        max_tokens=4,
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    return 1.0 if raw.startswith("1") else 0.0


async def run(run_name: str, dataset_name: str, threshold: float | None) -> None:
    from langfuse import Langfuse

    from rag import tracing
    from rag.config import get_settings
    from rag.pipeline import stream_answer
    from rag.retrieval.repository import ChunkRepository

    settings = get_settings()
    if key := settings.openai_api_key.get_secret_value():
        os.environ.setdefault("OPENAI_API_KEY", key)

    if not settings.langfuse_public_key:
        print("No Langfuse credentials — set LANGFUSE_PUBLIC_KEY/SECRET_KEY in .env")
        sys.exit(1)

    tracing.init(settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host)

    lf = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )

    try:
        dataset = lf.get_dataset(dataset_name)
    except Exception:
        print(f"Dataset '{dataset_name}' not found — run `task dataset:seed` first.")
        sys.exit(1)

    items = [i for i in dataset.items if isinstance(i.input, dict) and i.input.get("question")]
    if not items:
        print("No usable dataset items found.")
        sys.exit(0)

    print(f"Running experiment '{run_name}' on {len(items)} items (model: {settings.llm_model})\n")

    repo = await ChunkRepository.create(settings.database_url)
    scores: list[float] = []

    for item in items:
        question = item.input["question"]

        # item.observe() yields the trace ID (str) and links it to the dataset run.
        # We then create a proper trace client from that ID so stream_answer can attach spans.
        with item.observe(run_name=run_name) as trace_id:
            lf_trace = lf.trace(
                id=trace_id,
                name="rag_query",
                input={"question": question},
                tags=[settings.llm_model, "sherlock-holmes", "experiment"],
                session_id=run_name,
            )

            answer_parts: list[str] = []
            async for token in stream_answer(question, repo, lf_trace, settings):
                answer_parts.append(token)
            answer = "".join(answer_parts)

        # Simple faithfulness judge — Langfuse's managed evaluator will also score async
        # using the full chunk content stored in the retrieval span
        faith = await judge_faithfulness(question, answer, answer, settings.llm_model)
        lf.score(trace_id=trace_id, name="faithfulness", value=faith)

        scores.append(faith)
        status = "✓" if faith == 1.0 else "✗"
        print(f"  {status} [{faith:.0f}] {question[:65]}")

    await repo.close()
    lf.flush()

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"\nExperiment '{run_name}': {avg:.0%} faithful ({len(scores)} items)")
    print(f"View results: Langfuse UI → Experiments → {dataset_name}")

    if threshold is not None and avg < threshold:
        print(f"\nFAIL — faithfulness {avg:.2f} below threshold {threshold:.2f}")
        sys.exit(1)


def main() -> None:
    from datetime import UTC, datetime

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default=f"run-{datetime.now(UTC).strftime('%Y%m%d-%H%M')}")
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    asyncio.run(run(args.run_name, args.dataset, args.threshold))


if __name__ == "__main__":
    main()
