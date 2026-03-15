import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const NotificationSettings = () => {
  const { t } = useTranslation();
  const notifications = useSettingsStore((state) => state.notifications);
  const updateNotifications = useSettingsStore((state) => state.updateNotifications);

  const initial = useMemo(
    () => ({
      email_notifications: notifications?.email_notifications ?? true,
      interview_reminders: notifications?.interview_reminders ?? true,
      weekly_summary: notifications?.weekly_summary ?? true,
      skill_suggestions: notifications?.skill_suggestions ?? true
    }),
    [notifications]
  );

  const [form, setForm] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage('');
      setError('');
      await updateNotifications(form);
      setMessage(t('settings.notifications.saved'));
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to update notifications');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t('settings.notifications.title')}</h2>
      <p className={styles.subtitle}>{t('settings.notifications.subtitle')}</p>

      <label className={styles.checkRow}>
        <input
          type="checkbox"
          checked={form.email_notifications}
          onChange={(event) => setForm((prev) => ({ ...prev, email_notifications: event.target.checked }))}
        />
        <span>{t('settings.notifications.email')}</span>
      </label>

      <label className={styles.checkRow}>
        <input
          type="checkbox"
          checked={form.interview_reminders}
          onChange={(event) => setForm((prev) => ({ ...prev, interview_reminders: event.target.checked }))}
        />
        <span>{t('settings.notifications.reminders')}</span>
      </label>

      <label className={styles.checkRow}>
        <input
          type="checkbox"
          checked={form.weekly_summary}
          onChange={(event) => setForm((prev) => ({ ...prev, weekly_summary: event.target.checked }))}
        />
        <span>{t('settings.notifications.weekly')}</span>
      </label>

      <label className={styles.checkRow}>
        <input
          type="checkbox"
          checked={form.skill_suggestions}
          onChange={(event) => setForm((prev) => ({ ...prev, skill_suggestions: event.target.checked }))}
        />
        <span>{t('settings.notifications.skills')}</span>
      </label>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave} disabled={saving}>
          {saving ? t('settings.notifications.saving') : t('settings.notifications.save')}
        </button>
      </div>
    </section>
  );
};

export default NotificationSettings;
