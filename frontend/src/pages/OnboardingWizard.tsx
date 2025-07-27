import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'classnames';

// Types for the wizard form data
interface WizardData {
  gameId: string;
  game: string;
  goal: string;
}

const games = ['League of Legends', 'PUBG', 'Valorant', 'Overwatch 2'];
const goals = [
  { value: 'rank_up', label: '랭크 승급' },
  { value: 'win_rate', label: '승률 55%+' },
  { value: 'kd', label: 'K/D 2.0+' },
];

const ProgressDots: React.FC<{ step: number }> = ({ step }) => (
  <div className="mt-6 flex items-center justify-center gap-3" aria-label={`진행도 ${step} / 4 단계`}>
    {[1, 2, 3, 4].map((i) => (
      <span
        key={i}
        className={clsx('h-2 w-2 rounded-full', i <= step ? 'bg-accent' : 'bg-border')}
      />
    ))}
    <span className="ml-3 text-xs text-muted">{step} / 4 단계</span>
  </div>
);

const OnboardingWizard: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [data, setData] = useState<WizardData>({ gameId: '', game: '', goal: '' });
  const [error, setError] = useState('');

  const next = () => setStep((s) => Math.min(4, s + 1));
  const prev = () => setStep((s) => Math.max(1, s - 1));

  const handleFinish = () => {
    localStorage.setItem('onboarded', 'true');
    // TODO: send `data` to backend
    navigate('/chat');
  };

  /* ----------------------------- Step Renderers ---------------------------- */
  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="flex w-full max-w-md flex-col items-center text-center">
            <h2 className="mb-4 text-2xl font-bold">Game ID를 연동해요</h2>
            <p className="mb-8 text-muted">전적을 자동으로 가져오기 위해 닉네임/배틀태그를 입력해 주세요.</p>
            <input
              type="text"
              placeholder="닉네임 또는 배틀태그"
              value={data.gameId}
              onChange={(e) => setData({ ...data, gameId: e.target.value })}
              className="w-full rounded border border-border bg-surface p-3 text-center outline-none focus:ring-2 focus:ring-primary"
              aria-invalid={!!error}
            />
            {error && (
              <p className="mt-2 text-sm text-red-500" aria-live="polite">
                {error}
              </p>
            )}
            <button
              className="mt-8 w-full rounded bg-primary py-3 font-semibold text-bg hover:bg-primary/90 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
              onClick={() => {
                if (!data.gameId.trim()) {
                  setError('닉네임을 다시 확인해 주세요 😢');
                  return;
                }
                setError('');
                next();
              }}
            >
              다음 단계 2 / 4 →
            </button>
          </div>
        );
      case 2:
        return (
          <div className="flex w-full max-w-md flex-col items-center text-center">
            <h2 className="mb-4 text-2xl font-bold">주력 게임을 선택해요</h2>
            <p className="mb-8 text-muted">가장 많이 플레이하는 게임을 골라 주세요.</p>
            <div className="grid w-full gap-4">
              {games.map((g) => (
                <button
                  key={g}
                  className={`rounded border p-3 font-semibold transition-colors hover:border-primary hover:text-primary ${
                    data.game === g ? 'border-primary text-primary' : 'border-border text-text'
                  }`}
                  onClick={() => setData({ ...data, game: g })}
                >
                  {g}
                </button>
              ))}
            </div>
            <div className="mt-8 flex w-full justify-between">
              <button className="text-muted" onClick={prev}>
                ← 이전
              </button>
              <button
                className="rounded bg-primary px-4 py-2 text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
                disabled={!data.game}
                onClick={next}
              >
                다음 단계 3 / 4 →
              </button>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="flex w-full max-w-md flex-col items-center text-center">
            <h2 className="mb-4 text-2xl font-bold">목표를 설정해요</h2>
            <p className="mb-8 text-muted">시즌 종료 전 달성하고 싶은 목표를 골라 주세요.</p>
            <div className="grid w-full gap-4">
              {goals.map((g) => (
                <button
                  key={g.value}
                  className={`rounded border p-3 font-semibold transition-colors hover:border-primary hover:text-primary ${
                    data.goal === g.value ? 'border-primary text-primary' : 'border-border text-text'
                  }`}
                  onClick={() => setData({ ...data, goal: g.value })}
                >
                  {g.label}
                </button>
              ))}
            </div>
            <div className="mt-8 flex w-full justify-between">
              <button className="text-muted" onClick={prev}>
                ← 이전
              </button>
              <button
                className="rounded bg-primary px-4 py-2 text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
                disabled={!data.goal}
                onClick={next}
              >
                분석 시작 →
              </button>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="flex w-full max-w-md flex-col items-center text-center">
            <h2 className="mb-6 text-2xl font-bold">데이터 수집 중…</h2>
            <p className="mb-4 text-muted">첫 분석이 완료되면 알림을 드릴게요!</p>
            <div className="relative mb-8 h-2 w-full overflow-hidden rounded bg-border">
              <div className="absolute inset-0 motion-safe:animate-progress bg-accent" />
            </div>
            <button
              className="rounded bg-primary px-6 py-3 font-semibold text-bg hover:bg-primary/90"
              onClick={handleFinish}
            >
              대시보드로 이동 →
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-bg text-text px-4">
      <ProgressDots step={step} />
      {renderStepContent()}
    </div>
  );
};

export default OnboardingWizard; 