import React, { useMemo, useState } from 'react';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const ProfileSettings = () => {
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
      setMessage('Profile updated successfully.');
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>Profile Management</h2>
      <p className={styles.subtitle}>Update your personal and professional details.</p>

      <div className={styles.grid}>
        <div className={styles.field}>
          <label>Full Name</label>
          <input
            className={styles.input}
            value={form.full_name}
            onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
          />
        </div>
        <div className={styles.field}>
          <label>Email</label>
          <input className={styles.input} value={form.email} disabled />
        </div>
        <div className={styles.field}>
          <label>Primary Role</label>
          <input
            className={styles.input}
            value={form.primary_role}
            onChange={(event) => setForm((prev) => ({ ...prev, primary_role: event.target.value }))}
            placeholder="e.g. Java Developer"
          />
        </div>
        <div className={styles.field}>
          <label>Experience Level</label>
          <input
            className={styles.input}
            value={form.experience_level}
            onChange={(event) => setForm((prev) => ({ ...prev, experience_level: event.target.value }))}
            placeholder="e.g. Fresher"
          />
        </div>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </section>
  );
};

export default ProfileSettings;
