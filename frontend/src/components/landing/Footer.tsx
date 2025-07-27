import React from 'react';

const Footer: React.FC = () => (
  <footer className="bg-surface py-6 text-center text-sm text-muted">
    © {new Date().getFullYear()} LVLUP AI. All Rights Reserved.
  </footer>
);

export default Footer; 