"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
}

export default function ChatWindow({ messages, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">Marriott AI Concierge</h2>
          <p className="text-gray-500 text-sm leading-relaxed">
            Ask me to find a Marriott hotel anywhere in the world.
          </p>
          <div className="mt-6 space-y-2 text-xs text-gray-400">
            <p>&quot;Peaceful Marriott near Taj Mahal for a workcation&quot;</p>
            <p>&quot;Beachfront resort in Goa with spa for a romantic getaway&quot;</p>
            <p>&quot;Business hotel in New York near Times Square under $300&quot;</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin">
      <div className="space-y-6">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && messages[messages.length - 1]?.role === "assistant" && !messages[messages.length - 1]?.content && (
          <TypingIndicator />
        )}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}
