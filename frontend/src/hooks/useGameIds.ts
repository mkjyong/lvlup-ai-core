import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchGameIds, patchGameIds } from '../api/client';

export const useGameIds = () => {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ['gameIds'],
    queryFn: fetchGameIds,
  });

  const mutation = useMutation({
    mutationFn: patchGameIds,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gameIds'] }),
  });
  return { ...query, updateGameIds: mutation.mutateAsync };
}; 