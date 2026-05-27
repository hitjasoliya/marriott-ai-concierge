"use client";

import type { SearchResultItem } from "../types";

interface Props {
  hotel: SearchResultItem;
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
};

const typeColors: Record<string, string> = {
  luxury: "bg-amber-50 border-amber-400",
  business: "bg-blue-50 border-blue-400",
  resort: "bg-emerald-50 border-emerald-400",
  budget: "bg-gray-50 border-gray-300",
};

export default function HotelResultBlock({ hotel }: Props) {
  const borderClass = typeColors[hotel.hotel_type || "budget"] || typeColors.budget;

  const topAmenities = hotel.amenities
    ? Object.keys(hotel.amenities).filter((k) => hotel.amenities![k] && amenityLabels[k]).slice(0, 4)
    : [];

  return (
    <div className={`border-l-2 rounded-lg p-4 text-sm ${borderClass}`}>
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
              &#8377;{hotel.price_per_night.toLocaleString()}<span className="text-xs text-gray-400 font-normal">/night</span>
            </div>
          )}
        </div>
      </div>

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
      </div>

      {hotel.semantic_text && (
        <p className="text-xs text-gray-500 mt-2 line-clamp-2 italic">
          &ldquo;{hotel.semantic_text.slice(0, 150)}&rdquo;
        </p>
      )}
    </div>
  );
}
