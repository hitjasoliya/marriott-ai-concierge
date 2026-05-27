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


def _resolve_relative_date(text: str, today: date) -> Optional[str]:
    text_lower = text.lower()
    if "tomorrow" in text_lower:
        return (today + timedelta(days=1)).isoformat()
    if "next weekend" in text_lower:
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        return (today + timedelta(days=days_until_saturday)).isoformat()
    if "next friday" in text_lower:
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return (today + timedelta(days=days_until_friday)).isoformat()
    if "next monday" in text_lower:
        days_until = (0 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    if "next tuesday" in text_lower:
        days_until = (1 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    if "next wednesday" in text_lower:
        days_until = (2 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    if "next thursday" in text_lower:
        days_until = (3 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    if "next saturday" in text_lower:
        days_until = (5 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    if "next sunday" in text_lower:
        days_until = (6 - today.weekday()) % 7
        if days_until == 0:
            days_until = 7
        return (today + timedelta(days=days_until)).isoformat()
    return None


async def extract_intent(query: str) -> dict:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    prompt = INTENT_SYSTEM_PROMPT.format(
        today_date=today.isoformat(),
        tomorrow_date=tomorrow.isoformat(),
    )

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

    result.setdefault("guests", 2)
    result.setdefault("brand", "Marriott")
    result.setdefault("semantic_intent", [])
    result.setdefault("amenities", [])

    return result
