import React, { useState } from 'react';
import { useGameIds } from '../hooks/useGameIds';
import { FaGamepad } from 'react-icons/fa';
import toast from 'react-hot-toast';
import RegionSelector from './RegionSelector';

const games: Array<{ key: string; label: string }> = [
  { key: 'lol', label: 'LoL' },
  { key: 'pubg', label: 'PUBG' },
];

const GameAccountSection: React.FC = () => {
  const { data: gameIds, isLoading, updateGameIds } = useGameIds();
  const [form, setForm] = useState<Record<string, { account_id: string; region?: string }>>({});

  if (isLoading && !gameIds) return <div>Loading...</div>;

  const current = gameIds ?? {};

  const handleChange = (game: string, field: string, value: string) => {
    setForm((prev) => ({
      ...prev,
      [game]: { ...prev[game], [field]: value },
    }));
  };

  const handleSave = async () => {
    try {
      await updateGameIds(form);
      toast.success('게임 계정이 저장되었습니다');
      setForm({});
    } catch (e) {
      toast.error('저장 실패');
    }
  };

  return (
    <div className="relative z-20 rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-soft">
      <div className="mb-4 flex items-center gap-2 text-lg font-semibold">
        <FaGamepad className="text-accent" /> <span>게임 계정 연동</span>
      </div>
      <div className="space-y-4">
        {games.map(({ key, label }) => (
          <div key={key} className="flex flex-col gap-1">
            <label className="text-sm font-medium text-accent/80" htmlFor={`${key}-id`}>
              {label} ID
            </label>
            <input
              id={`${key}-id`}
              type="text"
              defaultValue={current[key]?.account_id ?? ''}
              onChange={(e) => handleChange(key, 'account_id', e.target.value)}
              placeholder="소환사명 / 플레이어ID"
              className="rounded-md bg-bg border border-border px-3 py-2 text-sm"
            />
            {key === 'lol' && (
              <RegionSelector
                value={current[key]?.region ?? 'KR'}
                onChange={(val) => handleChange(key, 'region', val)}
              />
            )}
          </div>
        ))}
      </div>
      <button
        className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-bg hover:bg-primary/80"
        onClick={handleSave}
        type="button"
      >
        저장
      </button>
    </div>
  );
};

export default GameAccountSection; 