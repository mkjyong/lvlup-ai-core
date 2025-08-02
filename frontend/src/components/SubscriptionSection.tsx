import React, { useEffect, useState } from 'react';
import api from '../api/client';

interface SubscriptionInfo {
  payment_id?: string;
  expires_at?: string;
  status?: string;
  amount_usd?: number;
  currency?: string;
}

const SubscriptionSection: React.FC = () => {
  const [info, setInfo] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const load = async () => {
    try {
      const { data } = await api.get('/billing/active');
      setInfo(data);
    } catch {
      setInfo(null);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const cancel = async () => {
    if (!info?.payment_id) return;
    if (!window.confirm('정말 구독을 해지하시겠습니까?')) return;
    try {
      setLoading(true);
      await api.post('/billing/cancel', { payment_id: info.payment_id });
      alert('구독이 해지되었습니다');
      load();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      alert('해지 실패: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const PlanLabel = () => {
    if (!info?.status || !['payment_succeeded', 'paid', 'processing'].includes(info.status)) {
      return <span className="text-muted">구독 없음</span>;
    }
    return (
      <span className="font-semibold text-accent">
        활성 구독 (만료일: {info.expires_at ? new Date(info.expires_at).toLocaleDateString() : '—'})
      </span>
    );
  };

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-soft">
      <div className="mb-4 text-lg font-semibold">구독</div>
      <PlanLabel />
      {info?.payment_id && ['payment_succeeded', 'paid', 'processing'].includes(info.status || '') && (
        <button
          type="button"
          className="mt-4 rounded border border-red-500 px-4 py-2 text-sm font-semibold text-red-500 hover:bg-red-500/10"
          onClick={cancel}
          disabled={loading}
        >
          {loading ? '처리 중…' : '구독 해지하기'}
        </button>
      )}
    </div>
  );
};

export default SubscriptionSection;
