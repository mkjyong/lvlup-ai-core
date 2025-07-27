import React, { useState } from 'react';
import RegionSelector from './RegionSelector';

interface Props {
  game: 'lol' | 'pubg';
  account?: { account_id: string; region?: string } | null;
  onSave: (data: { account_id: string; region?: string }) => Promise<void>;
}

const AccountBar: React.FC<Props> = ({ game, account, onSave }) => {
  const [editing, setEditing] = useState(!account);
  const [accountId, setAccountId] = useState(account?.account_id ?? '');
  const [region, setRegion] = useState(account?.region ?? 'KR');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    try {
      setSaving(true);
      await onSave({ account_id: accountId, region: game === 'lol' ? region : undefined });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  if (!editing) {
    return (
      <div className="flex items-center justify-between gap-2 rounded border border-border bg-surface px-3 py-2 text-xs">
        <span>
          {game.toUpperCase()} 계정: {account?.account_id}
          {game === 'lol' && account?.region ? ` (${account.region})` : ''}
        </span>
        <button
          type="button"
          className="rounded border border-border px-2 py-1 hover:bg-border"
          onClick={() => setEditing(true)}
        >
          수정
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-2 text-xs">
      <input
        className="w-1/2 min-w-[160px] rounded border border-border bg-bg px-3 py-2 text-sm"
        placeholder="게임 ID"
        value={accountId}
        onChange={(e) => setAccountId(e.target.value)}
        onBlur={() => {
          if (accountId.trim()) {
            handleSave();
          } else if (account) {
            // 기존 계정은 유지하되 편집 모드만 종료
            setEditing(false);
          } // 입력이 비어있고 기존 계정도 없다면 편집 상태 유지
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && accountId.trim()) {
            e.preventDefault();
            handleSave();
          }
          if (e.key === 'Escape') {
            setEditing(false);
          }
        }}
      />
      {game === 'lol' && (
        <div className="w-1/2 min-w-[160px]">
          <RegionSelector
            value={region}
            onChange={(val) => {
              setRegion(val);
              if (accountId.trim()) handleSave();
            }}
          />
        </div>
      )}
    </div>
  );
};

export default AccountBar; 