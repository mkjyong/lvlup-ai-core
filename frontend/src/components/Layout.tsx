import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaComments, FaHistory, FaChartLine, FaCreditCard, FaCog } from 'react-icons/fa';

const navItems = [
  { to: '/chat', label: '챗', icon: <FaComments size={20} /> },
  { to: '/history', label: '히스토리', icon: <FaHistory size={20} /> },
  { to: '/dashboard/performance', label: '대시보드', icon: <FaChartLine size={20} /> },
  { to: '/billing', label: '구독', icon: <FaCreditCard size={20} /> },
  { to: '/settings', label: '설정', icon: <FaCog size={20} /> },
];

const Layout: React.FC = () => {
  const location = useLocation();
  const hideNav = location.pathname.startsWith('/onboarding');

  const { t } = useTranslation();
  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      {/* 사업자 정보 (작게 표기) */}
      <footer className="bg-surface border-t border-border px-3 py-2 text-center text-[10px] sm:text-xs text-muted">
        <div className="space-y-0.5">
          <p className="mb-0.5">
            <Link to="/terms" className="underline hover:text-text">{t('legal.terms')}</Link>
            <span className="mx-1">|</span>
            <Link to="/privacy" className="underline hover:text-text">{t('legal.privacy')}</Link>
          </p>
          <p>상호명: 비욘드퓨처 · 대표자명: 전민규 · 사업자등록번호: 132-32-00628</p>
          <p>사업장주소: 경기도 성남시 분당구 판교역로 109 B동 802호</p>
          <p>
            대표전화번호: <a href="tel:05060220360" className="underline hover:text-text">050-6022-0360</a>
            {' '}· 대표이메일: <a href="mailto:lvlupai.official@gmail.com" className="underline hover:text-text">lvlupai.official@gmail.com</a>
          </p>
        </div>
      </footer>
      {!hideNav && (
        <nav className="flex h-14 items-center justify-around border-t border-border bg-surface">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center text-xs ${isActive ? 'text-primary' : 'text-muted'}`
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
};

export default Layout; 