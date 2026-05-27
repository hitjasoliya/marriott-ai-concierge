import hashlib
import random
from datetime import date


def check_availability(hotel_id: int, check_in: str, check_out: str, base_price: int = 0) -> dict:
    seed = int(hashlib.md5(f"{hotel_id}{check_in}{check_out}".encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    available = rng.random() > 0.28
    rooms_left = rng.randint(1, 8) if available else 0
    surge = 1 + rng.uniform(0, 0.35)

    nights = 1
    try:
        ci = date.fromisoformat(check_in)
        co = date.fromisoformat(check_out)
        nights = (co - ci).days
        if nights < 1:
            nights = 1
    except (ValueError, TypeError):
        pass

    return {
        "hotel_id": hotel_id,
        "available": available,
        "rooms_left": rooms_left,
        "price_total": int(base_price * nights * surge) if available and base_price > 0 else None,
    }
