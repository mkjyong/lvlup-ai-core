import { create } from "zustand";

export interface SessionMeta {
  id: string;
  started_at: string;
  last_used_at: string;
  title?: string;
  preview?: string | null;
}

interface ChatStore {
  sessions: SessionMeta[];
  current?: SessionMeta;
  setCurrent: (id?: string) => void;
  setSessions: (arr: SessionMeta[]) => void;
  upsertSession: (m: SessionMeta) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  sessions: [],
  setCurrent: (id) =>
    set((s) => ({ current: id ? s.sessions.find((v) => v.id === id) : undefined })),
  setSessions: (arr) => set(() => ({ sessions: arr })),
  upsertSession: (meta) =>
    set((s) => {
      const others = s.sessions.filter((x) => x.id !== meta.id);
      return { sessions: [meta, ...others], current: meta };
    }),
}));