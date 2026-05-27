import type { BookingRequest, BookingResponse, SearchResponse } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function search(
  query: string,
  guests: number,
  sessionId?: string,
  selectedAmenities?: string[],
  exploreWithoutDates?: boolean,
): Promise<SearchResponse> {
  const body: Record<string, unknown> = { query, guests };
  if (sessionId) body.session_id = sessionId;
  if (selectedAmenities?.length) body.selected_amenities = selectedAmenities;
  if (exploreWithoutDates) body.explore_without_dates = true;

  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Search request failed");
  }

  const data = await response.json();

  // Map backend snake_case to frontend camelCase
  return {
    ...data,
    suggestedAmenities: data.suggested_amenities ?? data.suggestedAmenities ?? [],
    missingFields: data.missing_fields ?? data.missingFields ?? [],
    accumulatedIntent: data.accumulated_intent ?? data.accumulatedIntent ?? null,
    sessionId: data.session_id ?? data.sessionId ?? null,
  };
}

export async function createBooking(data: BookingRequest): Promise<BookingResponse> {
  const response = await fetch(`${API_BASE}/bookings`, {
    method: "POST",
    body: JSON.stringify(data),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Booking request failed");
  }

  return response.json();
}
