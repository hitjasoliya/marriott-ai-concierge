import asyncio
import json
import os
from datetime import date
from typing import AsyncGenerator

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db.models import Hotel
from app.db.session import get_db
from app.models.schemas import (
    AvailabilityRequest, AvailabilityResponse, HotelResponse,
    IntentResponse, SearchRequest, SearchResultItem,
)
from app.services.intent import extract_intent
from app.services.geo import resolve_landmark, get_city_coordinates
from app.retrieval.sql_retrieval import retrieve_by_filters
from app.retrieval.geo_retrieval import retrieve_by_radius
from app.retrieval.reranker import rerank_by_semantic_similarity, build_query_semantic_text
from app.ranking.engine import rank_hotels
from app.availability.mock_api import check_availability

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

router = APIRouter()


@router.post("/search")
async def search(request: SearchRequest):
    async def event_stream() -> AsyncGenerator[dict, None]:
        yield {"event": "status", "data": json.dumps({"type": "start", "message": "Extracting search intent..."})}

        try:
            intent = await extract_intent(request.query)
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Intent extraction failed: {str(e)}"})}
            return

        yield {"event": "intent", "data": json.dumps({"type": "intent", "data": intent})}

        ref_point = None
        if intent.get("near_landmark"):
            yield {"event": "status", "data": json.dumps({"type": "status", "message": f"Resolving landmark: {intent['near_landmark']}..."})}
            ref_point = await resolve_landmark(intent["near_landmark"])

        if ref_point is None and intent.get("city"):
            ref_point = get_city_coordinates(intent["city"])

        yield {"event": "status", "data": json.dumps({"type": "status", "message": "Searching hotels..."})}

        from app.db.session import async_session
        async with async_session() as session:
            hotels = await retrieve_by_filters(
                session,
                city=intent.get("city"),
                hotel_type=intent.get("hotel_type"),
                budget_max=intent.get("budget_max_per_night"),
                amenities=intent.get("amenities"),
                limit=50,
            )

            distance_map: dict[int, float] = {}
            if ref_point and hotels:
                lat, lon = ref_point
                geo_results = await retrieve_by_radius(session, lat, lon, radius_km=50.0, limit=50)
                geo_hotel_ids = {h.id for h, _ in geo_results}
                hotels = [h for h in hotels if h.id in geo_hotel_ids]
                distance_map = {h.id: d for h, d in geo_results}

            if not hotels:
                yield {"event": "hotels", "data": json.dumps({"type": "hotels", "data": []})}
                yield {"event": "token", "data": json.dumps({"type": "token", "data": "I couldn't find any Marriott hotels matching your criteria. Try broadening your search — for example, remove the city filter or adjust your budget."})}
                yield {"event": "done", "data": json.dumps({"type": "done"})}
                return

            query_text = build_query_semantic_text(intent)
            if not query_text:
                query_text = request.query

            scored = await rerank_by_semantic_similarity(session, query_text, hotels)
            top_candidates = scored[:20]

            available_ids = set()
            availability_data = {}
            check_in = intent.get("check_in")
            check_out = intent.get("check_out")
            if check_in and check_out:
                for hotel, _ in top_candidates:
                    avail = check_availability(hotel.id, check_in, check_out, hotel.price_per_night or 0)
                    if avail["available"]:
                        available_ids.add(hotel.id)
                    availability_data[hotel.id] = avail
            else:
                available_ids = {h.id for h, _ in top_candidates}

            rankings = rank_hotels(scored, distance_map, available_ids)
            top_5 = rankings[:5]

            top_hotel_ids = [r.hotel_id for r in top_5]
            hotel_map = {h.id: h for h, _ in scored}

            results = []
            for rank in top_5:
                h = hotel_map[rank.hotel_id]
                avail = availability_data.get(h.id, {"available": True, "rooms_left": 3, "price_total": None})
                results.append({
                    "id": h.id,
                    "name": h.name,
                    "brand": h.brand,
                    "city": h.city,
                    "description": h.description,
                    "semantic_text": h.semantic_text,
                    "rating": h.rating,
                    "amenities": h.amenities,
                    "price_per_night": h.price_per_night,
                    "hotel_type": h.hotel_type,
                    "score": round(rank.final_score, 4),
                    "distance_km": round(rank.distance_km, 1) if rank.distance_km < 999 else None,
                    "available": avail.get("available", rank.available),
                    "rooms_left": avail.get("rooms_left", 0),
                    "price_total": avail.get("price_total"),
                })

            yield {"event": "hotels", "data": json.dumps({"type": "hotels", "data": results})}

            hotel_context = "\n".join([
                f"- {r['name']} in {r['city']}: {r['semantic_text'][:200]}... Rating: {r['rating']}, "
                f"Price: INR {r['price_per_night']}/night, "
                f"{'Available' if r['available'] else 'Limited availability'}"
                for r in results
            ])

            system_prompt = (
                "You are a helpful, knowledgeable Marriott hotel concierge. "
                "You help guests find the perfect Marriott property for their needs. "
                "Be warm, conversational, and specific. Mention hotel names, unique features, "
                "and why each hotel fits the guest's preferences. "
                "Keep responses concise — 2-3 sentences per hotel recommendation. "
                "Never make up details not in the hotel data provided."
            )

            user_prompt = (
                f"Guest query: {request.query}\n\n"
                f"Intent extracted: {json.dumps(intent)}\n\n"
                f"Top matching hotels:\n{hotel_context}\n\n"
                f"Write a warm, helpful response recommending these hotels to the guest. "
                f"Mention specific hotel names, atmosphere, standout amenities, and why each matches their query."
            )

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield {"event": "token", "data": json.dumps({"type": "token", "data": chunk.text})}
                    await asyncio.sleep(0)

        yield {"event": "done", "data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_stream())


@router.get("/hotel/{hotel_id}", response_model=HotelResponse)
async def get_hotel(hotel_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        text("SELECT * FROM hotels WHERE id = :id"), {"id": hotel_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return HotelResponse(
        id=row.id, name=row.name, brand=row.brand, city=row.city,
        latitude=row.latitude, longitude=row.longitude,
        description=row.description, semantic_text=row.semantic_text,
        rating=row.rating, amenities=row.amenities,
        price_per_night=row.price_per_night, hotel_type=row.hotel_type,
    )


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    hotel_id: int = Query(...),
    check_in: str = Query(...),
    check_out: str = Query(...),
    guests: int = Query(default=2, ge=1),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        text("SELECT price_per_night FROM hotels WHERE id = :id"), {"id": hotel_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hotel not found")

    avail = check_availability(hotel_id, check_in, check_out, row.price_per_night or 0)
    return AvailabilityResponse(
        hotel_id=avail["hotel_id"],
        available=avail["available"],
        rooms_left=avail["rooms_left"],
        price_total=avail["price_total"],
    )


@router.post("/seed-hotels")
async def seed_hotels():
    import subprocess
    subprocess.Popen(["python", "-m", "app.seed.seeder"])
    return {"status": "seeding started"}


@router.post("/embed-hotels")
async def embed_hotels():
    import subprocess
    subprocess.Popen(["python", "-m", "app.embeddings.pipeline"])
    return {"status": "embedding started"}
