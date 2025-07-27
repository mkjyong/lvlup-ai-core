import React from 'react';

interface Clip {
  id: number;
  title: string;
  video: string; // mp4 path
  poster: string; // jpg for poster
  prompt: string;
}

const clips: Clip[] = [
  {
    id: 1,
    title: 'LoL 1v3 아웃플레이',
    video: '/clips/lol_highlight.mp4',
    poster: '/clips/lol_highlight.jpg',
    prompt: '이 상황에서 상대 3명을 상대로 생존하려면?',
  },
  {
    id: 2,
    title: 'PUBG 클러치 치킨',
    video: '/clips/pubg_highlight.mp4',
    poster: '/clips/pubg_highlight.jpg',
    prompt: '마지막 원에서 어떻게 파이트해야 할까?',
  },
  {
    id: 3,
    title: '팀 교전 매크로',
    video: '/clips/team_macro.mp4',
    poster: '/clips/team_macro.jpg',
    prompt: '3:2 숫자 열세에서 이기는 교전 플랜은?',
  },
];

const HighlightReel: React.FC = () => (
  <section className="relative -mt-16 bg-[#0a0a0d] py-24 text-white">
    {/* top fade to connect previous section */}
    <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-transparent to-[#0a0a0d]" />
    <div className="container mx-auto px-4">
      <h2 className="mb-12 text-center text-4xl font-extrabold">하이라이트 리플레이</h2>
      <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {clips.map((c) => (
          <div key={c.id} className="group relative overflow-hidden rounded-2xl ring-1 ring-primary/40">
            <video
              src={c.video}
              poster={c.poster}
              muted
              loop
              playsInline
              className="h-56 w-full object-cover transition-opacity group-hover:opacity-80"
            />
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/60 opacity-0 transition-opacity group-hover:opacity-100">
              <h3 className="mb-4 text-xl font-semibold">{c.title}</h3>
              <button
                type="button"
                className="rounded bg-primary px-4 py-2 text-sm font-bold text-bg hover:bg-primary/90"
                onClick={() => {
                  document.dispatchEvent(new CustomEvent('fillPrompt', { detail: c.prompt }));
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                같은 상황 코칭 받기 →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

export default HighlightReel; 