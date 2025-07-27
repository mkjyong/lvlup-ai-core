import React from 'react';

interface Props {
  className?: string;
  children: React.ReactNode;
}

/**
 * 재사용 가능한 글래스모피즘 + 네온 글로우 카드.
 *  - 배경 투명도, 블러, 이중 링, 스캔라인 오버레이를 포함합니다.
 */
const GlassCard: React.FC<Props> = ({ className = '', children }) => (
  <div
    className={`relative overflow-hidden rounded-2xl bg-white/5 backdrop-blur-md ring-1 ring-inset ring-primary/40 shadow-[0_0_20px_-2px_theme(colors.primary/50)] ${className}`}
  >
    {/* scanline overlay */}
    <div className="pointer-events-none absolute inset-0 bg-[url('/textures/scanlines.png')] opacity-10" />
    <div className="relative z-10">{children}</div>
  </div>
);

export default GlassCard; 