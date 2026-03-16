import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  BarChart3,
  Code2,
  Building2,
  LayoutDashboard,
  MessageSquareText,
  FilePenLine,
  Settings,
  Bot,
  Rocket,
  Users
} from 'lucide-react';
import styles from './Layout.module.css';
import careerIQLogo from '../../assets/careeriq-logo.svg';

const navItems = [
  { label: 'nav.dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'nav.interviews', to: '/interviews', icon: Users },
  { label: 'nav.companyPrep', to: '/company-prep', icon: Building2 },
  { label: 'nav.careerIntelligence', to: '/career-intelligence', icon: BarChart3 },
  { label: 'Practice Center', to: '/practice-center', icon: Rocket },
  { label: 'AI Coach', to: '/ai-coach', icon: Bot },
  { label: 'nav.codingPractice', to: '/coding-practice', icon: Code2 },
  { label: 'nav.answerLab', to: '/answer-lab', icon: MessageSquareText },
  { label: 'nav.resumeRewriter', to: '/resume-rewriter', icon: FilePenLine },
  { label: 'nav.settings', to: '/settings', icon: Settings }
];

export const Sidebar = ({ isOpen, onNavigate }) => {
  const { t } = useTranslation();

  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ''}`}>
      <div className={styles.brand}>
        <img src={careerIQLogo} alt="CareerIQ" className={styles.brandLogo} />
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={`${item.label}-${item.to}`}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
              }
            >
              <Icon size={17} />
              <span>{t(item.label)}</span>
            </NavLink>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '8px 10px', color: '#94a3b8', fontSize: 12 }}>
        Powered by <strong style={{ color: '#cbd5e1', fontWeight: 600 }}>AI</strong>
      </div>
    </aside>
  );
};
