"use client";

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
};

interface Props {
  amenities: string[];
  selected: string[];
  onToggle: (amenity: string) => void;
  disabled?: boolean;
}

export default function AmenityChips({ amenities, selected, onToggle, disabled }: Props) {
  if (!amenities.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {amenities.map((a) => {
        const isSelected = selected.includes(a);
        return (
          <button
            key={a}
            onClick={() => onToggle(a)}
            disabled={disabled}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              isSelected
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white hover:bg-gray-100 text-gray-700 border-gray-200 hover:border-gray-300"
            } disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {amenityLabels[a] || a}
          </button>
        );
      })}
    </div>
  );
}
