import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import api from '../api/client';

export interface SubscriptionInfo {
  payment_id?: string;
  expires_at?: string;
  status?: string;
  amount_usd?: number;
  currency?: string;
}

const fetchSubscription = async (): Promise<SubscriptionInfo | null> => {
  try {
    const { data } = await api.get('/billing/active');
    return data;
  } catch {
    return null;
  }
};

export const useSubscription = () => {
  const queryClient = useQueryClient();
  const {
    data: subInfo,
    isLoading,
    error,
    refetch,
  } = useQuery({ queryKey: ['subscription'], queryFn: fetchSubscription, staleTime: 5 * 60 * 1000 });

  const cancelMutation = useMutation({
    mutationFn: async (paymentId: string) => {
      await api.post('/billing/cancel', { payment_id: paymentId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
    },
  });

  return {
    subInfo: subInfo ?? null,
    isLoading,
    error,
    refetch,
    cancel: cancelMutation.mutateAsync,
  };
};
