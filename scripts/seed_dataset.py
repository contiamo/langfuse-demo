"""Seed a Langfuse evaluation dataset from recent session traces.

Usage:  task dataset:seed
        uv run python scripts/seed_dataset.py [--dataset NAME] [--limit N]

Pulls traces tagged "sherlock-holmes" that have both input (question) and
output (answer), then creates dataset items linked to their source trace.
Participants can then open the dataset in Langfuse, review items, and add
expected outputs / quality scores.
"""
import argparse
import sys

DATASET_NAME = "sherlock-eval"
DEFAULT_LIMIT = 50


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Langfuse eval dataset from traces")
    parser.add_argument("--dataset", default=DATASET_NAME)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    from rag.config import get_settings

    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        print("No Langfuse credentials — set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        sys.exit(1)

    from langfuse import Langfuse

    lf = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )

    print(f"Fetching traces (limit {args.limit})...")
    traces = lf.get_traces(tags=["sherlock-holmes"], limit=args.limit)
    candidates = [t for t in traces.data if t.input and t.output]
    print(f"  {len(traces.data)} traces fetched, {len(candidates)} have input+output")

    if not candidates:
        print("No complete traces found. Ask some questions first, then re-run.")
        sys.exit(0)

    # Create dataset if it doesn't exist
    try:
        lf.get_dataset(args.dataset)
        print(f"Adding to existing dataset '{args.dataset}'")
    except Exception:
        lf.create_dataset(
            name=args.dataset,
            description="Sherlock Holmes RAG — built from session traces",
        )
        print(f"Created dataset '{args.dataset}'")

    created, skipped = 0, 0
    for trace in candidates:
        question = trace.input.get("question", "") if isinstance(trace.input, dict) else ""
        if not question:
            skipped += 1
            continue
        try:
            lf.create_dataset_item(
                dataset_name=args.dataset,
                input={"question": question},
                expected_output=None,  # participants fill this in during the lab
                source_trace_id=trace.id,
            )
            created += 1
            print(f"  + {question[:70]}")
        except Exception as e:
            print(f"  skip ({e}): {question[:50]}")
            skipped += 1

    print(f"\n{created} items added, {skipped} skipped.")
    print(f"Open Langfuse → Datasets → '{args.dataset}' to review and annotate.")


if __name__ == "__main__":
    main()
