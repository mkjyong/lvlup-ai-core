import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LiveStats from './LiveStats';
import GameSelector from './GameSelector';

const HeroChat: React.FC = () => {
  const navigate = useNavigate();
  const [coachType, setCoachType] = useState<'general' | 'special'>('general');
  const [game, setGame] = useState('');
  const [nickname, setNickname] = useState('');
  const [question, setQuestion] = useState('');

  // listen for examples prompt fill
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as string;
      setQuestion(detail);
    };
    document.addEventListener('fillPrompt', handler);
    return () => document.removeEventListener('fillPrompt', handler);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
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
    <section className="relative isolate flex min-h-screen items-center justify-center bg-[#0a0a0d] px-4 py-24 text-center">
      {/* decorative gradient blob */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_600px_at_center,rgba(255,0,128,0.15)_0%,rgba(0,0,0,0)_70%)]" />

      <div className="w-full max-w-4xl space-y-8 rounded-3xl bg-[#1b1b1f]/90 p-14 shadow-2xl ring-1 ring-primary/40 backdrop-blur-md">
        {/* Branding */}
        <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-transparent bg-gradient-to-r from-[#6b7bff] via-[#ff22aa] to-[#6b7bff] bg-clip-text">
          AI Game Coach
        </h1>

        {/* Typing banner placeholder */}
        <p className="min-h-[1.5rem] text-base text-muted" aria-live="polite">
          실시간 전략 · 경기 분석 · 맞춤 피드백
        </p>

        {/* Live stats */}
        <div className="flex justify-center">
          <LiveStats />
        </div>

        {/* Coach toggle */}
        <div className="flex justify-center gap-2 pt-4">
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

        <form onSubmit={handleSubmit} className="space-y-4">
          {coachType === 'special' && (
            <div className="flex flex-col gap-4 md:flex-row">
              <GameSelector value={game} onChange={setGame} />
              <input
                type="text"
                placeholder="닉네임"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                className="flex-1 rounded border border-border bg-surface p-3 text-sm focus:ring-2 focus:ring-primary"
              />
            </div>
          )}

          <textarea
            placeholder="궁금한 점을 물어보세요..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            className="w-full resize-none rounded border border-border bg-[#0d0d10] p-4 text-base text-white placeholder:text-muted/70 focus:ring-2 focus:ring-primary"
          />

          <button
            type="submit"
            disabled={coachType === 'special' && (!game || !nickname.trim())}
            className="w-full rounded bg-primary px-6 py-3 font-semibold text-bg transition-opacity disabled:opacity-50"
          >
            대화 시작하기 →
          </button>
        </form>
      </div>
    </section>
  );
};

export default HeroChat; 