"use client";

import { useState, useCallback } from "react";
import type { ChatMessage } from "../types";
import { search } from "../services/stream";

let nextId = 1;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const send = useCallback(async (text: string) => {
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
      const data = await search(text, 2);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? { ...m, content: data.reply, hotels: data.hotels, intent: data.intent }
            : m
        )
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? { ...m, content: "Something went wrong. Please try again." }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, send, isLoading };
}
