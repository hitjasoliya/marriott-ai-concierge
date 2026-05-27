import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.seed.data import HOTELS
from app.embeddings.model import embed_batch
from app.db.models import Hotel

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://marriott:password@localhost:5432/marriott_hotels")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(lambda sync_conn: __import__("app.db.models", fromlist=["Hotel"]))

    semantic_texts = [h["semantic_text"] for h in HOTELS]
    print(f"Embedding {len(semantic_texts)} hotel descriptions...")
    embeddings = embed_batch(semantic_texts)

    async with session_factory() as session:
        hotels = []
        for i, hotel_data in enumerate(HOTELS):
            hotel = Hotel(
                name=hotel_data["name"],
                brand=hotel_data["brand"],
                city=hotel_data["city"],
                latitude=hotel_data["latitude"],
                longitude=hotel_data["longitude"],
                description=hotel_data["description"],
                semantic_text=hotel_data["semantic_text"],
                embedding=embeddings[i],
                rating=hotel_data["rating"],
                amenities=hotel_data["amenities"],
                price_per_night=hotel_data["price_per_night"],
                hotel_type=hotel_data["hotel_type"],
                geom=from_shape(Point(hotel_data["longitude"], hotel_data["latitude"]), srid=4326),
            )
            hotels.append(hotel)

        session.add_all(hotels)
        await session.commit()

    print(f"Seeded {len(HOTELS)} hotels with embeddings.")

    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM hotels"))
        count = result.scalar()
        print(f"Verification: {count} hotels in database.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
