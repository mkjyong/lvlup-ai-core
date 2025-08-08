import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import LanguageSwitcher from '../ui/LanguageSwitcher';
import { useTranslation } from 'react-i18next';

const Header: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-20 w-full bg-black/40 backdrop-blur-md">
      <div className="mx-auto flex max-w-screen-lg items-center justify-between px-4 py-4">
        <Link
          to="/"
          className="bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text font-display text-2xl font-extrabold text-transparent"
        >
          LVLUP AI
        </Link>
        <div className="flex items-center gap-3 ml-auto">
          <Link
            to={isAuthenticated ? '/chat' : '/auth'}
            className="rounded-full border border-primary px-5 py-2 text-sm font-semibold text-primary transition-colors hover:bg-primary hover:text-bg"
          >
            {isAuthenticated ? t('header.dashboard') : t('header.login')}
          </Link>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
};

export default Header; 