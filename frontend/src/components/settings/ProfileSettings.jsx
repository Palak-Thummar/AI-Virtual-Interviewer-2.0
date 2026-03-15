import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const ProfileSettings = () => {
  const { t } = useTranslation();
  const profile = useSettingsStore((state) => state.profile);
  const updateProfile = useSettingsStore((state) => state.updateProfile);

  const initial = useMemo(
    () => ({
      full_name: profile?.full_name || '',
      email: profile?.email || '',
      primary_role: profile?.primary_role || '',
      experience_level: profile?.experience_level || ''
    }),
    [profile]
  );

  const [form, setForm] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setMessage('');
      await updateProfile(form);
      setMessage(t('settings.profile.saved'));
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t('settings.profile.title')}</h2>
      <p className={styles.subtitle}>{t('settings.profile.subtitle')}</p>

      <div className={styles.grid}>
        <div className={styles.field}>
          <label>{t('settings.profile.fullName')}</label>
          <input
            className={styles.input}
            value={form.full_name}
            onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
          />
        </div>
        <div className={styles.field}>
          <label>{t('settings.profile.email')}</label>
          <input className={styles.input} value={form.email} disabled />
        </div>
        <div className={styles.field}>
          <label>{t('settings.profile.primaryRole')}</label>
          <input
            className={styles.input}
            value={form.primary_role}
            onChange={(event) => setForm((prev) => ({ ...prev, primary_role: event.target.value }))}
            placeholder={t('settings.profile.primaryRole')}
          />
        </div>
        <div className={styles.field}>
          <label>{t('settings.profile.experienceLevel')}</label>
          <input
            className={styles.input}
            value={form.experience_level}
            onChange={(event) => setForm((prev) => ({ ...prev, experience_level: event.target.value }))}
            placeholder={t('settings.profile.experienceLevel')}
          />
        </div>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave} disabled={saving}>
          {saving ? t('settings.profile.saving') : t('settings.profile.save')}
        </button>
      </div>
    </section>
  );
};

export default ProfileSettings;
