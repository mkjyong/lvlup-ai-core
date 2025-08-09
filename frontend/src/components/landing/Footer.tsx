import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const Footer: React.FC = () => {
  const { t } = useTranslation();
  return (
    <footer className="bg-surface border-t border-border py-6 text-center text-xs sm:text-sm text-muted">
      <div className="space-y-1">
        <p className="mb-1">© {new Date().getFullYear()} LVLUP AI. All Rights Reserved.</p>
        <p className="mb-2">
          <Link to="/terms" className="underline hover:text-text">{t('legal.terms')}</Link>
          <span className="mx-2">|</span>
          <Link to="/privacy" className="underline hover:text-text">{t('legal.privacy')}</Link>
        </p>
        <p className="mt-2">상호명: 비욘드퓨처 · 대표자명: 전민규 · 사업자등록번호: 132-32-00628</p>
        <p>사업장주소: 경기도 성남시 분당구 판교역로 109 B동 802호</p>
        <p>
          대표전화번호: <a href="tel:05060220360" className="underline hover:text-text">050-6022-0360</a>
          {' '}· 대표이메일: <a href="mailto:lvlupai.official@gmail.com" className="underline hover:text-text">lvlupai.official@gmail.com</a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;