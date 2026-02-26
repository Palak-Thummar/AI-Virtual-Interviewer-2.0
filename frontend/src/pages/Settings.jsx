import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSettingsStore } from '../store/settingsStore';
import { ProfileSettings } from '../components/settings/ProfileSettings';
import { SecuritySettings } from '../components/settings/SecuritySettings';
import { PreferencesSettings } from '../components/settings/PreferencesSettings';
import { ResumeSettings } from '../components/settings/ResumeSettings';
import { NotificationSettings } from '../components/settings/NotificationSettings';
import { PrivacySettings } from '../components/settings/PrivacySettings';
import styles from './Settings.module.css';

const sections = [
  { key: 'profile', label: 'Profile' },
  { key: 'security', label: 'Security' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'resume', label: 'Resume' },
  { key: 'notifications', label: 'Notifications' },
  { key: 'privacy', label: 'Data & Privacy' }
];

export const SettingsPage = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [activeSection, setActiveSection] = useState('profile');
  const { loadSettings, loading, error } = useSettingsStore();

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleAccountDeleted = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const renderSection = () => {
    if (activeSection === 'profile') return <ProfileSettings />;
    if (activeSection === 'security') return <SecuritySettings />;
    if (activeSection === 'preferences') return <PreferencesSettings />;
    if (activeSection === 'resume') return <ResumeSettings />;
    if (activeSection === 'notifications') return <NotificationSettings />;
    return <PrivacySettings onAccountDeleted={handleAccountDeleted} />;
  };

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Settings</h1>
        <p>Manage your profile, security, interview preferences, and privacy controls</p>
      </header>

      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          {sections.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setActiveSection(item.key)}
              className={`${styles.menuItem} ${activeSection === item.key ? styles.menuItemActive : ''}`}
            >
              {item.label}
            </button>
          ))}
        </aside>

        <main className={styles.panel}>
          {loading ? <div className={styles.stateBox}>Loading settings...</div> : null}
          {!loading && error ? <div className={styles.stateError}>{error}</div> : null}
          {!loading && !error ? renderSection() : null}
        </main>
      </div>
    </section>
  );
};

export default SettingsPage;
