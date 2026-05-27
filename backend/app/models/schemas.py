from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class HotelResponse(BaseModel):
    id: int
    name: str
    brand: str
    city: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    semantic_text: Optional[str] = None
    rating: Optional[float] = None
    amenities: Optional[dict] = None
    price_per_night: Optional[int] = None
    hotel_type: Optional[str] = None

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    guests: int = Field(default=2, ge=1)


class AvailabilityRequest(BaseModel):
    hotel_id: int
    check_in: date
    check_out: date
    guests: int = Field(default=2, ge=1)


class AvailabilityResponse(BaseModel):
    hotel_id: int
    available: bool
    rooms_left: int
    price_total: Optional[int] = None


class IntentResponse(BaseModel):
    brand: Optional[str] = None
    city: Optional[str] = None
    near_landmark: Optional[str] = None
    semantic_intent: list[str] = []
    amenities: list[str] = []
    hotel_type: Optional[str] = None
    budget_max_per_night: Optional[int] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    guests: int = 2


class SearchResultItem(BaseModel):
    hotel: HotelResponse
    score: float
    distance_km: Optional[float] = None
    available: bool = False
    price_total: Optional[int] = None


class BookingRequest(BaseModel):
    hotel_id: int
    guest_name: str
    email: str
    check_in: str
    check_out: str
    guests: int = Field(default=2, ge=1)


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    hotel_name: str
    hotel_city: str
    check_in: str
    check_out: str
    guests: int
    price_total: Optional[int] = None
    guest_name: str
