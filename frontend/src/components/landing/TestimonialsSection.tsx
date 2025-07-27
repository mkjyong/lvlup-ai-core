import React from 'react';

const testimonials = [
  {
    quote:
      '퇴근 후 스트레스만 받던 게임이 즐거워졌어요. AI 코치가 콕 집어준 문제점을 고치니 연승하네요!',
    name: '김대리',
    info: '32, 마케터',
  },
  {
    quote:
      '제 플레이를 데이터로 보니 확실히 다르더군요. 막연했던 감 대신, 정확한 분석으로 실력을 올릴 수 있었습니다.',
    name: '최프로',
    info: '28, 개발자',
  },
  {
    quote:
      '친구들한테 더 이상 미안하지 않아요! AI 코치 덕분에 팀에 기여하는 플레이어가 됐습니다.',
    name: '박주임',
    info: '25, 신입사원',
  },
];

const TestimonialsSection: React.FC = () => (
  <section className="py-24">
    <div className="mx-auto max-w-screen-lg px-4">
      <h2 className="mb-16 text-center text-3xl font-extrabold sm:text-4xl">
        먼저 경험한 <span className="text-primary">유저들의 후기</span>
      </h2>
      <div className="grid gap-10 sm:grid-cols-2 md:grid-cols-3">
        {testimonials.map((t) => (
          <blockquote
            key={t.name}
            className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-md shadow-xl"
          >
            <p className="before:content-['“'] after:content-['”'] mb-6 text-base italic leading-relaxed text-text/90">
              {t.quote}
            </p>
            <footer className="text-sm font-semibold text-muted">
              {t.name} <span className="font-normal">/ {t.info}</span>
            </footer>
          </blockquote>
        ))}
      </div>
    </div>
  </section>
);

export default TestimonialsSection; 