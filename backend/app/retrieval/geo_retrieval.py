from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Hotel


async def retrieve_by_radius(
    session: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 30.0,
    limit: int = 50,
) -> list[tuple[Hotel, float]]:
    stmt = text("""
        SELECT h.*, ST_Distance(h.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS distance_m
        FROM hotels h
        WHERE ST_DWithin(
            h.geom,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            :radius_m
        )
        ORDER BY distance_m ASC
        LIMIT :limit
    """)

    result = await session.execute(stmt, {
        "lat": latitude,
        "lon": longitude,
        "radius_m": radius_km * 1000,
        "limit": limit,
    })

    rows = result.fetchall()
    hotels = []
    for row in rows:
        hotel = Hotel(
            id=row.id,
            name=row.name,
            brand=row.brand,
            city=row.city,
            latitude=row.latitude,
            longitude=row.longitude,
            description=row.description,
            semantic_text=row.semantic_text,
            embedding=row.embedding,
            rating=row.rating,
            amenities=row.amenities,
            price_per_night=row.price_per_night,
            hotel_type=row.hotel_type,
        )
        distance_km = row.distance_m / 1000.0 if row.distance_m else float("inf")
        hotels.append((hotel, distance_km))

    return hotels
