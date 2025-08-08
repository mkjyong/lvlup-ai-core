import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useSubscription } from '../hooks/useSubscription';
import Modal from '../components/ui/Modal';
import api from '../api/client';
import PortOne from "@portone/browser-sdk/v2";
import { toast } from 'react-hot-toast';

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
  const [paypalUILoaded, setPayPalUILoaded] = useState(false);
  const [successModalOpen, setSuccessModalOpen] = useState(false);

  const { t, i18n } = useTranslation();
  // 언어 기반 KR 여부 판단 (ko 계열)
  const isKorean = i18n.language.startsWith('ko');
// const isKorean = false;
const currency = isKorean ? 'KRW' : 'USD';

  const initiateCheckout = async () => {
    // 한국(카드) vs 글로벌(PayPal) 분기 처리
    setError(null);
    setLoadingId('subscribe');

    const storeId = import.meta.env.VITE_PORTONE_STORE_ID as string;
    const issueName = 'LvLUp Basic Subscription';
    const issueId = `sub-${Date.now()}`;
    const redirectUrl = window.location.href;

    const channelKey: string | undefined = isKorean
      ? (import.meta.env.VITE_PORTONE_CHANNEL_KEY_CARD as string | undefined)
      : (import.meta.env.VITE_PORTONE_CHANNEL_KEY_PAYPAL as string | undefined);

    if (isKorean) {
      // ----------------------------------------------------
      // 🇰🇷 카드 빌링키 발급 (requestIssueBillingKey)
      // ----------------------------------------------------
      try {
        const reqBody = {
          storeId,
          billingKeyMethod: 'EASY_PAY',
          issueName,
          issueId,
          redirectUrl,
          ...(channelKey ? { channelKey } : {}),
        } as Parameters<typeof PortOne.requestIssueBillingKey>[0];

        const issue: any = await PortOne.requestIssueBillingKey(reqBody);

        if (issue.code !== undefined) throw new Error(issue.message);

        await api.post('/billing/store-billing-key', {
          billing_key: issue.billingKey,
          customer_id: issue.customer?.id,
          channel_key: channelKey,
        });

        setSuccessModalOpen(true);
        refetch();
      } catch (err) {
        console.error(err);
        setError('결제 과정에서 오류가 발생했습니다.');
      } finally {
        setLoadingId(null);
      }
    } else {
      // ----------------------------------------------------
      // 🌐 PayPal 빌링키 발급 (loadIssueBillingKeyUI – PAYPAL_RT)
      // ----------------------------------------------------
      try {
        await PortOne.loadIssueBillingKeyUI(
          {
            uiType: 'PAYPAL_RT',
            storeId,
            billingKeyMethod: 'PAYPAL',
            issueName,
            issueId,
            redirectUrl,
            channelKey: channelKey as string,
          },
          {
            onIssueBillingKeySuccess: async (response: any) => {
              try {
                await api.post('/billing/store-billing-key', {
                  billing_key: response.billingKey,
                  channel_key: channelKey,
                });
                setSuccessModalOpen(true);
                refetch();
              } catch (apiErr) {
                console.error(apiErr);
                setError('서버 저장 중 오류가 발생했습니다.');
              } finally {
                setLoadingId(null);
              }
            },
            // PayPal 빌링키 발급 실패 시(code 포함) 로그 전송 & UI 복원
            onIssueBillingKeyFail: async (error: any) => {
              console.error(error);
              try {
                await api.post('/billing/log-failure', {
                  code: error.code ?? 'UNKNOWN',
                  message: error.message,
                });
              } catch (logErr) {
                console.error('Failed to log billing error', logErr);
              }
              setError(`${error.message || '결제 과정에서 오류가 발생했습니다.'} (code: ${error.code ?? 'N/A'})`);
              setLoadingId(null);
            },
            // 사용자가 PayPal 창을 닫은 경우
            onIssueBillingKeyCancel: () => {
              setLoadingId(null);
                            toast('결제를 취소하셨습니다.');
             },
          } as any,
        );
        setPayPalUILoaded(true);
      } catch (err) {
        console.error(err);
        setError('결제 UI 로드 중 오류가 발생했습니다.');
        setLoadingId(null);
      }
    }
  };

  

  const { subInfo, cancel, refetch } = useSubscription();
  const isSubscribed = !!subInfo?.payment_id && subInfo.status !== 'payment_failed';

  // expiresAt 배너용 계산
  const expiresBanner = useMemo(() => {
    if (!subInfo?.expires_at) return null;
    const d = new Date(subInfo.expires_at);
    const diff = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return null;
    return t('billing.expires_banner', { days: diff, date: d.toLocaleDateString() });
  }, [subInfo?.expires_at, t]);

  const cancelSubscription = async () => {
    if (!subInfo?.payment_id) return;
    if (!window.confirm(t('billing.confirm_cancel'))) return;
    try {
      await cancel(subInfo.payment_id);
      toast.success(t('billing.cancel_success'));
      refetch();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      toast.error(t('billing.cancel_fail', { message: (err as Error).message }));
    }
  };

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-border p-4 text-xl font-display">{t('billing.header')}</header>
      <main className="flex-1 p-6 flex flex-col items-center justify-center">
        <div className="w-full max-w-md rounded-2xl border border-transparent bg-white/5 p-1 shadow-medium transition-transform motion-safe:hover:-translate-y-1 bg-gradient-to-br from-primary/40 via-accent/30 to-secondary/40">
          <div className="rounded-2xl bg-bg p-8 text-center">
            {error && <p className="mb-4 text-red-500 text-sm">{error}</p>}
            {expiresBanner && <p className="mb-2 text-sm text-primary/80">{expiresBanner}</p>}
            {subInfo?.status === 'payment_failed' && (
              <div className="mb-4 rounded bg-red-500/10 p-2 text-sm text-red-400">
                {t('billing.payment_failed')}
                <button
                  type="button"
                  className="ml-2 underline"
                  onClick={initiateCheckout}
                >
                  {t('billing.resubscribe')}
                </button>
              </div>
            )}
            <h2 className="mb-4 bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-3xl font-extrabold text-transparent drop-shadow">
              {t('billing.plan', { plan: offerings[period].name })}
            </h2>
            {/* Toggle */}
            <div className="mb-6 flex items-center justify-center gap-3 text-sm">
              <span className={period === 'monthly' ? 'text-accent font-semibold' : 'text-muted'}>{t('billing.monthly')}</span>
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
              <span className={period === 'yearly' ? 'text-accent font-semibold' : 'text-muted'}>{t('billing.yearly')}</span>
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
                  ? t('billing.cost_per_month_vat', { price: `₩${offerings[period].priceKrw.toLocaleString()}` })
                  : t('billing.cost_per_month', { price: `$${offerings[period].priceUsd}` })}
              </p>
            )}

            {/* Feature list */}
            <ul className="mb-8 space-y-2 text-left text-sm sm:text-base">
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> {t('billing.features.ai_unlimited')}
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> {t('billing.features.game_specific')}
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> {t('billing.features.personalized')}
              </li>
              <li className="flex items-center gap-2">
                <span className="text-accent">✔</span> {t('billing.features.patch_insight')}
              </li>
            </ul>
            {isSubscribed ? (
              <button
                type="button"
                className="w-full mb-3 rounded bg-red-600 py-3 font-semibold text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
                onClick={cancelSubscription}
              >
                {t('billing.cancel')}
              </button>
            ) : (
              isKorean ? (
              <button
                type="button"
                className="w-full mb-3 rounded bg-primary py-3 font-semibold text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
                onClick={initiateCheckout}
                disabled={loadingId === offerings[period].id}
              >
                {loadingId === offerings[period].id ? t('billing.loading') : t('billing.subscribe')}
              </button>
            ) : (
              <>
                {!paypalUILoaded && (
                  <button
                    type="button"
                    className="w-full mb-3 rounded bg-primary py-3 font-semibold text-bg disabled:opacity-50 motion-safe:hover:shadow-[0_0_8px_var(--color-accent)]"
                    onClick={initiateCheckout}
                    disabled={loadingId === offerings[period].id}
                  >
                    {loadingId === offerings[period].id ? t('billing.loading') : t('billing.paypal')}
                  </button>
                )}
                {/* PayPal 버튼 렌더링 컨테이너 */}
                <div className="portone-ui-container flex justify-center my-4" />
              </>
            ))}

          </div>
        </div>
      </main>
      <Modal open={successModalOpen} onClose={() => setSuccessModalOpen(false)}>
        <h3 className="mb-4 text-lg font-bold">{t('billing.success_title')}</h3>
        <button
          type="button"
          className="w-full rounded bg-primary py-2 font-semibold text-bg"
          onClick={() => setSuccessModalOpen(false)}
        >
          {t('billing.confirm')}
        </button>
      </Modal>
    </div>
  );
};

export default BillingPage;
