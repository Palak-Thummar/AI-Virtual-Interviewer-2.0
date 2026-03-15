import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const SecuritySettings = () => {
  const { t } = useTranslation();
  const changePassword = useSettingsStore((state) => state.changePassword);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSave = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError(t('settings.security.validation.required'));
      return;
    }
    if (newPassword.length < 8) {
      setError(t('settings.security.validation.length'));
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(t('settings.security.validation.match'));
      return;
    }

    try {
      setLoading(true);
      setMessage('');
      setError('');
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setMessage(t('settings.security.saved'));
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t('settings.security.title')}</h2>
      <p className={styles.subtitle}>{t('settings.security.subtitle')}</p>

      <div className={styles.field}>
        <label>{t('settings.security.currentPassword')}</label>
        <input
          type="password"
          className={styles.input}
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
        />
      </div>

      <div className={styles.grid}>
        <div className={styles.field}>
          <label>{t('settings.security.newPassword')}</label>
          <input
            type="password"
            className={styles.input}
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
        </div>
        <div className={styles.field}>
          <label>{t('settings.security.confirmPassword')}</label>
          <input
            type="password"
            className={styles.input}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
        </div>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave} disabled={loading}>
          {loading ? t('settings.security.saving') : t('settings.security.save')}
        </button>
      </div>
    </section>
  );
};

export default SecuritySettings;
