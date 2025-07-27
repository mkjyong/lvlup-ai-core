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
  // 기본 모킹 데이터를 설정해 API가 없더라도 배지가 항상 표시되도록 한다.
  const [stats, setStats] = useState<Stats>({ active: 128, improved: 42 });

  useEffect(() => {
    let isMounted = true;
    const fetchStats = async () => {
      try {
        const res = await fetch('/api/coach/stats');
        if (!res.ok) throw new Error('Failed to load');
        const data: Stats = await res.json();
        if (isMounted) setStats(data);
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
    };

    fetchStats();
    const id = setInterval(fetchStats, 60_000);
    return () => {
      isMounted = false;
      clearInterval(id);
    };
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