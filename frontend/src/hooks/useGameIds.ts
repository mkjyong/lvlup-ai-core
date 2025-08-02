import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchGameIds, patchGameIds } from '../api/client';

export const useGameIds = () => {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ['gameIds'],
    queryFn: fetchGameIds,
    staleTime: Infinity, // 세션 동안 캐시 유지 (수동 invalidation)
    cacheTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: patchGameIds,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gameIds'] }),
  });
  return { ...query, updateGameIds: mutation.mutateAsync };
}; 