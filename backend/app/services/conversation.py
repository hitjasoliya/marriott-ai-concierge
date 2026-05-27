import json
import os
import re
from datetime import date, timedelta
from typing import Optional

import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

# In-memory conversation store: session_id -> dict with turns + accumulated_intent
_sessions: dict[str, dict] = {}

SCALAR_INTENT_FIELDS = [
    "brand", "city", "near_landmark", "hotel_type",
    "budget_max_per_night", "check_in", "check_out", "guests",
]
LIST_INTENT_FIELDS = ["semantic_intent", "amenities"]

KNOWN_CITY_AREAS: dict[str, list[str]] = {
    "mumbai": ["Juhu", "Bandra", "South Mumbai / Colaba", "Near the airport"],
    "delhi": ["Connaught Place", "Aerocity", "South Delhi", "Gurgaon"],
    "goa": ["Candolim", "Baga", "Palolem", "Anjuna"],
    "bangalore": ["Koramangala", "Whitefield", "MG Road", "Indiranagar"],
    "jaipur": ["Near City Palace", "Amer", "C-Scheme", "Near the airport"],
    "dubai": ["Marina", "Downtown", "Palm Jumeirah", "Deira"],
    "singapore": ["Marina Bay", "Orchard Road", "Sentosa", "Chinatown"],
    "london": ["Mayfair", "Canary Wharf", "West End", "Kensington"],
    "new york": ["Midtown Manhattan", "Times Square", "Financial District", "Central Park South"],
}

GAP_ANALYSIS_PROMPT = """You are a warm, helpful Marriott hotel concierge having a conversation with a guest.

The guest just said: "{query}"

What we've understood so far across the entire conversation:
{accumulated_summary}

From this latest message, we specifically extracted:
{current_summary}

We are still missing these details: {missing_list}

Your job:
1. Write a warm reply with a brief 1-line confirmation of what you understood, followed by a bulleted list of questions asking about the missing details. Format the questions like:
   - A short intro line confirming what was understood
   - • Question about first missing detail?
   - • Question about second missing detail?
   - If "guests" is in the missing list, ask: "• How many guests will be staying?"
   - If dates are missing, include: "• Or I can show you options without specific dates if you prefer"
   - If the city has well-known neighborhoods, add a question narrowing the area
   - Keep each bullet concise (one line)

2. Generate 2-4 suggested quick-reply chips the guest could tap. Examples:
   - Missing dates: "This weekend", "Next week", "Explore without dates"
   - Missing city: "Mumbai", "Delhi", "Goa", "Dubai"
   - Missing location specificity: "Juhu area", "Bandra", "Near the airport"
   - Missing guests: "Just 2 guests", "Family of 4", "Solo trip"

Return ONLY valid JSON (no markdown, no backticks, no explanation):
{{
  "needs_follow_up": true,
  "reply": "...",
  "suggestions": ["...", "..."],
  "missing_fields": ["...", "..."],
  "confirmed_fields": {{}}
}}"""


def _make_accumulated_summary(accumulated: dict, include_guests: bool = False) -> str:
    parts = []
    if accumulated.get("city"):
        parts.append(f"City: {accumulated['city']}")
    if accumulated.get("near_landmark"):
        parts.append(f"Near: {accumulated['near_landmark']}")
    if accumulated.get("hotel_type"):
        parts.append(f"Hotel type: {accumulated['hotel_type']}")
    if accumulated.get("semantic_intent"):
        parts.append(f"Vibe: {', '.join(accumulated['semantic_intent'])}")
    if accumulated.get("amenities"):
        parts.append(f"Amenities wanted: {', '.join(accumulated['amenities'])}")
    if accumulated.get("budget_max_per_night"):
        parts.append(f"Max budget: INR {accumulated['budget_max_per_night']}/night")
    if accumulated.get("check_in"):
        parts.append(f"Check-in: {accumulated['check_in']}")
    if accumulated.get("check_out"):
        parts.append(f"Check-out: {accumulated['check_out']}")
    if include_guests and accumulated.get("guests", 2) != 2:
        parts.append(f"Guests: {accumulated['guests']} (confirmed)")
    return "\n".join(parts) if parts else "(nothing established yet)"


def _make_current_summary(intent: dict) -> str:
    return _make_accumulated_summary(intent, include_guests=False)


_GUEST_REGEX = (
    r'\b(\d+)\s*(guest|people|person|adult|traveller|traveler)s?\b|'
    r'\b(solo|myself|just\s+me|alone|single)\b|'
    r'\b(couple|pair|duo)\b'
)


def _query_mentions_guests(query: str) -> bool:
    import re
    return bool(re.search(_GUEST_REGEX, query.lower()))


def _merge_intent(existing: dict, new: dict) -> dict:
    merged = dict(existing)
    for field in SCALAR_INTENT_FIELDS:
        new_val = new.get(field)
        if new_val is not None:
            if field == "guests" and new_val == 2 and existing.get("guests", 2) != 2:
                continue  # don't overwrite explicit guest count with default
            merged[field] = new_val
    for field in LIST_INTENT_FIELDS:
        existing_list = set(merged.get(field, []))
        new_list = set(new.get(field, []))
        merged[field] = sorted(existing_list | new_list)
    # Preserve or apply confirmation flags from either side
    for flag in ("_guests_confirmed",):
        if existing.get(flag) or new.get(flag):
            merged[flag] = True
    return merged


def identify_missing_fields(intent: dict, query: str = "") -> list[str]:
    missing = []
    if not intent.get("city") and not intent.get("near_landmark"):
        missing.append("city")
    if not intent.get("check_in"):
        missing.append("check_in")
    if not intent.get("check_out"):
        missing.append("check_out")
    # Only flag guests if still at default (2) and never explicitly confirmed
    if intent.get("guests", 2) == 2 and not intent.get("_guests_confirmed"):
        if not _query_mentions_guests(query):
            missing.append("guests")
    return missing


def get_or_create_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "session_id": session_id,
            "turns": [],
            "accumulated_intent": {"guests": 2, "brand": "Marriott", "semantic_intent": [], "amenities": [], "_guests_confirmed": False},
            "created_at": date.today().isoformat(),
        }
    return _sessions[session_id]


def add_turn(session_id: str, role: str, content: str, intent: dict | None) -> None:
    session = get_or_create_session(session_id)
    session["turns"].append({
        "role": role,
        "content": content,
        "intent": intent,
        "timestamp": date.today().isoformat(),
    })
    if intent and role == "user":
        # Track whether guests was ever explicitly mentioned across the conversation
        if _query_mentions_guests(content):
            intent["_guests_confirmed"] = True
        session["accumulated_intent"] = _merge_intent(session["accumulated_intent"], intent)


async def generate_follow_up(
    intent: dict, missing_fields: list[str], query: str, accumulated_intent: dict
) -> dict:
    accumulated_summary = _make_accumulated_summary(accumulated_intent, include_guests=False)
    current_summary = _make_current_summary(intent)
    missing_list = ", ".join(missing_fields)

    today = date.today()
    next_saturday = today + timedelta(days=(5 - today.weekday()) % 7)
    if (5 - today.weekday()) % 7 == 0:
        next_saturday += timedelta(days=7)

    prompt = GAP_ANALYSIS_PROMPT.format(
        query=query,
        accumulated_summary=accumulated_summary,
        current_summary=current_summary,
        missing_list=missing_list,
    )

    city = (accumulated_intent.get("city") or intent.get("city") or "").lower()
    if city in KNOWN_CITY_AREAS:
        areas = KNOWN_CITY_AREAS[city]
        prompt += f"\n\nThe guest is searching in {city.title()}. Popular areas here include: {', '.join(areas)}. If location specificity is missing, suggest 2-3 of these areas as quick-reply chips."

    prompt += f"\n\nToday is {today.isoformat()}. Next Saturday is {next_saturday.isoformat()}."

    model = genai.GenerativeModel("gemini-3.1-flash-lite")
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "needs_follow_up": True,
            "reply": "Let me help you find the perfect Marriott stay. Could you tell me a bit more about when you'd like to travel and any preferences you have?",
            "suggestions": ["This weekend", "Next week", "Explore without dates"],
            "missing_fields": missing_fields,
            "confirmed_fields": {},
        }

    # B8: Don't let the LLM bypass gap detection
    if missing_fields:
        result["needs_follow_up"] = True

    # B9: Normalize missing_fields to a list
    if not isinstance(result.get("missing_fields"), list):
        result["missing_fields"] = missing_fields

    # Normalize suggestions to a list
    if not isinstance(result.get("suggestions"), list):
        result["suggestions"] = []

    return result


AMENITY_SUGGESTIONS_BY_TYPE: dict[str, list[str]] = {
    "luxury": ["spa", "pool", "restaurant", "bar"],
    "business": ["wifi", "gym", "business_center", "airport_shuttle"],
    "resort": ["spa", "pool", "beach_access", "restaurant"],
    "budget": ["wifi", "breakfast", "parking", "gym"],
}


def get_default_amenity_suggestions(intent: dict) -> list[str]:
    hotel_type = intent.get("hotel_type", "")
    if hotel_type in AMENITY_SUGGESTIONS_BY_TYPE:
        return AMENITY_SUGGESTIONS_BY_TYPE[hotel_type]
    return ["wifi", "pool", "spa", "breakfast"]


async def generate_suggestions_for_results(intent: dict, hotels: list[dict]) -> list[str]:
    suggestions = []
    if hotels:
        suggestions.append(f"Book {hotels[0]['name']}")
        if len(hotels) > 3:
            suggestions.append("Show me more options")
    if intent.get("amenities"):
        suggestions.append("Filter by different amenities")
    if not intent.get("check_in"):
        suggestions.append("Check availability for this weekend")
    if len(suggestions) < 3:
        suggestions.append("Search in a different area")
    return suggestions[:4]
