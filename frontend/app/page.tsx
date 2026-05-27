"use client";

import { useChat } from "./hooks/useChat";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

export default function Home() {
  const { messages, send, isLoading } = useChat();

  return (
    <div className="h-screen flex flex-col max-w-3xl mx-auto">
      <header className="flex-shrink-0 px-4 py-3 border-b border-gray-100">
        <h1 className="text-lg font-semibold text-gray-800">Marriott AI Concierge</h1>
        <p className="text-xs text-gray-400">Find your perfect stay</p>
      </header>
      <ChatWindow messages={messages} isLoading={isLoading} />
      <ChatInput onSend={send} disabled={isLoading} />
    </div>
  );
}
