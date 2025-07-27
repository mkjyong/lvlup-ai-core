import { useState, useCallback } from "react";

export function useChatStream() {
  const [jsonData, setJsonData] = useState<string | null>(null);
  const [text, setText] = useState("");

  const start = useCallback(async (params: { question: string; game?: string }) => {
    setJsonData(null);
    setText("");

    const response = await fetch("/api/coach/ask/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      credentials: "include",
    });

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    const processBuffer = () => {
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        const lines = chunk.split("\n");
        const eventLine = lines.find((l) => l.startsWith("event:"));
        const dataLine = lines.find((l) => l.startsWith("data:"));
        if (eventLine && dataLine) {
          const event = eventLine.replace("event:", "").trim();
          const dataRaw = dataLine.replace("data:", "").trim();
          if (event === "json") {
            setJsonData(dataRaw);
          } else if (event === "token") {
            setText((prev) => prev + dataRaw);
          }
        }

        boundary = buffer.indexOf("\n\n");
      }
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      processBuffer();
    }
  }, []);

  return { jsonData, text, start };
} 