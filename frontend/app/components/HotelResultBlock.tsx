"use client";

import { useState } from "react";
import type { SearchResultItem, IntentData } from "../types";
import { createBooking } from "../services/stream";
import type { BookingResponse } from "../types";

interface Props {
  hotel: SearchResultItem;
  intent?: IntentData | null;
}

const amenityLabels: Record<string, string> = {
  wifi: "WiFi",
  spa: "Spa",
  pool: "Pool",
  gym: "Gym",
  breakfast: "Breakfast",
  parking: "Parking",
  airport_shuttle: "Airport shuttle",
  restaurant: "Restaurant",
  bar: "Bar",
  beach_access: "Beach access",
  private_beach: "Private beach",
  kids_club: "Kids club",
  business_center: "Business center",
  rooftop_pool: "Rooftop pool",
  butler_service: "Butler service",
  yoga_deck: "Yoga deck",
  dj: "DJ",
};

const typeColors: Record<string, string> = {
  luxury: "bg-amber-50 border-amber-400",
  business: "bg-blue-50 border-blue-400",
  resort: "bg-emerald-50 border-emerald-400",
  budget: "bg-gray-50 border-gray-300",
};

export default function HotelResultBlock({ hotel, intent }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [bookingError, setBookingError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    guest_name: "",
    email: "",
    check_in: intent?.check_in || "",
    check_out: intent?.check_out || "",
    guests: intent?.guests || 2,
  });

  const borderClass = typeColors[hotel.hotel_type || "budget"] || typeColors.budget;

  const allAmenities = hotel.amenities
    ? Object.keys(hotel.amenities).filter((k) => hotel.amenities![k] && amenityLabels[k])
    : [];

  const topAmenities = allAmenities.slice(0, 4);
  const remainingAmenities = allAmenities.slice(4);

  const handleBook = async () => {
    if (!form.guest_name.trim() || !form.email.trim() || !form.check_in || !form.check_out) {
      setBookingError("Please fill in all fields.");
      return;
    }
    setBookingError("");
    setSubmitting(true);
    try {
      const result = await createBooking({
        hotel_id: hotel.id,
        guest_name: form.guest_name,
        email: form.email,
        check_in: form.check_in,
        check_out: form.check_out,
        guests: form.guests,
      });
      setBooking(result);
    } catch {
      setBookingError("Booking failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className={`border-l-2 rounded-lg p-4 text-sm cursor-pointer transition-shadow hover:shadow-md ${borderClass}`}
      onClick={() => {
        if (!expanded) setExpanded(true);
      }}
    >
      {/* Header — always visible */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-gray-900 text-base">{hotel.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {hotel.city}
            {hotel.distance_km != null && <span> · {hotel.distance_km} km</span>}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-xs text-gray-400">⭐ {hotel.rating}</div>
          {hotel.price_per_night && (
            <div className="font-semibold text-gray-900 text-sm">
              &#8377;{hotel.price_per_night.toLocaleString()}
              <span className="text-xs text-gray-400 font-normal">/night</span>
            </div>
          )}
        </div>
      </div>

      {/* Badges — always visible */}
      <div className="flex flex-wrap gap-1.5 mt-2">
        {hotel.available ? (
          <span className="text-[11px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
            {hotel.rooms_left} rooms
          </span>
        ) : (
          <span className="text-[11px] text-red-600 bg-red-50 px-1.5 py-0.5 rounded">
            Limited
          </span>
        )}
        {topAmenities.map((key) => (
          <span key={key} className="text-[11px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
            {amenityLabels[key] || key}
          </span>
        ))}
        {remainingAmenities.length > 0 && !expanded && (
          <span className="text-[11px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">
            +{remainingAmenities.length} more
          </span>
        )}
      </div>

      {/* Snippet — always visible */}
      {hotel.semantic_text && !expanded && (
        <p className="text-xs text-gray-500 mt-2 line-clamp-2 italic">
          &ldquo;{hotel.semantic_text.slice(0, 150)}&rdquo;
        </p>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
          {hotel.description && (
            <p className="text-xs text-gray-600">{hotel.description}</p>
          )}

          {hotel.semantic_text && (
            <p className="text-xs text-gray-500 italic">
              &ldquo;{hotel.semantic_text}&rdquo;
            </p>
          )}

          {/* All amenities */}
          {allAmenities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {allAmenities.map((key) => (
                <span key={key} className="text-[11px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                  {amenityLabels[key] || key}
                </span>
              ))}
            </div>
          )}

          {/* Meta row */}
          <div className="flex flex-wrap gap-2 text-[11px] text-gray-400">
            {hotel.brand && <span className="bg-gray-50 px-1.5 py-0.5 rounded">{hotel.brand}</span>}
            {hotel.hotel_type && <span className="bg-gray-50 px-1.5 py-0.5 rounded capitalize">{hotel.hotel_type}</span>}
            <span className="bg-gray-50 px-1.5 py-0.5 rounded">Match: {(hotel.score * 100).toFixed(0)}%</span>
          </div>

          {/* Booking section */}
          {booking ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded uppercase">
                  {booking.status}
                </span>
                <span className="text-xs text-emerald-700 font-medium">Booking #{booking.booking_id}</span>
              </div>
              <div className="mt-1.5 text-xs text-emerald-600 space-y-0.5">
                <p>{booking.hotel_name}, {booking.hotel_city}</p>
                <p>{booking.check_in} → {booking.check_out} · {booking.guests} guest{booking.guests > 1 ? "s" : ""}</p>
                {booking.price_total && (
                  <p className="font-semibold">Total: &#8377;{booking.price_total.toLocaleString()}</p>
                )}
              </div>
            </div>
          ) : showBookingForm ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-gray-500">Name</label>
                  <input
                    className="w-full text-xs border border-gray-200 rounded px-2 py-1 mt-0.5"
                    placeholder="Your name"
                    value={form.guest_name}
                    onChange={(e) => setForm({ ...form, guest_name: e.target.value })}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-500">Email</label>
                  <input
                    className="w-full text-xs border border-gray-200 rounded px-2 py-1 mt-0.5"
                    placeholder="you@email.com"
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-500">Check-in</label>
                  <input
                    className="w-full text-xs border border-gray-200 rounded px-2 py-1 mt-0.5"
                    type="date"
                    value={form.check_in}
                    onChange={(e) => setForm({ ...form, check_in: e.target.value })}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-500">Check-out</label>
                  <input
                    className="w-full text-xs border border-gray-200 rounded px-2 py-1 mt-0.5"
                    type="date"
                    value={form.check_out}
                    onChange={(e) => setForm({ ...form, check_out: e.target.value })}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              </div>
              <div>
                <label className="text-[11px] text-gray-500">Guests</label>
                <input
                  className="w-20 text-xs border border-gray-200 rounded px-2 py-1 mt-0.5 block"
                  type="number"
                  min={1}
                  value={form.guests}
                  onChange={(e) => setForm({ ...form, guests: parseInt(e.target.value) || 1 })}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              {bookingError && <p className="text-[11px] text-red-500">{bookingError}</p>}
              <div className="flex gap-2">
                <button
                  className="text-[11px] bg-gray-900 text-white px-3 py-1 rounded font-medium disabled:opacity-50"
                  onClick={(e) => { e.stopPropagation(); handleBook(); }}
                  disabled={submitting}
                >
                  {submitting ? "Booking..." : "Confirm Booking"}
                </button>
                <button
                  className="text-[11px] text-gray-500 px-3 py-1 rounded"
                  onClick={(e) => { e.stopPropagation(); setShowBookingForm(false); setBookingError(""); }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              className="text-[11px] bg-gray-900 text-white px-3 py-1 rounded font-medium"
              onClick={(e) => { e.stopPropagation(); setShowBookingForm(true); }}
            >
              Book Now
            </button>
          )}

          {/* Collapse button */}
          <button
            className="text-[11px] text-gray-400 hover:text-gray-600"
            onClick={(e) => { e.stopPropagation(); setExpanded(false); setShowBookingForm(false); }}
          >
            Show less
          </button>
        </div>
      )}

      {/* Expand hint — only when collapsed */}
      {!expanded && (
        <p className="text-[11px] text-gray-400 mt-2">Click for details</p>
      )}
    </div>
  );
}
