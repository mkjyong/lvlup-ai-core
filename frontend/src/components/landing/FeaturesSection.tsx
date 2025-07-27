import React from 'react';
import { FaChartLine, FaComments, FaCheckCircle } from 'react-icons/fa';

const features = [
  {
    icon: <FaChartLine size={32} />,
    title: '데이터 기반 맞춤 분석',
    desc: '수백 판의 게임 기록을 AI가 분석하여 당신만의 승리 공식을 찾아냅니다.',
  },
  {
    icon: <FaComments size={32} />,
    title: '1:1 대화형 코칭',
    desc: '내 플레이에 대해 AI 코치와 편하게 대화하며 답을 찾으세요.',
  },
  {
    icon: <FaCheckCircle size={32} />,
    title: '실천 가능한 액션 플랜',
    desc: '매 게임 성장할 수 있는 명확한 목표를 제시합니다.',
  },
];

const FeaturesSection: React.FC = () => (
  <section className="relative bg-gradient-to-b from-surface/50 to-bg py-24">
    <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0,rgba(255,255,255,0.15),transparent)]" />
    <div className="mx-auto max-w-screen-lg px-4">
      <h2 className="mb-16 text-center text-3xl font-extrabold text-text sm:text-4xl">
        LVLUP AI만의 <span className="text-primary">핵심 기능</span>
      </h2>
      <div className="grid gap-10 sm:grid-cols-2 md:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-md transition-transform duration-300 hover:-translate-y-1 hover:shadow-xl"
          >
            <div className="mb-6 flex justify-center text-3xl text-secondary transition-colors group-hover:text-primary">
              {f.icon}
            </div>
            <h3 className="mb-3 text-center text-xl font-semibold text-text">{f.title}</h3>
            <p className="text-center text-sm text-muted">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export default FeaturesSection; 