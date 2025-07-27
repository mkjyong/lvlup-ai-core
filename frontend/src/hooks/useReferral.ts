import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';

export interface ReferralInfo {
  referral_code: string | null;
  credits: number;
  referred_count: number;
}

const fetchReferral = async (): Promise<ReferralInfo> => {
  const { data } = await api.get<ReferralInfo>('/referral/me');
  return data;
};

const issueReferral = async (): Promise<ReferralInfo> => {
  const { data } = await api.post<ReferralInfo>('/referral/issue');
  return data;
};

export const useReferral = () => {
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ['referralInfo'],
    queryFn: fetchReferral,
    staleTime: 1000 * 60 * 10,
  });

  const mutation = useMutation({
    mutationFn: issueReferral,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['referralInfo'] }),
  });

  return {
    ...query,
    issueReferral: mutation.mutateAsync,
  };
}; 