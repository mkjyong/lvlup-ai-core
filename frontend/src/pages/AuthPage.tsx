import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import api from '../api/client';
import { useAuth } from '../hooks/useAuth';

const AuthPage: React.FC = () => {
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [agreePrivacy, setAgreePrivacy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const referralCode = searchParams.get('ref') || undefined;
  const [needsConsent, setNeedsConsent] = useState<boolean>(true);
  // 토큰이 없는 상태에서는 서버에 동의 여부 조회 불가하므로,
  // 로그인 UI 진입 시에는 기본적으로 동의 체크 UI를 보이고,
  // 토큰이 있는(재방문 로그인 상태) 경우에는 서버에서 동의 여부를 조회해 UI를 생략한다.
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setNeedsConsent(true);
      return;
    }
    (async () => {
      try {
        const { data } = await api.get<{ terms: boolean; privacy: boolean }>('/user/consent');
        setNeedsConsent(!(data.terms && data.privacy));
      } catch {
        setNeedsConsent(true);
      }
    })();
  }, []);

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
      // 약관/개인정보 동의 저장 (필수 체크 완료된 상태에서만 이 코드 도달)
      try {
        await api.post('/user/consent', { terms: true, privacy: true });
      } catch {
        // 동의 저장 실패는 로그인 흐름을 막지 않음
      }
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
        {needsConsent && (
          <div className="mx-auto w-full max-w-sm text-left space-y-3">
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-1 h-4 w-4 accent-primary"
              />
              <span>
                이용약관(필수)에 동의합니다.{' '}
                <Link to="/terms" className="underline hover:text-accent">내용보기</Link>
              </span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={agreePrivacy}
                onChange={(e) => setAgreePrivacy(e.target.checked)}
                className="mt-1 h-4 w-4 accent-primary"
              />
              <span>
                개인정보처리방침(필수)에 동의합니다.{' '}
                <Link to="/privacy" className="underline hover:text-accent">내용보기</Link>
              </span>
            </label>
          </div>
        )}

        <div className="flex justify-center mt-4">
          {!needsConsent || (agreeTerms && agreePrivacy) ? (
            <GoogleLogin
              onSuccess={handleSuccess}
              useOneTap={!needsConsent || (agreeTerms && agreePrivacy)}
              theme="filled_blue"
              size="large"
              width="300"
            />
          ) : (
            <button
              type="button"
              disabled
              className="w-[300px] cursor-not-allowed rounded bg-border py-3 font-semibold text-muted"
              title="약관 및 개인정보 처리방침 동의 후 로그인할 수 있습니다."
            >
              약관 동의 후 로그인 이용 가능
            </button>
          )}
        </div>
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