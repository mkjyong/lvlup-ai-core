import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const DemoSection: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nickname.trim()) {
      setError('닉네임을 입력해주세요');
      return;
    }
    setError('');
    setSubmitted(true);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNickname(e.target.value);
    if (error) setError('');
  };

  if (!isAuthenticated)
    return (
      <section className="bg-bg py-16">
        <div className="container mx-auto flex flex-col items-center justify-center px-4 text-center">
          <h2 className="mb-4 text-2xl font-bold">AI 코칭, 직접 경험해보세요</h2>
          <p className="mb-8 text-muted">회원가입 후 데모 체험이 가능합니다.</p>
          <Link
            to="/auth"
            className="rounded bg-primary px-6 py-3 font-semibold text-bg transition-colors hover:bg-primary/90"
          >
            회원가입 하러 가기
          </Link>
        </div>
      </section>
    );

  return (
    <section className="bg-bg py-16">
      <div className="container mx-auto flex flex-col items-center justify-center px-4 text-center">
        <h2 className="mb-4 text-2xl font-bold">AI 코칭, 직접 경험해보세요</h2>
        {!submitted ? (
          <form onSubmit={handleSubmit} className="flex flex-col items-center space-y-4">
            <input
              type="text"
              placeholder="게임 닉네임을 입력하세요"
              value={nickname}
              onChange={handleChange}
              className="w-64 rounded border border-border bg-surface p-3 text-center outline-none focus:ring-2 focus:ring-primary"
              aria-invalid={!!error}
            />
            {error && (
              <p className="text-sm text-red-500" aria-live="polite">
                {error}
              </p>
            )}
            <button
              type="submit"
              className="rounded bg-primary px-6 py-3 font-semibold text-bg transition-colors hover:bg-primary/90"
            >
              AI 분석 보기
            </button>
          </form>
        ) : (
          <p className="text-lg font-semibold text-primary">분석 중입니다... (데모)</p>
        )}
      </div>
    </section>
  );
};

export default DemoSection; 