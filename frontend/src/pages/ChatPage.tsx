import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { v4 as uuid } from 'uuid';
import ChatBubble, { ChatMessage } from '../components/ChatBubble';
import GameToggle from '../components/GameToggle';
import SessionSidebar from '../components/SessionSidebar';
import AccountBar from '../components/AccountBar';
import { useGameIds } from '../hooks/useGameIds';
import { useChatSession } from '../hooks/useChatSession';
import { useChatStore } from '../stores/chat';

const ChatPage: React.FC = () => {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const initialQuestion = urlParams.get('q') ?? '';
  const initialGameParam = (urlParams.get('game') as 'general' | 'lol' | 'pubg' | null) ?? null;
  const nicknameRef = useRef<string | null>(urlParams.get('nick'));

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { current } = useChatStore();
  const [input, setInput] = useState(initialQuestion);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showLimitWarning, setShowLimitWarning] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [game, setGame] = useState<'general' | 'lol' | 'pubg'>(initialGameParam ?? 'general');
  const { data: gameIds, updateGameIds } = useGameIds();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Streaming hook ---------------------------------------------
  const { streamText, start: startStream } = useChatSession();
  const assistantMessageIdRef = useRef<string | null>(null);

  // helper to add files with limit
  const addImageFiles = (files: File[]) => {
    if (files.length === 0) return;
    setImageFiles((prev) => {
      const combined = [...prev, ...files];
      if (combined.length > 3) {
        if (!showLimitWarning) {
          setShowLimitWarning(true);
          setTimeout(() => setShowLimitWarning(false), 2000);
        }
      }
      return combined.slice(0, 3);
    });
  };

  // 이미지 클립보드 붙여넣기 지원 ----------------------
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i += 1) {
        const item = items[i];
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            addImageFiles([file]);
            e.preventDefault();
            break;
          }
        }
      }
    };
    window.addEventListener('paste', handlePaste);
    return () => {
      window.removeEventListener('paste', handlePaste);
    };
  }, []);

  const exampleText = useMemo(() => {
    if (game === 'lol') return '예시: "내 롤 전적을 분석해서 코칭해줘"';
    if (game === 'pubg') return '예시: "내 배그 전적을 분석해서 코칭해줘"';
    return '예시: "오버워치 게임 전략을 알려줘"';
  }, [game]);

  const sendMessage = async () => {
    if (!input.trim() && imageFiles.length === 0) return;

    const imageUrls = imageFiles.map((f) => URL.createObjectURL(f));


    const userMsg: ChatMessage = {
      id: uuid(),
      role: 'user',
      text: input || undefined,
      imageUrls,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setImageFiles([]);

    const assistantId = uuid();
    assistantMessageIdRef.current = assistantId;
    setMessages((prev) => [...prev, { id: assistantId, role: 'assistant', text: '...' }]);

    try {
      await startStream({
        text: userMsg.text ?? '',
        files: imageFiles,
        game,
      });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, text: '오류가 발생했습니다.' } : m)),
      );
    }
  };

  // Auto-send initial question if provided via URL
  const hasAutoSent = useRef(false);
  useEffect(() => {
    if (!hasAutoSent.current && initialQuestion.trim()) {
      hasAutoSent.current = true;
      sendMessage();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 세션 변경 시 히스토리 로드
  useEffect(() => {
    if (!current?.id) return;
    (async () => {
      const list = await fetch(`/chat/messages?session_id=${current.id}`, {
        credentials: 'include',
      }).then((r) => r.json());
      const mapped: ChatMessage[] = list.map((m: any) => ({ id: uuid(), role: m.role, text: m.text }));
      setMessages(mapped);
    })();
  }, [current?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Token streaming effect -------------------------------------
  useEffect(() => {
    if (!assistantMessageIdRef.current) return;
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantMessageIdRef.current ? { ...m, text: streamText || m.text } : m,
      ),
    );
  }, [streamText]);


  return (
   <div className={`flex h-full bg-bg text-text ${isDragging ? 'ring-4 ring-primary/40' : ''}`}>
     <SessionSidebar />
     <div className="flex flex-1 flex-col"
      onDragOver={(e) => {
        e.preventDefault();
      }}
      onDragEnter={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith('image/'));
        addImageFiles(files);
      }}
    >
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-accent/50 bg-bg/80 p-4 backdrop-blur-md shadow-[0_1px_4px_rgba(0,255,149,0.1)]">
        <Link to="/" className="font-display text-xl text-accent hover:text-primary">
          LvLUp AI 코치
        </Link>
        <GameToggle
          value={game}
          onChange={(val) => {
            // @ts-ignore
            setGame(val);
          }}
        />
      </header>
      <main className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted">
            <p className="text-center text-sm">AI 코치에게 첫 질문을 던져보세요!</p>
            <p className="text-center text-xs">{exampleText}</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </main>
      {game !== 'general' && (
        <div className="border-t border-border bg-bg/70 p-2 backdrop-blur-md">
          <AccountBar
            game={game as 'lol' | 'pubg'}
            account={gameIds ? gameIds[game as 'lol' | 'pubg'] : undefined}
            onSave={async (data) => {
              await updateGameIds({ [game]: data });
            }}
          />
        </div>
      )}

      <form
        className="flex items-center gap-2 border-t border-border p-4"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <input
          className="flex-1 rounded border border-border bg-surface p-2 text-sm focus:border-primary focus:outline-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="무엇이 궁금한가요? (Enter 전송)"
        />
        <button
          type="button"
          className="rounded border border-border bg-surface px-2 py-2 text-xs hover:bg-border"
          onClick={() => fileInputRef.current?.click()}
          disabled={imageFiles.length >= 3}
        >
          이미지
        </button>
        <input
          type="file"
          accept="image/*"
          multiple
          hidden
          ref={fileInputRef}
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            addImageFiles(files);
          }}
        />
        {imageFiles.length > 0 && (
          <div className="flex gap-1">
            {imageFiles.map((f) => (
              <img
                key={f.name + f.lastModified}
                src={URL.createObjectURL(f)}
                alt="preview"
                className="h-10 w-10 rounded object-cover"
                loading="lazy"
              />
            ))}
          </div>
        )}
        {showLimitWarning && (
          <span className="text-xs text-red-400">이미지는 최대 3장까지 첨부할 수 있습니다.</span>
        )}
        <button
          type="submit"
          className="flex items-center gap-1 rounded bg-primary px-4 py-2 text-bg disabled:opacity-40 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
          disabled={!input.trim() && imageFiles.length === 0}
        >
          전송
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="currentColor"
            viewBox="0 0 16 16"
            width="14"
            height="14"
          >
            <path d="M1 8l14-7v14L1 8z" />
          </svg>
        </button>
      </form>
    </div>
  </div>
  );
};

export default ChatPage; 