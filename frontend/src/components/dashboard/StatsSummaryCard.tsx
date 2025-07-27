import React from 'react';

interface Props {
  title: string;
  value: number | string;
  unit?: string;
  percentile?: number;
}

const StatsSummaryCard: React.FC<Props> = ({ title, value, unit, percentile }) => (
  <div className="flex flex-col rounded-lg border border-border p-4 backdrop-blur-md bg-surface/60 shadow-soft">
    <span className="text-sm text-accent/80">{title}</span>
    <div className="mt-1 text-2xl font-bold text-accent flex items-baseline gap-1">
      <span>{value}</span>
      {unit && <span className="text-base font-medium">{unit}</span>}
    </div>
    {percentile !== undefined && (
      <span className="mt-1 text-xs text-primary">상위 {percentile}%</span>
    )}
  </div>
);

export default StatsSummaryCard; 