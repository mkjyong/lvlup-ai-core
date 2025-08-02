import { useState, useCallback } from "react";

export function useChatStream() {
  const [jsonData, setJsonData] = useState<string | null>(null);
  const [text, setText] = useState("");

  const start = useCallback(async (params: { question: string; game?: string }) => {
    setJsonData(null);
    setText("");

    const token = localStorage.getItem("token");

    // --- FormData 구성 ---
    const form = new FormData();
    form.append("text", params.question);
    if (params.game && (params.game === "lol" || params.game === "pubg")) {
      form.append("game", params.game);
    }

    async function doRequest(accessToken?: string): Promise<Response> {
      return fetch(`${import.meta.env.VITE_API_BASE_URL}/api/coach/ask/stream`, {
        method: "POST",
        body: form,
        credentials: "include",
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
      });
    }

    let response = await doRequest(token || undefined);

    // 토큰 만료 시 자동 재발급 시도
    if (response.status === 401) {
      try {
        const refreshResp = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });
        if (refreshResp.ok) {
          const { access_token }: { access_token: string } = await refreshResp.json();
          localStorage.setItem("token", access_token);
          response = await doRequest(access_token);
        }
      } catch {
        // ignore; 실패 시 아래서 handler 진행
      }
    }

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