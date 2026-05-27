const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHotel(id: number) {
  const res = await fetch(`${API_BASE}/hotel/${id}`);
  if (!res.ok) throw new Error("Hotel not found");
  return res.json();
}

export async function checkAvailability(hotelId: number, checkIn: string, checkOut: string, guests: number) {
  const params = new URLSearchParams({ hotel_id: String(hotelId), check_in: checkIn, check_out: checkOut, guests: String(guests) });
  const res = await fetch(`${API_BASE}/availability?${params}`);
  if (!res.ok) throw new Error("Availability check failed");
  return res.json();
}
