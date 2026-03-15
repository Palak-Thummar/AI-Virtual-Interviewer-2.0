import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
  { key: 'profile', label: 'settings.sections.profile' },
  { key: 'security', label: 'settings.sections.security' },
  { key: 'preferences', label: 'settings.sections.preferences' },
  { key: 'resume', label: 'settings.sections.resume' },
  { key: 'notifications', label: 'settings.sections.notifications' },
  { key: 'privacy', label: 'settings.sections.privacy' }
];

export const SettingsPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { logout } = useAuth();
  const [activeSection, setActiveSection] = useState(searchParams.get('section') || 'profile');
  const { loadSettings, loading, error } = useSettingsStore();

  useEffect(() => {
    const section = searchParams.get('section');
    if (section && sections.some((item) => item.key === section)) {
      setActiveSection(section);
    }
  }, [searchParams]);

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
        <h1>{t('settings.title')}</h1>
        <p>{t('settings.subtitle')}</p>
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
                {t(item.label)}
            </button>
          ))}
        </aside>

        <main className={styles.panel}>
            {loading ? <div className={styles.stateBox}>{t('settings.loading')}</div> : null}
          {!loading && error ? <div className={styles.stateError}>{error}</div> : null}
          {!loading && !error ? renderSection() : null}
        </main>
      </div>
    </section>
  );
};

export default SettingsPage;
