"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { ChatMessage } from "../types";
import { search } from "../services/stream";

let nextId = 1;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const sessionIdRef = useRef("");

  useEffect(() => {
    if (!sessionIdRef.current) {
      sessionIdRef.current = crypto.randomUUID();
    }
  }, []);

  const send = useCallback(
    async (text: string, exploreWithoutDates = false) => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = {
        id: String(nextId++),
        role: "user",
        content: text,
      };

      const assistantMsg: ChatMessage = {
        id: String(nextId++),
        role: "assistant",
        content: "",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsLoading(true);

      try {
        const data = await search(
          text,
          2,
          sessionIdRef.current,
          selectedAmenities,
          exploreWithoutDates,
        );

        const errorText = data.error || (!data.reply && !data.hotels?.length ? "Something went wrong. Please try again." : null);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? {
                  ...m,
                  content: errorText || data.reply,
                  hotels: data.hotels,
                  intent: data.intent,
                  suggestions: data.suggestions,
                  suggestedAmenities: data.suggestedAmenities,
                  stage: data.stage,
                }
              : m,
          ),
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: "Something went wrong. Please try again." }
              : m,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [selectedAmenities],
  );

  const toggleAmenity = useCallback((amenity: string) => {
    setSelectedAmenities((prev) =>
      prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity],
    );
  }, []);

  return { messages, send, isLoading, selectedAmenities, toggleAmenity };
}
