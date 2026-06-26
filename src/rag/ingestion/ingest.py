"""CLI: ingest PDFs and TXT files from a directory into the vector DB."""
import argparse
import asyncio
import os
from pathlib import Path

EMBED_BATCH_SIZE = 32
SUPPORTED = {".pdf", ".txt"}


async def run(source_dir: Path) -> None:
    from rag.config import get_settings
    from rag.ingestion.embed import LiteLLMEmbeddingService
    from rag.ingestion.parse import parse_file
    from rag.retrieval.repository import ChunkRepository

    settings = get_settings()
    if settings.openai_api_key.get_secret_value():
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key.get_secret_value())

    repo = await ChunkRepository.create(settings.database_url)
    embedder = LiteLLMEmbeddingService(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )

    files = sorted(p for p in source_dir.iterdir() if p.suffix.lower() in SUPPORTED)
    if not files:
        print(f"No supported files ({', '.join(SUPPORTED)}) found in {source_dir}")
        return

    for path in files:
        print(f"Processing {path.name}...")
        chunks = parse_file(path)
        print(f"  {len(chunks)} chunks")

        for i in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[i : i + EMBED_BATCH_SIZE]
            embeddings = await embedder.embed([c.content for c in batch])
            for chunk, embedding in zip(batch, embeddings):
                await repo.upsert(
                    source=chunk.source,
                    page=chunk.page,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=embedding,
                    metadata=chunk.metadata,
                )
            print(f"  upserted {i}–{i + len(batch) - 1}")

    await repo.close()
    print(f"\nDone. Ingested {len(files)} file(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the RAG demo vector DB")
    parser.add_argument("--source-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    asyncio.run(run(args.source_dir))


if __name__ == "__main__":
    main()
