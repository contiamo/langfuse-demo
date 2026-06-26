"""Apply SQL migrations in order."""
import asyncio
from pathlib import Path

import psycopg


async def run_migrations(database_url: str) -> None:
    conn = await psycopg.AsyncConnection.connect(database_url, autocommit=True)
    migrations_dir = Path(__file__).parent
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        print(f"Applying {sql_file.name}...")
        await conn.execute(sql_file.read_text())
    await conn.close()
    print("Migrations done.")


def main() -> None:
    from rag.config import get_settings
    settings = get_settings()
    asyncio.run(run_migrations(settings.database_url))


if __name__ == "__main__":
    main()
