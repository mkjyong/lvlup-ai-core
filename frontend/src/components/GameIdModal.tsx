import React, { useState } from 'react';
import Modal from './ui/Modal';
import { useGameIds } from '../hooks/useGameIds';
import toast from 'react-hot-toast';
import RegionSelector from './RegionSelector';

interface Props {
  open: boolean;
  game: 'lol' | 'pubg';
  onClose: () => void;
}

const GameIdModal: React.FC<Props> = ({ open, game, onClose }) => {
  const { updateGameIds } = useGameIds();
  const [accountId, setAccountId] = useState('');
  const [region, setRegion] = useState('KR');

  const handleSave = async () => {
    try {
      await updateGameIds({ [game]: { account_id: accountId, region: game === 'lol' ? region : undefined } });
      toast.success('저장되었습니다! 다시 요청해주세요');
      onClose();
    } catch {
      toast.error('저장 실패');
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <h2 className="mb-4 text-lg font-semibold text-accent">{game.toUpperCase()} 계정 연동</h2>
      <input
        type="text"
        value={accountId}
        onChange={(e) => setAccountId(e.target.value)}
        placeholder="게임 ID"
        className="mb-3 w-full rounded border border-border bg-bg p-2 text-sm"
      />
      {game === 'lol' && (
        <RegionSelector value={region} onChange={setRegion} />
      )}
      <button
        type="button"
        className="w-full rounded bg-primary py-2 text-sm font-semibold text-bg"
        onClick={handleSave}
        disabled={!accountId.trim()}
      >
        저장
      </button>
    </Modal>
  );
};

export default GameIdModal; 