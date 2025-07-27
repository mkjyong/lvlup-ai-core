import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface Props {
  data: Array<[string, number]>; // [date, value]
  color?: string;
}

const TrendChart: React.FC<Props> = ({ data, color = '#00FF99' }) => {
  const chartData = data.map(([date, value]) => ({ date, value }));
  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} domain={[0, 'auto']} />
          <Tooltip contentStyle={{ backgroundColor: '#1f1f1f', border: 'none' }} />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart; 