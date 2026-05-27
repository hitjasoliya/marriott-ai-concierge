import asyncio
import os
import time
from typing import Optional

import httpx

NOMINATIM_EMAIL = os.environ.get("NOMINATIM_EMAIL", "user@example.com")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

_last_request_time = 0.0
_lock = asyncio.Lock()


async def resolve_landmark(landmark: str) -> Optional[tuple[float, float]]:
    global _last_request_time

    async with _lock:
        elapsed = time.monotonic() - _last_request_time
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _last_request_time = time.monotonic()

    headers = {
        "User-Agent": f"MarriottAIConcierge/1.0 ({NOMINATIM_EMAIL})",
    }
    params = {
        "q": landmark,
        "format": "json",
        "limit": 1,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            print(f"Nominatim resolution failed for '{landmark}': {e}")

    return None


def get_city_coordinates(city: str) -> Optional[tuple[float, float]]:
    coords = {
        "mumbai": (19.0760, 72.8777),
        "delhi": (28.6139, 77.2090),
        "agra": (27.1751, 78.0421),
        "goa": (15.5140, 73.7633),
        "bangalore": (12.9716, 77.5946),
        "jaipur": (26.9124, 75.7873),
        "dubai": (25.2048, 55.2708),
        "singapore": (1.3521, 103.8198),
        "london": (51.5074, -0.1278),
        "new york": (40.7128, -74.0060),
    }
    return coords.get(city.lower())
