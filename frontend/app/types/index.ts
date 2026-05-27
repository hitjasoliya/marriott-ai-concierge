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

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  hotels?: SearchResultItem[];
  intent?: IntentData;
  isStreaming?: boolean;
}

export interface SSEEvent {
  type: "intent" | "hotels" | "token" | "done" | "status" | "error";
  data?: unknown;
  message?: string;
}
