import { useEffect } from "react";
import { useChatStore } from "../stores/chat";

export default function SessionSidebar() {
  const { sessions, current, setCurrent, setSessions } = useChatStore();

  useEffect(() => {
    (async () => {
      const list = await fetch("/chat/sessions", { credentials: "include" }).then((r) => r.json());
      setSessions(list);
      if (list.length && !current) setCurrent(list[0].id);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <aside className="w-64 border-r border-border overflow-y-auto">
      {sessions.map((s) => (
        <button
          key={s.id}
          onClick={() => setCurrent(s.id)}
          className={`block w-full text-left px-4 py-2 hover:bg-border/10 ${current?.id === s.id ? 'bg-border/20' : ''}`}
        >
          {s.title || s.id.slice(0, 8)}
        </button>
      ))}
    </aside>
  );
}