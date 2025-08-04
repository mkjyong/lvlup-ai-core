import React, { useEffect, useState } from 'react';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';
import ChatBubble from '../components/ChatBubble';
import { useChatStore } from '../stores/chat';

const PAGE_SIZE = 20;

const HistoryPage: React.FC = () => {
  const { sessions, setSessions, setCurrent } = useChatStore();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const fetchPage = async (init = false) => {
    if (isLoading || (!init && !hasMore)) return;
    setIsLoading(true);
    try {
      const { data } = await api.get('/chat/sessions', {
        params: { offset: init ? 0 : offset, limit: PAGE_SIZE },
      });
      if (init) {
        setSessions(data);
      } else {
        setSessions([...sessions, ...data]);
      }
      if (data.length < PAGE_SIZE) setHasMore(false);
      setOffset((prev) => prev + data.length);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPage(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-border p-4 text-xl font-display">대화 히스토리</header>
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && sessions.length === 0 && (
          <div className="flex h-full items-center justify-center text-muted">로딩 중...</div>
        )}
        {!isLoading && sessions.length === 0 && (
          <div className="flex h-full items-center justify-center text-muted">저장된 대화가 없습니다.</div>
        )}
        {sessions.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => {
              setCurrent(s.id);
              navigate('/chat');
            }}
            className="flex w-full flex-col gap-1 rounded border border-transparent p-4 text-left transition-colors hover:border-accent/40 hover:bg-white/5 hover:backdrop-blur-sm"
          >
            <span className="text-sm text-muted">{new Date(s.started_at).toLocaleString()}</span>
            {s.preview ? (
              <p className="mt-1 line-clamp-2 text-sm text-text/80">{s.preview}</p>
            ) : (
              <span className="mt-1 text-sm text-muted">대화가 비어있습니다.</span>
            )}
          </button>
        ))}
        {hasMore && (
          <div className="flex items-center justify-center pt-4">
            <button
              type="button"
              onClick={() => fetchPage()}
              disabled={isLoading}
              className="rounded border border-border px-3 py-1 text-sm hover:bg-border/20 disabled:opacity-50"
            >
              {isLoading ? '로딩...' : '더 보기'}
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default HistoryPage; 