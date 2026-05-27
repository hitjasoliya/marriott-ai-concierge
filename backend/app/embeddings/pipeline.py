import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.embeddings.model import embed_batch

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://marriott:password@localhost:5432/marriott_hotels")


async def embed_all():
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(text("SELECT id, semantic_text FROM hotels"))
        rows = result.fetchall()

        hotel_ids = [row[0] for row in rows]
        texts = [row[1] for row in rows]

        print(f"Embedding {len(texts)} hotels...")
        embeddings = embed_batch(texts)

        for hid, emb in zip(hotel_ids, embeddings):
            await session.execute(
                text("UPDATE hotels SET embedding = :embedding WHERE id = :id"),
                {"embedding": emb, "id": hid},
            )
        await session.commit()

    print(f"Updated embeddings for {len(hotel_ids)} hotels.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(embed_all())
