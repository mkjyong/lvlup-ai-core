import React, { useEffect, useState } from 'react';

const HoloAvatar: React.FC = () => {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const offsetX = (e.clientX - innerWidth / 2) / innerWidth;
      const offsetY = (e.clientY - innerHeight / 2) / innerHeight;
      setPos({ x: offsetX * 20, y: offsetY * 20 });
    };
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return (
    <img
      src="/avatar/ai_holo.png"
      alt="AI Avatar"
      style={{ transform: `translate3d(${pos.x}px, ${pos.y}px, 0)` }}
      className="pointer-events-none absolute bottom-8 right-8 w-32 select-none opacity-80 drop-shadow-[0_0_6px_#00e0ff]"
    />
  );
};

export default HoloAvatar; 