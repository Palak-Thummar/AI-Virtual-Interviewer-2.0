import React, { useMemo, useState } from 'react';
import { Bell, ChevronDown, LogOut, Menu, UserCircle2 } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import styles from './Layout.module.css';

const titleMap = {
  '/dashboard': 'nav.dashboard',
  '/interviews': 'nav.interviews',
  '/company-prep': 'nav.companyPrep',
  '/career-intelligence': 'nav.careerIntelligence',
  '/analytics': 'nav.careerIntelligence',
  '/setup': 'common.startInterview',
  '/coding-practice': 'nav.codingPractice',
  '/answer-lab': 'nav.answerLab',
  '/resume-rewriter': 'nav.resumeRewriter',
  '/settings': 'nav.settings'
};

const resolveTitleKey = (pathname) => {
  if (pathname.startsWith('/interview/')) return 'nav.interviewSession';
  if (pathname.startsWith('/results/')) return 'nav.results';

  const direct = titleMap[pathname];
  if (direct) return direct;

  const firstSegment = `/${pathname.split('/').filter(Boolean)[0] || ''}`;
  return titleMap[firstSegment] || 'nav.workspace';
};

export const Topbar = ({ onOpenSidebar }) => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);

  const pageTitle = useMemo(() => t(resolveTitleKey(pathname)), [pathname, t]);

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
          <label className={styles.profileButton} style={{ gap: 8 }}>
            <span>{t('language.label')}</span>
            <select
              value={i18n.language}
              onChange={(event) => i18n.changeLanguage(event.target.value)}
              style={{ background: 'transparent', border: 'none', outline: 'none', color: 'inherit' }}
              aria-label={t('language.label')}
            >
              <option value="en">{t('language.english')}</option>
              <option value="hi">{t('language.hindi')}</option>
              <option value="es">{t('language.spanish')}</option>
            </select>
          </label>

          <button type="button" className={styles.iconButton} aria-label={t('common.notifications')}>
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
              <span>{user?.name || t('common.profile')}</span>
              <ChevronDown size={15} />
            </button>

            {menuOpen ? (
              <div className={styles.profileMenu}>
                <button type="button" className={styles.menuItem} onClick={handleLogout}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <LogOut size={15} />
                    {t('common.logout')}
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
