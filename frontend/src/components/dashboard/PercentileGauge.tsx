import React from 'react';

interface Props {
  value: number; // 0-100
}

const PercentileGauge: React.FC<Props> = ({ value }) => {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value / 100);
  return (
    <svg width="100" height="100" className="mx-auto">
      <circle cx="50" cy="50" r={radius} stroke="#444" strokeWidth="8" fill="none" />
      <circle
        cx="50"
        cy="50"
        r={radius}
        stroke="#00FF99"
        strokeWidth="8"
        fill="none"
        strokeDasharray={`${circumference} ${circumference}`}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 50 50)"
      />
      <text x="50" y="55" textAnchor="middle" fill="#fff" fontSize="16" fontWeight="bold">
        {value}%
      </text>
    </svg>
  );
};

export default PercentileGauge; 