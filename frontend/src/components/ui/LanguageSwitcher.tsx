import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

    const current = i18n.language.startsWith('ko') ? 'ko' : 'en';

  const toggle = () => {
    void i18n.changeLanguage(current === 'ko' ? 'en' : 'ko');
  };

  const label = current === 'ko' ? 'KO' : 'EN';

  return (
    <button
      type="button"
      onClick={toggle}
      className="ml-2 rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted transition-colors hover:border-primary hover:text-primary"
      aria-label="Change language"
    >
      {label}
    </button>
  );
};

export default LanguageSwitcher;
