import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const Header: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-20 w-full bg-black/40 backdrop-blur-md">
      <div className="mx-auto flex max-w-screen-lg items-center justify-between px-4 py-4">
        <Link
          to="/"
          className="bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text font-display text-2xl font-extrabold text-transparent"
        >
          LVLUP AI
        </Link>
        <Link
          to={isAuthenticated ? '/chat' : '/auth'}
          className="rounded-full border border-primary px-5 py-2 text-sm font-semibold text-primary transition-colors hover:bg-primary hover:text-bg"
        >
          {isAuthenticated ? '대시보드' : '로그인 / 회원가입'}
        </Link>
      </div>
    </header>
  );
};

export default Header; 