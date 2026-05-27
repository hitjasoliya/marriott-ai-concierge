"use client";

import { useChat } from "./hooks/useChat";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

export default function Home() {
  const { messages, send, isLoading } = useChat();
  const hasMessages = messages.length > 0;

  return (
    <div className="h-screen flex flex-col max-w-3xl mx-auto p-4">
      {hasMessages ? (
        <>
          <header className="flex-shrink-0 px-1 py-3 border-b border-gray-100">
            <h1 className="text-lg font-semibold text-gray-800">Marriott AI Concierge</h1>
            <p className="text-xs text-gray-400">Find your perfect stay</p>
          </header>
          <ChatWindow messages={messages} isLoading={isLoading} />
          <ChatInput onSend={send} disabled={isLoading} />
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-6">
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
          <div className="w-full max-w-lg">
            <ChatInput onSend={send} disabled={isLoading} />
          </div>
        </div>
      )}
    </div>
  );
}
