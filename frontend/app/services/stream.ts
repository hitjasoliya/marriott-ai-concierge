const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StreamHandlers {
  onIntent: (data: Record<string, unknown>) => void;
  onHotels: (data: unknown[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
  onStatus: (message: string) => void;
}

export async function streamSearch(query: string, guests: number, handlers: StreamHandlers): Promise<void> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    body: JSON.stringify({ query, guests }),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    handlers.onError("Search request failed");
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    handlers.onError("No response stream");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;

      const jsonStr = trimmed.slice(6);
      if (jsonStr === "[DONE]") {
        handlers.onDone();
        return;
      }

      try {
        const event = JSON.parse(jsonStr);
        switch (event.type) {
          case "intent":
            handlers.onIntent(event.data);
            break;
          case "hotels":
            handlers.onHotels(event.data);
            break;
          case "token":
            handlers.onToken(event.data);
            break;
          case "done":
            handlers.onDone();
            return;
          case "status":
            handlers.onStatus(event.message || event.data);
            break;
          case "error":
            handlers.onError(event.message || "Unknown error");
            return;
        }
      } catch {
        // skip malformed JSON lines
      }
    }
  }

  handlers.onDone();
}
