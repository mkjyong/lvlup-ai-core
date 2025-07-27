import React from 'react';
import LiveStats from './LiveStats';
import GlassCard from '../ui/GlassCard';

const LiveStatsHUD: React.FC = () => (
  <div className="absolute right-4 top-4 z-10">
    <GlassCard className="px-3 py-2 text-xs">
      <LiveStats />
    </GlassCard>
  </div>
);

export default LiveStatsHUD; 