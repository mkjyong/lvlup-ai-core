import React, { useEffect, useRef, useState } from 'react';
import api from '../api/client';
import ChatBubble, { ChatMessage } from '../components/ChatBubble';

interface HistoryItem {
  id: string;
  question: string;
  answer: string;
}

const PAGE_SIZE = 20;

const HistoryPage: React.FC = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const loader = useRef<HTMLDivElement>(null);

  const fetchPage = async () => {
    const res = await api.get<{ items: HistoryItem[] }>(
      `/api/coach/history?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`,
    );
    setItems((prev) => [...prev, ...res.data.items]);
    setHasMore(res.data.items.length === PAGE_SIZE);
    setPage((p) => p + 1);
  };

  useEffect(() => {
    fetchPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          fetchPage();
        }
      },
      { threshold: 1 },
    );
    if (loader.current) observer.observe(loader.current);
    return () => observer.disconnect();
  }, [loader, hasMore]);

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-border p-4 text-xl font-display">히스토리</header>
      <main className="flex-1 overflow-y-auto p-4">
        {items.map((item) => (
          <div key={item.id} className="mb-6 rounded border border-transparent transition-colors hover:border-accent/40 hover:bg-white/5 hover:backdrop-blur-sm">
            <ChatBubble message={{ id: `${item.id}-q`, role: 'user', text: item.question }} />
            <ChatBubble message={{ id: `${item.id}-a`, role: 'assistant', text: item.answer }} />
          </div>
        ))}
        {hasMore && <div ref={loader} className="h-10" />}
      </main>
    </div>
  );
};

export default HistoryPage; 