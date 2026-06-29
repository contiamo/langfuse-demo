from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row


@dataclass
class Chunk:
    source: str
    page: int | None
    content: str


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
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO document_chunks (source, page, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (source, chunk_index)
            DO UPDATE SET
                content   = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                page      = EXCLUDED.page
            """,
            (source, page, chunk_index, content, embedding),
        )
        await self._conn.commit()

    async def similarity_search(
        self, embedding: list[float], top_k: int = 5, min_similarity: float = 0.0
    ) -> list[Chunk]:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT source, page, content
                FROM document_chunks
                WHERE 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding, min_similarity, embedding, top_k),
            )
            rows = await cur.fetchall()
        return [
            Chunk(source=row["source"], page=row["page"], content=row["content"]) for row in rows
        ]

    async def close(self) -> None:
        await self._conn.close()
