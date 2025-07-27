import React from 'react';
import { Link } from 'react-router-dom';

const HeroSection: React.FC = () => (
  <section className="relative isolate overflow-hidden bg-gradient-to-b from-bg via-surface to-bg">
    {/* Decorative gradient blob */}
    <div
      className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[120%] w-[120%] -translate-x-1/2 rotate-45 transform bg-gradient-to-r from-primary/30 via-secondary/40 to-primary/30 opacity-30 blur-3xl" />

    <div className="mx-auto flex min-h-[80vh] max-w-screen-lg flex-col items-center justify-center px-6 pt-28 pb-20 text-center">
      <h1
        className="bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text font-extrabold text-transparent drop-shadow-md"
        style={{ fontSize: 'clamp(2.5rem,6vw,4.5rem)' }}
      >
        당신의 잠재력을 깨우는
        <br className="hidden sm:block" /> AI 게임 코치
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-muted sm:text-xl">
        게임 데이터를 분석하여 실력을 <span className="font-semibold text-text">즉시</span> 끌어올려 보세요.
      </p>
      <Link
        to="/auth"
        className="mt-10 inline-flex items-center gap-2 rounded-full bg-primary px-8 py-4 text-sm font-semibold text-bg shadow-lg transition-transform hover:-translate-y-0.5 hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50"
      >
        무료로 시작하기
      </Link>

      {/* Scroll indicator */}
      <div className="mt-20 flex motion-safe:animate-bounce flex-col items-center text-muted/60">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M12 16.5l-8-8 1.41-1.42L12 13.66l6.59-6.58L20 8.5z" />
        </svg>
        <span className="mt-1 text-xs">더 알아보기</span>
      </div>
    </div>
  </section>
);

export default HeroSection; 