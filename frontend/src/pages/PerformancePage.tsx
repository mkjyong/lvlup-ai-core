import React from 'react';

/**
 * PerformancePage (Dashboard Placeholder)
 * --------------------------------------------------
 * 2025-07-XX
 * 당장은 실제 통계 API/컴포넌트가 준비되지 않았으므로
 * 간단한 "Coming Soon" 화면을 하드코딩해둡니다.
 *
 * 추후 구현 시:
 * 1. useStatsOverview / useStatsTrend 훅 복원
 * 2. TrendChart, PercentileGauge, StatsSummaryCard 재연결
 * 3. GameToggle, 기간 선택 UI 등 추가
 */

const PerformancePage: React.FC = () => {
  return (
    <div className="flex h-screen flex-col items-center justify-center bg-bg text-text">
      <h1 className="mb-4 text-3xl font-display text-primary">
        당신의 게임 실력은 얼마나 상승하게 될까요?
      </h1>
      <p className="text-xl text-accent">Coming&nbsp;Soon...</p>
    </div>
  );
};

export default PerformancePage;
