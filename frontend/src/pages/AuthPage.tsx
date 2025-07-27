import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import api from '../api/client';
import { useAuth } from '../hooks/useAuth';

const AuthPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get('ref') || undefined;

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    const idToken = credentialResponse.credential;
    if (!idToken) return;
    try {
      const res = await api.post<{ access_token: string }>(
        `/auth/google/login${referralCode ? `?referral_code=${referralCode}` : ''}`,
        {
          id_token: idToken,
        },
      );
      login(res.data.access_token);
      navigate('/chat');
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    }
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg text-text px-4"
    >
      {/* Animated neon grid */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-20 blur-sm"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, transparent, transparent 49px, rgba(0, 175, 255, 0.1) 50px), repeating-linear-gradient(90deg, transparent, transparent 49px, rgba(0, 175, 255, 0.1) 50px)',
        }}
      />

      {/* Stars particles */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(#00afff_1px,transparent_1px)] [background-size:4px_4px] opacity-10" />

      <div className="w-full max-w-lg space-y-10 rounded-xl border border-accent/30 bg-white/5 p-10 text-center backdrop-blur-md shadow-medium">
        <h1
          className="bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text font-display font-extrabold text-transparent drop-shadow-lg whitespace-nowrap"
          style={{ fontSize: 'clamp(2rem,4vw,3rem)' }}
        >
          LvLUp AI 로그인
        </h1>
        <p className="text-sm sm:text-base text-muted">
          Google 계정으로 안전하게 로그인하고 <span className="text-accent font-semibold">한 단계 성장</span>하세요.
        </p>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            useOneTap
            theme="filled_blue"
            size="large"
            width="300"
          />
        </div>
        <button
          type="button"
          onClick={() => {
            login('guest-token');
            localStorage.setItem('onboarded', 'true');
            navigate('/chat');
          }}
          className="mx-auto mt-4 block rounded border border-accent px-4 py-2 text-sm font-semibold text-accent transition-colors hover:bg-accent hover:text-bg motion-safe:hover:shadow-[0_0_6px_var(--color-accent)]"
        >
          게스트 모드로 체험하기
        </button>
        <p className="mt-4 flex items-center justify-center gap-1 text-xs text-muted/80">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            fill="currentColor"
            className="text-accent"
            viewBox="0 0 16 16"
          >
            <path d="M8 0a8 8 0 1 0 8 8A8.009 8.009 0 0 0 8 0Zm0 14.667A6.667 6.667 0 1 1 14.667 8 6.674 6.674 0 0 1 8 14.667Z" />
            <path d="M8 4a.667.667 0 1 0 .667.667A.667.667 0 0 0 8 4Zm1 3.333H7a.333.333 0 0 0-.333.333v3a.333.333 0 0 0 .333.334h2a.333.333 0 0 0 .333-.334v-3A.333.333 0 0 0 9 7.333Z" />
          </svg>
          Google OAuth 암호화 인증
        </p>
      </div>
    </div>
  );
};

export default AuthPage; 