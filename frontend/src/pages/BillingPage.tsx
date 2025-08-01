import React, { useState, useEffect, useMemo } from 'react';
import api from '../api/client';

// 상품 정보는 백엔드 API 로부터 받아올 수도 있지만, MVP 단계에서는 하드코딩
// KR: 24,200원(VAT포함) / 월   |  글로벌: $15 / mo
const offerings = {
  monthly: {
    id: 'basic_monthly',
    name: 'Basic',
    priceKrw: 22000,
    priceUsd: 15,
    desc: '월간 구독, 언제든지 취소 가능',
  },
  yearly: {
    id: 'basic_yearly',
    name: 'Basic',
    priceKrw: 22000 * 12 * 0.9, // 10% 할인(부가세 별도 계산 후 포함)
    priceUsd: 15 * 12 * 0.9,
    desc: '연간 구독, 비용 절감',
  },
};

const BillingPage: React.FC = () => {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [period, setPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const [error, setError] = useState<string | null>(null);

  // 간단 국가 판별(ko-KR, ko 등) – 실제로는 IP Geo API 가 더 정확
const isKorean = navigator.language.startsWith('ko');
const currency = isKorean ? 'KRW' : 'USD';

  const initiateCheckout = async (offeringId: string) => {
    try {
      setLoadingId(offeringId);
      const res = await api.post<{ checkout_url: string }>('/billing/initiate', {
        offering_id: offeringId,
        currency,
      });
      window.location.href = res.data.checkout_url;
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      setError('결제 페이지로 이동하지 못했습니다.');
    } finally {
      setLoadingId(null);
    }
  };

  const [subInfo, setSubInfo] = useState<{ payment_id?: string } | null>(null);

  const loadSubscription = async () => {
    try {
      const { data } = await api.get('/billing/active');
      setSubInfo(data);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    loadSubscription();
  }, []);

  // expiresAt 배너용 계산
  const expiresBanner = useMemo(() => {
    if (!subInfo?.expires_at) return null;
    const d = new Date(subInfo.expires_at);
    const diff = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return null;
    return `구독이 ${diff}일 후(${d.toLocaleDateString()}) 만료됩니다`;
  }, [subInfo?.expires_at]);

  const cancelSubscription = async () => {
    if (!subInfo?.payment_id) return;
    if (!window.confirm('정말 구독을 해지하시겠습니까?')) return;
    try {
      await api.post('/billing/cancel', { payment_id: subInfo.payment_id });
      alert('구독이 해지되었습니다');
      loadSubscription();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      alert('해지 실패: ' + (err as Error).message);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-border p-4 text-xl font-display">결제 관리</header>
      <main className="flex-1 p-6 flex flex-col items-center justify-center">
        <div className="w-full max-w-md rounded-2xl border border-transparent bg-white/5 p-1 shadow-medium transition-transform motion-safe:hover:-translate-y-1 bg-gradient-to-br from-primary/40 via-accent/30 to-secondary/40">
          <div className="rounded-2xl bg-bg p-8 text-center">
            {error && <p className="mb-4 text-red-500 text-sm">{error}</p>}
            {expiresBanner && <p className="mb-2 text-sm text-primary/80">{expiresBanner}</p>}
            {subInfo?.status === 'payment_failed' && (
              <div className="mb-4 rounded bg-red-500/10 p-2 text-sm text-red-400">
                결제에 실패했습니다. 결제 정보를 업데이트하고 다시 시도해 주세요.
                <button
                  type="button"
                  className="ml-2 underline"
                  onClick={() => initiateCheckout(offerings[period].id)}
                >
                  다시 결제
                </button>
              </div>
            )}
            <h2 className="mb-4 bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-3xl font-extrabold text-transparent drop-shadow">
              {offerings[period].name} 플랜
            </h2>
            {/* Toggle */}
            <div className="mb-6 flex items-center justify-center gap-3 text-sm">
              <span className={period === 'monthly' ? 'text-accent font-semibold' : 'text-muted'}>월간</span>
              <button
                type="button"
                aria-label="기간 전환"
                className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors ${period === 'yearly' ? 'bg-primary' : 'bg-border'}`}
                onClick={() => setPeriod((p) => (p === 'monthly' ? 'yearly' : 'monthly'))}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-bg transition-transform ${period === 'yearly' ? 'translate-x-6' : 'translate-x-1'}`}
                />
              </button>
              <span className={period === 'yearly' ? 'text-accent font-semibold' : 'text-muted'}>연간</span>
            </div>
            {subInfo?.amount_usd ? (
              <p className="mb-6 text-4xl font-bold text-accent drop-shadow">
                {(subInfo.currency || 'USD') === 'KRW'
                  ? `₩${Math.round(subInfo.amount_usd! * 1.1).toLocaleString()} / 월 (VAT 포함)`
                  : `$${subInfo.amount_usd} / 월` }
              </p>
            ) : (
              <p className="mb-6 text-4xl font-bold text-accent drop-shadow">
                {currency === 'KRW'
                  ? `₩${Math.round(offerings[period].priceKrw * 1.1).toLocaleString()} / 월 (VAT 포함)`
                  : `$${offerings[period].priceUsd} / 월`}
              </p>
            )}

            {/* Feature list */}
            <ul className="mb-8 space-y-2 text-left text-sm sm:text-base">
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> AI 챗 코칭 무제한
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> 게임 특화 코칭(LOL, 배그 등 지속 추가)
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> 개인 맞춤 목표 & 코칭
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> 최신 패치 인사이트 제공
              </li>
            </ul>
            <button
              type="button"
              className="w-full mb-3 rounded bg-primary py-3 font-semibold text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
              onClick={() => initiateCheckout(offerings[period].id)}
              disabled={loadingId === offerings[period].id}
            >
              {loadingId === offerings[period].id ? '로딩...' : '구매하기'}
            </button>
            <button
              type="button"
              className="w-full rounded border border-red-500 py-3 font-semibold text-red-500 hover:bg-red-500/10 text-sm"
              onClick={cancelSubscription}
              disabled={!subInfo?.payment_id || !['payment_succeeded','paid'].includes(subInfo.status || '')}
            >
              {subInfo?.status === 'processing' ? '해지 요청 중…' : '구독 해지하기'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BillingPage;
