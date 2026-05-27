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
    vector_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"

    hotel_ids = [h.id for h in hotels]

    stmt = text(f"""
        SELECT id, 1 - (embedding <=> '{vector_literal}'::vector) AS similarity
        FROM hotels
        WHERE id = ANY(:ids)
        ORDER BY similarity DESC
    """)

    result = await session.execute(stmt, {
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
    """Build a natural-language query for embedding similarity search.

    Produces prose that matches the style of hotel semantic_text in the DB,
    so the BGE embedding model can compute meaningful cosine similarity.
    """
    descriptors: list[str] = []

    semantic_intent = intent.get("semantic_intent", [])
    if semantic_intent:
        descriptors.extend(semantic_intent)

    hotel_type = intent.get("hotel_type")
    if hotel_type:
        descriptors.append(hotel_type)

    requested_amenities = intent.get("amenities", [])
    if requested_amenities:
        descriptors.append(" with " + ", ".join(requested_amenities))

    # Build a natural-language sentence: "Luxury beachfront resort in Goa with pool, spa"
    phrase = " ".join(descriptors) if descriptors else "hotel"

    city = intent.get("city")
    landmark = intent.get("near_landmark")

    if city:
        phrase += f" in {city}"
    if landmark:
        phrase += f" near {landmark}"

    return phrase
