import json
import os
from dataclasses import dataclass, field

DEFAULT_WEIGHTS = {
    "semantic": 0.45,
    "distance": 0.25,
    "rating": 0.20,
    "availability": 0.10,
}


def _get_weights() -> dict:
    raw = os.environ.get("RANKING_WEIGHTS_JSON", "")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return DEFAULT_WEIGHTS


@dataclass
class HotelScore:
    hotel_id: int
    semantic_similarity: float = 0.0
    distance_km: float = 999.0
    max_distance_km: float = 1.0
    rating: float = 3.0
    available: bool = False
    final_score: float = 0.0

    def compute_final(self) -> float:
        w = _get_weights()

        distance_score = 1 - (self.distance_km / self.max_distance_km) if self.max_distance_km > 0 else 1.0
        distance_score = max(0.0, min(1.0, distance_score))

        rating_score = self.rating / 5.0
        availability_score = 1.0 if self.available else 0.4

        self.final_score = (
            w["semantic"] * self.semantic_similarity
            + w["distance"] * distance_score
            + w["rating"] * rating_score
            + w["availability"] * availability_score
        )
        return self.final_score


def compute_final_score(
    semantic_similarity: float,
    distance_km: float,
    max_distance_km: float,
    rating: float,
    available: bool,
) -> float:
    hs = HotelScore(
        hotel_id=0,
        semantic_similarity=semantic_similarity,
        distance_km=distance_km,
        max_distance_km=max_distance_km,
        rating=rating,
        available=available,
    )
    return hs.compute_final()


def rank_hotels(
    semantic_scored: list[tuple],
    distance_map: dict[int, float],
    available_hotel_ids: set[int],
) -> list[HotelScore]:
    if not semantic_scored:
        return []

    distances = [d for d in distance_map.values() if d < 999]
    max_dist = max(distances) if distances else 1.0

    results = []
    for hotel, sim in semantic_scored:
        hs = HotelScore(
            hotel_id=hotel.id,
            semantic_similarity=sim,
            distance_km=distance_map.get(hotel.id, 999.0),
            max_distance_km=max_dist,
            rating=hotel.rating or 3.0,
            available=hotel.id in available_hotel_ids,
        )
        hs.compute_final()
        results.append(hs)

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results
