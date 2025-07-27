import React, { useState, Suspense } from 'react';
import GameToggle from '../components/GameToggle';
import StatsSummaryCard from '../components/dashboard/StatsSummaryCard';
import ReactLazy from 'react';
const TrendChart = ReactLazy.lazy(() => import('../components/dashboard/TrendChart'));
const PercentileGauge = ReactLazy.lazy(() => import('../components/dashboard/PercentileGauge'));
import { useStatsOverview, useStatsTrend } from '../hooks/useStats';

const metricLabels: Record<string, string> = {
  winRate: '승률',
  kda: 'KDA',
  csPerMin: 'CS/분',
  killParticipation: '킬관여',
  avgDamage: '평균 데미지',
  top10Ratio: 'Top10%',
};

const PerformancePage: React.FC = () => {
  const [game, setGame] = useState('lol');
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');
  const { data: overview, isLoading } = useStatsOverview(game, period);

  const defaultMetric = overview ? Object.keys(overview.metrics)[0] : 'kda';
  const [selectedMetric, setSelectedMetric] = useState(defaultMetric);

  const { data: trend } = useStatsTrend(game, selectedMetric);

  if (isLoading || !overview) return <div className="flex h-screen items-center justify-center">Loading...</div>;

  const { metrics, percentile } = overview;

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-accent/50 p-4 text-xl font-display text-accent shadow-[0_1px_4px_rgba(0,255,149,0.1)] flex items-center justify-between">
        <span>성과 대시보드</span>
        <GameToggle value={game} onChange={(val) => setGame(val)} />
      </header>
      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Period toggle */}
        <div className="flex gap-2">
          {(['weekly', 'monthly'] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className={`rounded px-3 py-1 text-sm uppercase ${period === p ? 'bg-secondary text-bg' : 'bg-surface text-text'}`}
            >
              {p === 'weekly' ? '주간' : '월간'}
            </button>
          ))}
        </div>
        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Object.entries(metrics).map(([key, val]) => (
            <StatsSummaryCard
              key={key}
              title={metricLabels[key] ?? key}
              value={val as number}
              percentile={percentile[key]}
            />
          ))}
        </div>
        {/* Trend chart */}
        <div className="space-y-2">
          <div className="flex gap-2">
            {Object.keys(metrics).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setSelectedMetric(k)}
                className={`rounded px-3 py-1 text-sm ${selectedMetric === k ? 'bg-primary text-bg' : 'bg-surface text-text'}`}
              >
                {metricLabels[k] ?? k}
              </button>
            ))}
          </div>
          {trend && (
            <Suspense fallback={<div>Loading chart...</div>}>
              <TrendChart data={trend.trend} />
            </Suspense>
          )}
        </div>
        {/* Gauge example (첫 번째 metric) */}
        <div className="flex justify-center">
          <Suspense fallback={null}>
            <PercentileGauge value={percentile[selectedMetric] ?? 0} />
          </Suspense>
        </div>
      </main>
    </div>
  );
};

export default PerformancePage; 