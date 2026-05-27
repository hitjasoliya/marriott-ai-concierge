from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Hotel
from app.embeddings.model import embed_text


async def rerank_by_semantic_similarity(
    session: AsyncSession,
    query: str,
    hotels: list[Hotel],
) -> list[tuple[Hotel, float]]:
    if not hotels:
        return []

    query_embedding = embed_text(query)

    hotel_ids = [h.id for h in hotels]

    stmt = text("""
        SELECT id, 1 - (embedding <=> :query_vec) AS similarity
        FROM hotels
        WHERE id = ANY(:ids)
        ORDER BY similarity DESC
    """)

    result = await session.execute(stmt, {
        "query_vec": query_embedding,
        "ids": hotel_ids,
    })

    similarity_map = {row.id: row.similarity for row in result.fetchall()}

    scored = []
    for hotel in hotels:
        sim = similarity_map.get(hotel.id, 0.0)
        scored.append((hotel, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def build_query_semantic_text(intent: dict) -> str:
    parts = []

    semantic_intent = intent.get("semantic_intent", [])
    if semantic_intent:
        parts.append("semantic intents: " + ", ".join(semantic_intent))

    hotel_type = intent.get("hotel_type")
    if hotel_type:
        parts.append(f"hotel type: {hotel_type}")

    requested_amenities = intent.get("amenities", [])
    if requested_amenities:
        parts.append("amenities: " + ", ".join(requested_amenities))

    city = intent.get("city")
    if city:
        parts.append(f"near or in: {city}")

    landmark = intent.get("near_landmark")
    if landmark:
        parts.append(f"near landmark: {landmark}")

    if not parts:
        return intent.get("query", "")

    return ". ".join(parts)
