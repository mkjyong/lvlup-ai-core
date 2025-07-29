import React, { useEffect, useState } from 'react';

interface Stats {
  active: number;
  improved: number;
}

/**
 * 실시간 코칭 지표 배지.
 *  - 현재 코칭 중인 사용자 수와 최근 24시간 실력 향상 사용자 수를 보여줍니다.
 *  - 60초마다 갱신됩니다.
 */
const LiveStats: React.FC = () => {
  // 무작위 값 생성기 (active: 50-200, improved: 30-70)
  const randomStats = (): Stats => ({
    active: Math.floor(Math.random() * 151) + 50, // 0-150 → 50-200
    improved: Math.floor(Math.random() * 41) + 30, // 0-40 → 30-70
  });

  const [stats, setStats] = useState<Stats>(randomStats());

  useEffect(() => {
    // 60초마다 새로운 무작위 통계로 갱신
    const id = setInterval(() => setStats(randomStats()), 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      aria-live="polite"
      className="inline-flex items-center gap-2 rounded-full bg-white/70 dark:bg-black/40 px-4 py-1 text-sm font-medium text-text shadow backdrop-blur"
    >
      {/* user icon */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 24 24"
        className="h-4 w-4 text-primary"
      >
        <path d="M16 11c1.657 0 3-1.343 3-3S17.657 5 16 5s-3 1.343-3 3 1.343 3 3 3zm-8 0c1.657 0 3-1.343 3-3S9.657 5 8 5 5 6.343 5 8s1.343 3 3 3zm0 2c-2.673 0-8 1.337-8 4v3h8v-3c0-.697.123-1.366.343-2H0v-1.253C0 14.08 3.13 13 8 13zm8 0c4.87 0 8 1.08 8 2.747V17h-7.343c.22.634.343 1.303.343 2v3h8v-3c0-2.663-5.327-4-8-4z" />
      </svg>
      <span>
        현재 <b>{stats.active}</b>명 코칭 중 · 24h <b>{stats.improved}</b>명 실력 향상
      </span>
    </div>
  );
};

export default LiveStats; 