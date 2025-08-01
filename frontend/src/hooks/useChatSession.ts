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
  const readerRef = useRef<ReadableStreamDefaultReader | null>(null);

  const start = useCallback(async (payload: SendPayload) => {
    const form = new FormData();
    // 세션 ID
    if (payload.sessionId) {
      form.append("session_id", payload.sessionId);
    } else if (current?.id) {
      form.append("session_id", current.id);
    }
    if (payload.text) form.append("text", payload.text);
    if (payload.game) form.append("game", payload.game);
    payload.files?.forEach((f) => form.append("image", f, f.name));

    const res = await fetch("/api/coach/ask/stream", {
      method: "POST",
      body: form,
      credentials: "include",
    });

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
        if (chunk.startsWith("data:")) {
          setStreamText((prev) => prev + chunk.replace("data:", ""));
        }
      }
    }
  }, [current]);

  return { streamText, start };
}