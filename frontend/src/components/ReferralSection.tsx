import React from 'react';
import { useReferral } from '../hooks/useReferral';

const ReferralSection: React.FC = () => {
  const { data, isLoading, issueReferral } = useReferral();

  if (isLoading) return <p>로딩 중...</p>;
  if (!data) return <p>레퍼럴 정보를 불러올 수 없습니다.</p>;

  const url = data.referral_code ? `${window.location.origin}/auth?ref=${data.referral_code}` : '';

  const issueCode = async () => {
    try {
      await issueReferral();
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="font-medium">나의 코드:</span> {data.referral_code ?? '미발급'}
        {!data.referral_code && (
          <button
            type="button"
            className="rounded border border-accent px-2 py-0.5 text-[12px] text-accent hover:bg-accent hover:text-bg"
            onClick={issueCode}
          >
            발급
          </button>
        )}
      </div>
      <div>
        <span className="font-medium">추천인 수:</span> {data.referred_count}
      </div>
      <div>
        <span className="font-medium">적립 크레딧:</span> {data.credits}
      </div>
      {data.referral_code && (
        <button
          type="button"
          className="mt-2 rounded bg-primary px-3 py-1 text-sm text-bg"
          onClick={() => {
            navigator.clipboard.writeText(url);
          }}
        >
          링크 복사
        </button>
      )}
    </div>
  );
};

export default ReferralSection; 