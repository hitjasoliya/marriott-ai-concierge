export interface Hotel {
  id: number;
  name: string;
  brand: string;
  city: string;
  description: string | null;
  semantic_text: string | null;
  rating: number | null;
  amenities: Record<string, boolean> | null;
  price_per_night: number | null;
  hotel_type: string | null;
}

export interface SearchResultItem {
  id: number;
  name: string;
  brand: string;
  city: string;
  description: string | null;
  semantic_text: string | null;
  rating: number | null;
  amenities: Record<string, boolean> | null;
  price_per_night: number | null;
  hotel_type: string | null;
  score: number;
  distance_km: number | null;
  available: boolean;
  rooms_left: number;
  price_total: number | null;
}

export interface IntentData {
  brand: string | null;
  city: string | null;
  near_landmark: string | null;
  semantic_intent: string[];
  amenities: string[];
  hotel_type: string | null;
  budget_max_per_night: number | null;
  check_in: string | null;
  check_out: string | null;
  guests: number;
}

export interface SearchResponse {
  intent: IntentData | null;
  hotels: SearchResultItem[];
  reply: string;
  error?: string;
}

export interface BookingRequest {
  hotel_id: number;
  guest_name: string;
  email: string;
  check_in: string;
  check_out: string;
  guests: number;
}

export interface BookingResponse {
  booking_id: string;
  status: string;
  hotel_name: string;
  hotel_city: string;
  check_in: string;
  check_out: string;
  guests: number;
  price_total: number | null;
  guest_name: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  hotels?: SearchResultItem[];
  intent?: IntentData | null;
}
