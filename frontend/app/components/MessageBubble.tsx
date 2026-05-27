"use client";

import type { ChatMessage } from "../types";
import HotelResultBlock from "./HotelResultBlock";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

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
                {message.isStreaming && <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-text-bottom" />}
              </div>
            )}
            {message.hotels && message.hotels.length > 0 && (
              <div className="mt-4 space-y-3">
                {message.hotels.map((hotel) => (
                  <HotelResultBlock key={hotel.id} hotel={hotel} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
