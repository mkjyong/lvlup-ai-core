import React from 'react';
import { Link } from 'react-router-dom';

const CTASection: React.FC = () => (
  <section className="relative isolate overflow-hidden bg-gradient-to-r from-primary via-secondary to-primary py-24 text-center text-bg">
    <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.2),transparent)]" />
    <h2 className="mb-8 text-4xl font-extrabold sm:text-5xl">이제 당신 차례입니다</h2>
    <p className="mx-auto mb-12 max-w-2xl text-lg opacity-95">
      지금 바로 AI 코칭을 경험하고 스마트한 게이머로 거듭나세요!
    </p>
    <Link
      to="/auth"
      className="inline-flex items-center gap-2 rounded-full bg-bg px-10 py-4 text-base font-semibold text-primary shadow-lg transition-transform hover:-translate-y-0.5 hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-bg/50"
    >
      무료로 시작하기
    </Link>
  </section>
);

export default CTASection; 