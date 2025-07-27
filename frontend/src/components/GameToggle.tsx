import React from 'react';
import { FaGamepad } from 'react-icons/fa';

interface Props {
  value: string;
  onChange: (val: string) => void;
}

const games = ['general', 'lol', 'pubg'];

const GameToggle: React.FC<Props> = ({ value, onChange }) => (
  <div className="flex space-x-2">
    {games.map((g) => (
      <button
        key={g}
        type="button"
        className={`flex items-center space-x-1 rounded px-3 py-1 text-sm uppercase transition-colors ${
          value === g ? 'bg-secondary text-bg' : 'bg-surface text-text'
        }`}
        onClick={() => onChange(g)}
      >
        <FaGamepad />
        <span>{g === 'general' ? 'ALL' : g === 'pubg' ? '배그' : g.toUpperCase()}</span>
      </button>
    ))}
  </div>
);

export default GameToggle; 