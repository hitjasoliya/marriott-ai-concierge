import json
import os
import random
import string

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Hotel
from app.db.session import get_db
from app.models.schemas import (
    AvailabilityRequest, AvailabilityResponse, BookingRequest, BookingResponse,
    HotelResponse, IntentResponse, SearchRequest, SearchResultItem,
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

CHAT_SYSTEM_PROMPT = (
    "You are a helpful, knowledgeable Marriott hotel concierge. "
    "You help guests find the perfect Marriott property for their needs. "
    "Answer casual greetings and questions warmly and briefly. "
    "When hotel recommendations are provided, mention specific hotel names, "
    "unique features, and why each fits the guest's preferences. "
    "Keep responses concise. Never make up details."
)


def _has_hotel_search_intent(intent: dict) -> bool:
    return bool(
        intent.get("city")
        or intent.get("near_landmark")
        or intent.get("semantic_intent")
        or intent.get("amenities")
        or intent.get("hotel_type")
        or intent.get("budget_max_per_night")
    )


def _generate_gemini_response(system_prompt: str, user_prompt: str) -> str:
    model = genai.GenerativeModel("gemini-3.1-flash-lite")
    response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
    return response.text or ""


@router.post("/search")
async def search(request: SearchRequest):
    try:
        intent = await extract_intent(request.query)
    except Exception as e:
        return {"error": f"Intent extraction failed: {str(e)}", "intent": None, "hotels": [], "reply": ""}

    if not _has_hotel_search_intent(intent):
        reply = _generate_gemini_response(
            CHAT_SYSTEM_PROMPT,
            f"Guest says: {request.query}\n\n"
            f"Respond warmly and briefly. Introduce yourself as the Marriott AI Concierge "
            f"if this is a greeting. Keep it to 1-2 sentences and invite them to describe "
            f"what kind of hotel they're looking for."
        )
        return {"intent": intent, "hotels": [], "reply": reply}

    ref_point = None
    if intent.get("near_landmark"):
        ref_point = await resolve_landmark(intent["near_landmark"])

    if ref_point is None and intent.get("city"):
        ref_point = get_city_coordinates(intent["city"])

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
            geo_results = await retrieve_by_radius(session, lat, lon, radius_km=100.0, limit=50)
            geo_hotel_ids = {h.id for h, _ in geo_results}
            hotels = [h for h in hotels if h.id in geo_hotel_ids]
            distance_map = {h.id: d for h, d in geo_results}

        if not hotels:
            reply = _generate_gemini_response(
                CHAT_SYSTEM_PROMPT,
                f"Guest query: {request.query}\n\n"
                f"No hotels matched. Ask them to broaden their search — "
                f"try a different city, remove filters, or describe the vibe they want."
            )
            return {"intent": intent, "hotels": [], "reply": reply}

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

        hotel_map = {h.id: h for h, _ in scored}

        results = []
        for rank in rankings:
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

        hotel_context = "\n".join([
            f"- {r['name']} in {r['city']}: {r['semantic_text'][:200]}... Rating: {r['rating']}, "
            f"Price: INR {r['price_per_night']}/night, "
            f"{'Available' if r['available'] else 'Limited availability'}"
            for r in results[:5]
        ])

        reply = _generate_gemini_response(
            CHAT_SYSTEM_PROMPT,
            f"Guest query: {request.query}\n\n"
            f"Intent extracted: {json.dumps(intent)}\n\n"
            f"Top matching hotels:\n{hotel_context}\n\n"
            f"Write a warm, helpful response recommending these hotels to the guest. "
            f"Mention specific hotel names, atmosphere, standout amenities, and why each matches their query."
        )

    return {"intent": intent, "hotels": results, "reply": reply}


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


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(request: BookingRequest, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        text("SELECT name, city, price_per_night FROM hotels WHERE id = :id"),
        {"id": request.hotel_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel_name, hotel_city, price_per_night = row

    avail = check_availability(request.hotel_id, request.check_in, request.check_out, price_per_night or 0)

    booking_id = "MB" + "".join(random.choices(string.digits, k=4))

    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        hotel_name=hotel_name,
        hotel_city=hotel_city,
        check_in=request.check_in,
        check_out=request.check_out,
        guests=request.guests,
        price_total=avail["price_total"],
        guest_name=request.guest_name,
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
