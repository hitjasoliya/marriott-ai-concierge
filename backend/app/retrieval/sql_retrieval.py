from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Hotel


async def retrieve_by_filters(
    session: AsyncSession,
    city: str | None = None,
    hotel_type: str | None = None,
    budget_max: int | None = None,
    amenities: list[str] | None = None,
    limit: int = 50,
) -> list[Hotel]:
    conditions = []

    if city:
        conditions.append(Hotel.city.ilike(f"%{city}%"))

    if hotel_type:
        conditions.append(Hotel.hotel_type == hotel_type)

    if budget_max is not None:
        conditions.append(Hotel.price_per_night <= budget_max)

    stmt = select(Hotel)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    if amenities:
        for amenity in amenities:
            stmt = stmt.where(Hotel.amenities[amenity].isnot(None))
            stmt = stmt.where(Hotel.amenities[amenity] == True)

    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())
