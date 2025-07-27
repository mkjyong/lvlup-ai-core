import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
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

  return (
    <div className="flex h-screen flex-col bg-bg text-text">
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
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