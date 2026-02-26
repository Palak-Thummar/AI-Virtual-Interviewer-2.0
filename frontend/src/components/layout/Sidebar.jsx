import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  BarChart3,
  Brain,
  Code2,
  Building2,
  LayoutDashboard,
  MessageSquareText,
  FilePenLine,
  Settings,
  Sparkles,
  Users
} from 'lucide-react';
import styles from './Layout.module.css';

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Interviews', to: '/interviews', icon: Users },
  { label: 'Company Prep', to: '/company-prep', icon: Building2 },
  { label: 'Career Intelligence', to: '/analytics', icon: BarChart3 },
  { label: 'Coding Practice', to: '/coding-practice', icon: Code2 },
  { label: 'Answer Lab', to: '/answer-lab', icon: MessageSquareText },
  { label: 'Resume Rewriter', to: '/resume-rewriter', icon: FilePenLine },
  { label: 'Settings', to: '/settings', icon: Settings }
];

export const Sidebar = ({ isOpen, onNavigate }) => {
  return (
    <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ''}`}>
      <div className={styles.brand}>
        <span className={styles.brandBadge}>
          <Sparkles size={18} />
        </span>
        <div>
          <p className={styles.brandTitle}>AI Interviewer</p>
          <p className={styles.brandSub}>SaaS Workspace</p>
        </div>
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
              <span>{item.label}</span>
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
