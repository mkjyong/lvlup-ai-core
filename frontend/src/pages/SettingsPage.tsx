import React from 'react';
import { useTheme } from '../hooks/useTheme';
import ReferralSection from '../components/ReferralSection';
import GameAccountSection from '../components/GameAccountSection';
import SubscriptionSection from '../components/SubscriptionSection';
import { FaPalette, FaUserFriends } from 'react-icons/fa';

const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <header className="border-b border-accent/50 p-4 text-xl font-display text-accent shadow-[0_1px_4px_rgba(0,255,149,0.1)]">설정</header>
      <main className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto grid max-w-screen-sm gap-6">
          {/* Theme card */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-soft">
            <div className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <FaPalette className="text-accent" /> <span>테마</span>
            </div>
            <button
              type="button"
              onClick={toggleTheme}
              aria-label="테마 전환"
              className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors ${theme==='dark' ? 'bg-primary' : 'bg-border'}`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-bg transition-transform ${theme==='dark' ? 'translate-x-7' : 'translate-x-1'}`}
              />
            </button>
          </div>

          {/* Game account card */}
          <GameAccountSection />
          {/* Subscription card */}
          <SubscriptionSection />
          {/* Referral card */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-soft">
            <div className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <FaUserFriends className="text-accent" /> <span>레퍼럴</span>
            </div>
            <ReferralSection />
          </div>
        </div>
      </main>
    </div>
  );
};

export default SettingsPage; 