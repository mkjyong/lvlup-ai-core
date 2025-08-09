import { useState, useRef, useCallback } from "react";
import { useChatStore } from "../stores/chat";

interface SendPayload {
  text?: string;
  files?: File[];
  game?: string;
  sessionId?: string;
}

export function useChatSession() {
  const { current, upsertSession } = useChatStore();
  const [streamText, setStreamText] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const readerRef = useRef<ReadableStreamDefaultReader | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastPayloadRef = useRef<SendPayload | null>(null);

  const start = useCallback(async (payload: SendPayload) => {
    lastPayloadRef.current = payload;
    const form = new FormData();
    // 세션 ID
    if (payload.sessionId) {
      form.append("session_id", payload.sessionId);
    } else if (current?.id) {
      form.append("session_id", current.id);
    }
    if (payload.text) form.append("text", payload.text);
    if (payload.game && (payload.game === "lol" || payload.game === "pubg")) {
      form.append("game", payload.game);
    }
    payload.files?.forEach((f) => form.append("image", f, f.name));

    async function doRequest(accessToken?: string): Promise<Response> {
      abortControllerRef.current = new AbortController();
      return fetch(`${import.meta.env.VITE_API_BASE_URL}/api/coach/ask/stream`, {
        method: "POST",
        body: form,
        credentials: "include",
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
        signal: abortControllerRef.current.signal,
      });
    }

    let res = await doRequest(localStorage.getItem("token") || undefined);

    // --- 에러 상태 선처리 -----------------------------------
    if (res.status === 429) {
      // 사용량 한도 초과 → 사용자에게 명확한 메시지 전달
      let detail = "사용량 한도에 도달했습니다.";
      try {
        const j = await res.json();
        if (typeof j.detail === "string") detail = j.detail;
      } catch {
        // ignore parsing error; keep default detail
      }
      throw new Error(detail);
    }

    if (res.status === 401) {
      try {
        const refreshResp = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });
        if (refreshResp.ok) {
          const { access_token }: { access_token: string } = await refreshResp.json();
          localStorage.setItem("token", access_token);
          res = await doRequest(access_token);
        }
      } catch {}
    }

    const sid = res.headers.get("X-Chat-Session");
    if (sid) {
      upsertSession({
        id: sid,
        started_at: new Date().toISOString(),
        last_used_at: new Date().toISOString(),
      });
    }

    if (!res.body) return;
    readerRef.current = res.body.getReader();
    setStreamText("");
    setIsThinking(true);

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await readerRef.current.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        // Parse SSE: optional 'event:' + required 'data:'
        const lines = chunk.split("\n");
        const eventLine = lines.find((l) => l.startsWith("event:"));
        const dataLine = lines.find((l) => l.startsWith("data:"));
        if (dataLine) {
          const data = dataLine.replace("data:", "");
          const ev = eventLine ? eventLine.replace("event:", "").trim() : undefined;
          if (ev === "thinking") {
            setIsThinking(true);
          } else if (ev === "token") {
            setStreamText((prev) => prev + data);
          } else if (ev === "done") {
            setIsThinking(false);
          } else if (!ev) {
            // backward compatibility: treat as token
            setStreamText((prev) => prev + data);
          }
        }
      }
    }
    setIsThinking(false);
  }, [current]);

  const abort = useCallback(() => {
    try {
      abortControllerRef.current?.abort();
    } catch {}
    setIsThinking(false);
  }, []);

  const regenerate = useCallback(async () => {
    if (lastPayloadRef.current) {
      await start(lastPayloadRef.current);
    }
  }, [start]);

  return { streamText, isThinking, start, abort, regenerate };
}