import { useQuery } from '@tanstack/react-query';
import { fetchStatsOverview, fetchStatsTrend } from '../api/client';

export const useStatsOverview = (game: string, period: 'weekly' | 'monthly') =>
  useQuery({
    queryKey: ['statsOverview', game, period],
    queryFn: () => fetchStatsOverview(game, period),
    enabled: !!game,
    staleTime: 1000 * 60 * 5,
  });

export const useStatsTrend = (
  game: string,
  metric: string,
  weeks = 8,
) =>
  useQuery({
    queryKey: ['statsTrend', game, metric, weeks],
    queryFn: () => fetchStatsTrend(game, metric, weeks),
    enabled: !!game && !!metric,
    staleTime: 1000 * 60 * 5,
  }); 