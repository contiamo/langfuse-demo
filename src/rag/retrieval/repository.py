from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


@dataclass
class Chunk:
    id: UUID
    source: str
    page: int | None
    chunk_index: int
    content: str
    metadata: dict[str, Any]


class ChunkRepository:
    def __init__(self, conn: psycopg.AsyncConnection) -> None:
        self._conn = conn

    @classmethod
    async def create(cls, database_url: str) -> "ChunkRepository":
        conn = await psycopg.AsyncConnection.connect(database_url)
        await register_vector_async(conn)
        return cls(conn)

    async def upsert(
        self,
        source: str,
        page: int | None,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO document_chunks (source, page, chunk_index, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, chunk_index)
            DO UPDATE SET
                content   = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata  = EXCLUDED.metadata,
                page      = EXCLUDED.page
            """,
            (source, page, chunk_index, content, embedding, Jsonb(metadata or {})),
        )
        await self._conn.commit()

    async def similarity_search(self, embedding: list[float], top_k: int = 5) -> list[Chunk]:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, source, page, chunk_index, content, metadata
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding, top_k),
            )
            rows = await cur.fetchall()
        return [
            Chunk(
                id=row["id"],
                source=row["source"],
                page=row["page"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                metadata=row["metadata"],
            )
            for row in rows
        ]

    async def close(self) -> None:
        await self._conn.close()
