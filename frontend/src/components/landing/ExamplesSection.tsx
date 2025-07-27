import React from 'react';

interface Example {
  id: number;
  title: string;
  description: string;
  image: string; // URL or path under public
  prompt: string;
}

const examples: Example[] = [
  {
    id: 1,
    title: '솔랭 마스터 탈출',
    description: '챔피언 픽/밴, 라인전 솔루션 제공',
    image: '/examples/lol_master.png',
    prompt: '탑 라인전에서 상대 도란쉴드 카밀 상대로 어떻게 이길 수 있을까?',
  },
  {
    id: 2,
    title: 'PUBG 치킨 메이커',
    description: '포지셔닝 & 교전 피드백',
    image: '/examples/pubg_chicken.png',
    prompt: '에란겔 마지막 원에서 3인 스쿼드일 때 유리한 포지션은?',
  },
  {
    id: 3,
    title: '팀 전략 코치',
    description: '팀원 역할 분석 및 전략 설계',
    image: '/examples/team_strategy.png',
    prompt: '3-1-1 운영 시 서포터 시야 장악 루트 알려줘',
  },
];

const ExamplesSection: React.FC = () => (
  <section className="bg-bg py-20">
    <div className="container mx-auto px-4">
      <h2 className="mb-12 text-center text-3xl font-extrabold text-text">실제 활용 사례</h2>
      <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {examples.map((ex) => (
          <article
            key={ex.id}
            className="group relative overflow-hidden rounded-2xl bg-surface shadow-lg transition-transform hover:-translate-y-1"
          >
            <img src={ex.image} alt={ex.title} className="h-48 w-full object-cover transition-opacity group-hover:opacity-90" />
            <div className="p-6">
              <h3 className="mb-2 text-xl font-semibold text-text">{ex.title}</h3>
              <p className="mb-4 text-sm text-muted">{ex.description}</p>
              <button
                type="button"
                className="rounded bg-primary/90 px-4 py-2 text-xs font-semibold text-bg transition-colors hover:bg-primary"
                onClick={() => {
                  // Emit custom event to fill HeroChat input
                  document.dispatchEvent(new CustomEvent('fillPrompt', { detail: ex.prompt }));
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                이 프롬프트 사용하기 →
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  </section>
);

export default ExamplesSection; 