"use client";

import { useState, useCallback, useRef } from "react";
import type { ChatMessage, IntentData, SearchResultItem } from "../types";
import { streamSearch } from "../services/stream";

let nextId = 1;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const assistantRef = useRef<ChatMessage | null>(null);

  const send = useCallback((text: string) => {
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
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    assistantRef.current = assistantMsg;
    setIsLoading(true);

    const updateAssistant = (updates: Partial<ChatMessage>) => {
      const id = assistantRef.current?.id;
      if (!id) return;
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...updates } : m))
      );
    };

    streamSearch(text, 2, {
      onIntent(data) {
        updateAssistant({ intent: data as IntentData });
      },
      onHotels(data) {
        updateAssistant({ hotels: data as SearchResultItem[] });
      },
      onToken(token) {
        const current = assistantRef.current;
        updateAssistant({ content: (current?.content || "") + token });
      },
      onDone() {
        updateAssistant({ isStreaming: false });
        assistantRef.current = null;
        setIsLoading(false);
      },
      onError(message) {
        updateAssistant({ content: message || "Something went wrong. Please try again.", isStreaming: false });
        assistantRef.current = null;
        setIsLoading(false);
      },
      onStatus(_message) {
        // status updates are transparent to the UI
      },
    });
  }, []);

  return { messages, send, isLoading };
}
