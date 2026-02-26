import React, { useMemo, useState } from 'react';
import { Bell, ChevronDown, LogOut, Menu, UserCircle2 } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './Layout.module.css';

const titleMap = {
  '/dashboard': 'Dashboard',
  '/interviews': 'Interview History',
  '/company-prep': 'Company Interview Prep',
  '/analytics': 'Career Intelligence',
  '/setup': 'Interview Setup',
  '/coding-practice': 'Coding Practice',
  '/answer-lab': 'Answer Lab',
  '/resume-rewriter': 'Resume Rewriter',
  '/settings': 'Settings'
};

const resolveTitle = (pathname) => {
  if (pathname.startsWith('/interview/')) return 'Interview Session';
  if (pathname.startsWith('/results/')) return 'Answer Lab';

  const direct = titleMap[pathname];
  if (direct) return direct;

  const firstSegment = `/${pathname.split('/').filter(Boolean)[0] || ''}`;
  return titleMap[firstSegment] || 'Workspace';
};

export const Topbar = ({ onOpenSidebar }) => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const pageTitle = useMemo(() => resolveTitle(pathname), [pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className={styles.topbar}>
      <div className={styles.topbarInner}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            type="button"
            className={`${styles.iconButton} ${styles.mobileToggle}`}
            onClick={onOpenSidebar}
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>
          <h1 className={styles.title}>{pageTitle}</h1>
        </div>

        <div className={styles.topbarActions}>
          <button type="button" className={styles.iconButton} aria-label="Notifications">
            <Bell size={17} />
          </button>

          <div className={styles.profileMenuWrap}>
            <button
              type="button"
              className={styles.profileButton}
              onClick={() => setMenuOpen((prev) => !prev)}
              aria-expanded={menuOpen}
            >
              <UserCircle2 size={17} />
              <span>{user?.name || 'Profile'}</span>
              <ChevronDown size={15} />
            </button>

            {menuOpen ? (
              <div className={styles.profileMenu}>
                <button type="button" className={styles.menuItem} onClick={handleLogout}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <LogOut size={15} />
                    Logout
                  </span>
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
};
