import React, { useState } from 'react';
import api from '../api/client';

const offerings = {
  monthly: { id: 'basic_monthly', name: 'Basic', price: '$10 / 월', desc: '월간 구독, 언제든지 취소 가능' },
  yearly: { id: 'basic_yearly', name: 'Basic', price: '$100 / 년 (17% 할인)', desc: '연간 구독, 비용 절감' },
};

const BillingPage: React.FC = () => {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [period, setPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const currency = navigator.language.startsWith('ko') ? 'KRW' : 'USD';

  const initiateCheckout = async (offeringId: string) => {
    try {
      setLoadingId(offeringId);
      const res = await api.post<{ checkout_url: string }>('/billing/initiate', {
        offering_id: offeringId,
        currency,
      });
      window.location.href = res.data.checkout_url;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error(error);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-border p-4 text-xl font-display">결제 관리</header>
      <main className="flex-1 p-6 flex flex-col items-center justify-center">
        <div className="w-full max-w-md rounded-2xl border border-transparent bg-white/5 p-1 shadow-medium transition-transform motion-safe:hover:-translate-y-1 bg-gradient-to-br from-primary/40 via-accent/30 to-secondary/40">
          <div className="rounded-2xl bg-bg p-8 text-center">
            <h2 className="mb-4 bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-3xl font-extrabold text-transparent drop-shadow">{offerings[period].name} 플랜</h2>
            {/* Toggle as before */}
            <div className="mb-6 flex items-center justify-center gap-3 text-sm">
              <span className={period==='monthly'?'text-accent font-semibold':'text-muted'}>월간</span>
              <button
                type="button"
                aria-label="기간 전환"
                className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors ${period==='yearly' ? 'bg-primary' : 'bg-border'}`}
                onClick={() => setPeriod(p=>p==='monthly'?'yearly':'monthly')}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-bg transition-transform ${period==='yearly'?'translate-x-6':'translate-x-1'}`} />
              </button>
              <span className={period==='yearly'?'text-accent font-semibold':'text-muted'}>연간</span>
            </div>
            <p className="mb-6 text-4xl font-bold text-accent drop-shadow">
              {currency === 'KRW' ? offerings[period].price.replace('$', '₩').replace('/ 월', '원 / 월').replace('/ 년', '원 / 년') : offerings[period].price}
            </p>

            {/* Feature list */}
            <ul className="mb-8 space-y-2 text-left text-sm sm:text-base">
              <li className="flex items-center gap-2"><span className="text-accent">✔</span> AI 챗 코칭 무제한</li>
              <li className="flex items-center gap-2"><span className="text-accent">✔</span> 게임 특화 코칭(LOL, 배그 등 지속 추가)</li>
              <li className="flex items-center gap-2"><span className="text-accent">✔</span> 개인 맞춤 목표 & 코칭</li>
              <li className="flex items-center gap-2"><span className="text-accent">✔</span> 최신 패치 인사이트 제공</li>
            </ul>
            <button
              type="button"
              className="w-full rounded bg-primary py-3 font-semibold text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
              onClick={() => initiateCheckout(offerings[period].id)}
              disabled={loadingId === offerings[period].id}
            >
              {loadingId === offerings[period].id ? '로딩...' : '구매하기'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BillingPage; 