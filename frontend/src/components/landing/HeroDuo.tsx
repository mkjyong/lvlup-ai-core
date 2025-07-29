import React from 'react';
import LiveStatsHUD from './LiveStatsHUD';
import DuoChatPanel from './DuoChatPanel';
import { motion } from 'framer-motion';

const HeroDuo: React.FC = () => (
  <motion.section
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.8 }}
    className="relative isolate flex min-h-screen items-center justify-center overflow-hidden bg-black text-center text-white pt-28 lg:pt-0"
  >
    {/* Background video */}
    <video
      className="absolute inset-0 -z-20 h-full w-full object-cover opacity-40"
      src="/video/hero_bg.mp4"
      poster="/video/hero_bg.jpg"
      autoPlay
      muted
      loop
      playsInline
    />
    {/* radial overlay */}
    <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_600px_at_center,rgba(255,0,128,0.2)_0%,transparent_70%)]" />

    <LiveStatsHUD />

    <div className="z-10 w-full max-w-5xl space-y-8 px-4">
      <h1 className="text-6xl font-extrabold tracking-tight text-transparent bg-gradient-to-r from-[#6b7bff] via-[#ff22aa] to-[#6b7bff] bg-clip-text">
        Personal AI Game Coach
      </h1>
      <p className="mx-auto max-w-2xl text-lg text-muted">
        플레이 중 떠오르는 전략·교전·아이템 고민을 <span className="text-primary">LVLUP AI</span>가 즉시 해결해 드립니다. <br className="hidden md:inline" />
        <span className="text-white/90">AI와 함께 실시간으로 호흡하며 승리를 만들어가는 <strong className="text-primary">Co-Playing</strong> 경험을 지금 만나보세요.</span>
      </p>

      <DuoChatPanel />
    </div>
  </motion.section>
);

export default HeroDuo; 