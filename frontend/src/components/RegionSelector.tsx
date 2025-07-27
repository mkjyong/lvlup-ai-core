import React, { useEffect, useRef, useState } from 'react';
import { FiChevronDown } from 'react-icons/fi';

interface Props {
  value: string;
  onChange: (val: string) => void;
}

const REGIONS: Array<{ code: string; name: string }> = [
  { code: 'KR', name: 'Korea' },
  { code: 'JP1', name: 'Japan' },
  { code: 'NA1', name: 'North America' },
  { code: 'EUW1', name: 'EU West' },
  { code: 'EUN1', name: 'EU Nordic & East' },
  { code: 'BR1', name: 'Brazil' },
  { code: 'LA1', name: 'LAN' },
  { code: 'LA2', name: 'LAS' },
  { code: 'OC1', name: 'Oceania' },
  { code: 'RU', name: 'Russia' },
  { code: 'TR1', name: 'Turkey' },
];

const RegionSelector: React.FC<Props> = ({ value, onChange }) => {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const current = REGIONS.find((r) => r.code === value) ?? REGIONS[0];

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-md bg-bg px-3 py-2 text-sm text-white ring-1 ring-border transition focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <span>{current.code ? `${current.code} – ${current.name}` : '서버 선택'}</span>
        <FiChevronDown className="h-4 w-4 text-muted" />
      </button>
      {open && (
        <ul className="absolute z-[1000] mt-1 max-h-60 w-full overflow-y-auto rounded-md bg-bg py-1 ring-1 ring-border backdrop-blur">
          {REGIONS.map((r) => (
            <li key={r.code}>
              <button
                type="button"
                onClick={() => {
                  onChange(r.code);
                  setOpen(false);
                }}
                className={`flex w-full items-center px-3 py-2 text-left text-sm transition hover:bg-primary/10 ${
                  value === r.code ? 'font-semibold text-primary' : ''
                }`}
              >
                {r.code} – {r.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RegionSelector; 