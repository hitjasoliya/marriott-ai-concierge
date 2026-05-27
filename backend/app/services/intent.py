import json
import os
import re
from datetime import date, timedelta
from typing import Optional

import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

INTENT_SYSTEM_PROMPT = """You are a hotel search intent extractor.
Extract structured JSON from the user's hotel search query.
Return ONLY valid JSON — no explanation, no markdown, no backticks.

Today's date is {today_date}.

Fields to extract:
{{
  "brand": "Marriott",
  "city": string or null,
  "near_landmark": string or null,
  "semantic_intent": array of strings from: [peaceful, luxury, romantic, family, business, workcation, budget, quiet, scenic, beachfront, airport],
  "amenities": array from: [wifi, spa, pool, gym, breakfast, parking, airport_shuttle, restaurant, bar],
  "hotel_type": one of: luxury / business / resort / budget / null,
  "budget_max_per_night": integer or null,
  "check_in": "YYYY-MM-DD" or null (resolve relative dates like "next weekend", "next Friday", "tomorrow" using {today_date} as reference),
  "check_out": "YYYY-MM-DD" or null,
  "guests": integer (default 2)
}}

For relative dates:
- "tomorrow" = {tomorrow_date}
- "next weekend" = the upcoming Saturday
- "next Friday" = the upcoming Friday
- "{today_date}" is today
"""


_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _resolve_weekday(text_lower: str, today: date, day_name: str, day_index: int) -> str | None:
    """Resolve 'this <day>' or 'next <day>' to a date."""
    this_pattern = f"this {day_name}"
    next_pattern = f"next {day_name}"

    if this_pattern in text_lower:
        days_until = (day_index - today.weekday()) % 7
        if days_until == 0:
            days_until = 7  # "this Friday" on Friday = next week
        return (today + timedelta(days=days_until)).isoformat()

    if next_pattern in text_lower:
        days_until = (day_index - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until + 7)).isoformat()

    return None


def _resolve_relative_date(text: str, today: date) -> str | None:
    """Resolve relative date expressions to YYYY-MM-DD. Returns None if no match."""
    text_lower = text.lower()

    if "today" in text_lower or "tonight" in text_lower:
        return today.isoformat()

    if "tomorrow" in text_lower:
        return (today + timedelta(days=1)).isoformat()

    if "day after tomorrow" in text_lower:
        return (today + timedelta(days=2)).isoformat()

    if "this weekend" in text_lower or "the weekend" in text_lower:
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        return (today + timedelta(days=days_until_saturday)).isoformat()

    if "next weekend" in text_lower:
        days_until_saturday = (5 - today.weekday()) % 7 + 7
        return (today + timedelta(days=days_until_saturday)).isoformat()

    for day_name, day_index in _WEEKDAYS.items():
        resolved = _resolve_weekday(text_lower, today, day_name, day_index)
        if resolved:
            return resolved

    return None


async def extract_intent(query: str, accumulated_intent: dict | None = None) -> dict:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    prompt = INTENT_SYSTEM_PROMPT.format(
        today_date=today.isoformat(),
        tomorrow_date=tomorrow.isoformat(),
    )

    if accumulated_intent:
        context_parts = []
        if accumulated_intent.get("city"):
            context_parts.append(f"City already established: {accumulated_intent['city']}")
        if accumulated_intent.get("hotel_type"):
            context_parts.append(f"Hotel type already established: {accumulated_intent['hotel_type']}")
        if accumulated_intent.get("amenities"):
            context_parts.append(f"Amenities already selected: {', '.join(accumulated_intent['amenities'])}")
        if accumulated_intent.get("semantic_intent"):
            context_parts.append(f"Vibe already established: {', '.join(accumulated_intent['semantic_intent'])}")
        if accumulated_intent.get("check_in"):
            context_parts.append(f"Check-in already set: {accumulated_intent['check_in']}")
        if accumulated_intent.get("check_out"):
            context_parts.append(f"Check-out already set: {accumulated_intent['check_out']}")
        if accumulated_intent.get("guests") and accumulated_intent["guests"] != 2:
            context_parts.append(f"Guests already set: {accumulated_intent['guests']}")
        if context_parts:
            prompt += "\n\nPrevious conversation context (use this to resolve ambiguous references):\n" + "\n".join(context_parts)

    model = genai.GenerativeModel("gemini-3.1-flash-lite")
    response = model.generate_content(f"{prompt}\n\nUser query: {query}")

    raw = response.text.strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    result = json.loads(raw)

    if not result.get("check_in"):
        result["check_in"] = _resolve_relative_date(query, today)
    if not result.get("check_out"):
        result["check_out"] = _resolve_relative_date(query, today)
        # If we resolved check_in but not check_out, default check_out to check_in + 1 day
        if not result["check_out"] and result["check_in"]:
            try:
                ci = date.fromisoformat(result["check_in"])
                result["check_out"] = (ci + timedelta(days=1)).isoformat()
            except (ValueError, TypeError):
                pass

    # B2: If both dates resolved to the same day via fallback, push check_out forward
    try:
        ci = result.get("check_in")
        co = result.get("check_out")
        if ci and co and date.fromisoformat(ci) >= date.fromisoformat(co):
            result["check_out"] = (date.fromisoformat(ci) + timedelta(days=1)).isoformat()
    except (ValueError, TypeError):
        pass

    result.setdefault("guests", 2)
    result.setdefault("brand", "Marriott")
    result.setdefault("semantic_intent", [])
    result.setdefault("amenities", [])

    return result
