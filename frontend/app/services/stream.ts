import type { BookingRequest, BookingResponse, SearchResponse } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function search(query: string, guests: number): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    body: JSON.stringify({ query, guests }),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Search request failed");
  }

  return response.json();
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
