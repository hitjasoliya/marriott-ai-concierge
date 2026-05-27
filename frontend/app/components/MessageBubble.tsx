"use client";

import { useState } from "react";
import type { ChatMessage } from "../types";
import HotelResultBlock from "./HotelResultBlock";
import SuggestionChips from "./SuggestionChips";
import AmenityChips from "./AmenityChips";

interface Props {
  message: ChatMessage;
  onChipSelect?: (text: string) => void;
  onAmenityToggle?: (amenity: string) => void;
  selectedAmenities?: string[];
  disabled?: boolean;
  isLatest?: boolean;
}

const PAGE_SIZE = 5;

function chunk<T>(arr: T[], size: number): T[][] {
  const pages: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    pages.push(arr.slice(i, i + size));
  }
  return pages;
}

export default function MessageBubble({
  message,
  onChipSelect,
  onAmenityToggle,
  selectedAmenities,
  disabled,
  isLatest,
}: Props) {
  const isUser = message.role === "user";
  const [hotelPage, setHotelPage] = useState(0);

  const hotels = message.hotels || [];
  const pages = chunk(hotels, PAGE_SIZE);
  const currentHotels = pages[hotelPage] || [];

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "order-1" : ""}`}>
        {isUser ? (
          <div className="bg-gray-900 text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm leading-relaxed">
            {message.content}
          </div>
        ) : (
          <div>
            {message.content && (
              <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {message.content}
              </div>
            )}

            {isLatest && message.suggestions && message.suggestions.length > 0 && onChipSelect && (
              <SuggestionChips
                suggestions={message.suggestions}
                onSelect={onChipSelect}
                disabled={disabled}
              />
            )}

            {isLatest && message.suggestedAmenities && message.suggestedAmenities.length > 0 && onAmenityToggle && (
              <AmenityChips
                amenities={message.suggestedAmenities}
                selected={selectedAmenities ?? []}
                onToggle={onAmenityToggle}
                disabled={disabled}
              />
            )}

            {currentHotels.length > 0 && (
              <div className="mt-4 space-y-3">
                {currentHotels.map((hotel) => (
                  <HotelResultBlock key={hotel.id} hotel={hotel} intent={message.intent} />
                ))}
              </div>
            )}
            {pages.length > 1 && (
              <div className="mt-3 flex items-center justify-center gap-3 text-xs text-gray-500">
                <button
                  className="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  disabled={hotelPage === 0}
                  onClick={() => setHotelPage((p) => p - 1)}
                >
                  Prev
                </button>
                <span>
                  {hotelPage + 1} of {pages.length}
                </span>
                <button
                  className="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
                  disabled={hotelPage >= pages.length - 1}
                  onClick={() => setHotelPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
