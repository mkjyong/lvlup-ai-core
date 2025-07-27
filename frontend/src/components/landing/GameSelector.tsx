import React, { useState, useRef, useEffect } from 'react';
import { FiChevronDown } from 'react-icons/fi';

interface Props {
  value: string;
  onChange: (val: string) => void;
}

const GAMES: Array<{ id: string; label: string; disabled?: boolean }> = [
  { id: '', label: '게임 선택', disabled: true },
  { id: 'lol', label: '리그 오브 레전드' },
  { id: 'pubg', label: '배틀그라운드' },
  { id: 'ow', label: '오버워치 (예정)', disabled: true },
  { id: 'valorant', label: '발로란트 (예정)', disabled: true },
];

const GameSelector: React.FC<Props> = ({ value, onChange }) => {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const current = GAMES.find((g) => g.id === value) ?? GAMES[0];

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-lg bg-[#0d0d10]/80 px-4 py-3 text-base text-white ring-1 ring-border transition focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <span className={current.disabled ? 'text-muted' : ''}>{current.label}</span>
        <FiChevronDown className="h-5 w-5 text-muted transition-colors group-focus:text-primary" />
      </button>

      {open && (
        <ul className="absolute z-50 mt-2 max-h-60 w-full overflow-y-auto rounded-lg bg-[#1b1b1f]/95 py-1 ring-1 ring-border backdrop-blur">
          {GAMES.filter((g) => g.id !== '').map((g) => (
            <li key={g.id}>
              <button
                type="button"
                disabled={g.disabled}
                onClick={() => {
                  if (!g.disabled) {
                    onChange(g.id);
                    setOpen(false);
                  }
                }}
                className={`flex w-full items-center px-4 py-2 text-left text-base transition hover:bg-primary/10 disabled:cursor-not-allowed disabled:text-muted ${
                  value === g.id ? 'font-semibold text-primary' : ''
                }`}
              >
                {g.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default GameSelector; 