import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GameSelector from './GameSelector';
import GlassCard from '../ui/GlassCard';

const DuoChatPanel: React.FC = () => {
  const navigate = useNavigate();
  const [coachType, setCoachType] = useState<'general' | 'special'>('general');
  const [game, setGame] = useState('');
  const [nickname, setNickname] = useState('');
  const [question, setQuestion] = useState('');
  const suggestions = [
    '초반 정글 루트 추천해줘',
    '라인전에서 CS 유리하게 먹는 법?',
    '교전 타이밍 잡는 팁 알려줘',
  ];
  const [suggIdx, setSuggIdx] = useState(0);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as string;
      setQuestion(detail);
    };
    document.addEventListener('fillPrompt', handler);
    return () => document.removeEventListener('fillPrompt', handler);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setSuggIdx((i) => (i + 1) % suggestions.length), 4000);
    return () => clearInterval(id);
  }, []);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    if (coachType === 'special' && (!game || !nickname.trim())) return;
    const params = new URLSearchParams();
    params.append('type', coachType);
    if (game) params.append('game', game);
    if (nickname) params.append('nick', nickname);
    params.append('q', question.trim());
    navigate(`/chat?${params.toString()}`);
  };

  return (
    <GlassCard className="mx-auto w-full max-w-3xl p-8 space-y-6">
      <form onSubmit={onSubmit} className="space-y-6">
        {/* Coach toggle */}
        <div className="flex justify-center gap-4">
          {(['general', 'special'] as const).map((t) => (
            <button
              key={t}
              type="button"
              className={`rounded-full px-4 py-1 text-sm font-semibold uppercase transition-colors ${
                coachType === t ? 'bg-primary text-bg' : 'bg-surface text-text'
              }`}
              onClick={() => setCoachType(t)}
            >
              {t === 'general' ? '일반 코치' : '특별 코치'}
            </button>
          ))}
        </div>

        {/* Special inputs */}
        {coachType === 'special' && (
          <div className="flex flex-col gap-4 md:flex-row">
            <GameSelector value={game} onChange={setGame} />
            <input
              type="text"
              placeholder="닉네임"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              className="flex-1 rounded border border-border bg-[#1b1b1f] p-3 text-sm text-white placeholder:text-muted/60 focus:ring-2 focus:ring-primary"
            />
          </div>
        )}

        <textarea
          rows={5}
          placeholder="AI 코치에게 질문해보세요..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="w-full resize-none rounded border border-border bg-[#0d0d10] p-4 text-base text-white placeholder:text-muted/70 focus:ring-2 focus:ring-primary"
        />

        {question.trim() === '' && (
          <p className="text-center text-sm text-muted">
            예시: {suggestions[suggIdx]}
          </p>
        )}

        <button
          type="submit"
          disabled={coachType === 'special' && (!game || !nickname.trim())}
          className="w-full rounded bg-primary px-6 py-3 font-semibold text-bg transition-opacity disabled:opacity-50"
        >
          듀오 시작하기 →
        </button>
      </form>
    </GlassCard>
  );
};

export default DuoChatPanel; 