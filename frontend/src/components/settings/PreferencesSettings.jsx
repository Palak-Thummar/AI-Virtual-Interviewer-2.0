import React, { useMemo, useState } from 'react';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

const allQuestionTypes = ['mcq', 'coding', 'theory'];

export const PreferencesSettings = () => {
  const preferences = useSettingsStore((state) => state.preferences);
  const updatePreferences = useSettingsStore((state) => state.updatePreferences);

  const initial = useMemo(
    () => ({
      default_question_count: preferences?.default_question_count ?? 5,
      difficulty: preferences?.difficulty ?? 'medium',
      question_types: preferences?.question_types ?? ['mcq', 'coding'],
      include_dsa: preferences?.include_dsa ?? true,
      include_system_design: preferences?.include_system_design ?? false
    }),
    [preferences]
  );

  const [form, setForm] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const toggleType = (type) => {
    setForm((prev) => {
      const has = prev.question_types.includes(type);
      return {
        ...prev,
        question_types: has ? prev.question_types.filter((item) => item !== type) : [...prev.question_types, type]
      };
    });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage('');
      setError('');
      await updatePreferences(form);
      setMessage('Preferences updated successfully.');
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to update preferences');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>AI Interview Preferences</h2>
      <p className={styles.subtitle}>Control default interview generation behavior.</p>

      <div className={styles.grid}>
        <div className={styles.field}>
          <label>Default Question Count</label>
          <input
            type="number"
            min={1}
            max={20}
            className={styles.input}
            value={form.default_question_count}
            onChange={(event) =>
              setForm((prev) => ({
                ...prev,
                default_question_count: Number(event.target.value || 1)
              }))
            }
          />
        </div>

        <div className={styles.field}>
          <label>Difficulty</label>
          <select
            className={styles.select}
            value={form.difficulty}
            onChange={(event) => setForm((prev) => ({ ...prev, difficulty: event.target.value }))}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
      </div>

      <div className={styles.field}>
        <label>Question Types</label>
        <div className={styles.grid}>
          {allQuestionTypes.map((type) => (
            <label key={type} className={styles.checkRow}>
              <input
                type="checkbox"
                checked={form.question_types.includes(type)}
                onChange={() => toggleType(type)}
              />
              <span>{type.toUpperCase()}</span>
            </label>
          ))}
        </div>
      </div>

      <div className={styles.grid}>
        <label className={styles.checkRow}>
          <input
            type="checkbox"
            checked={form.include_dsa}
            onChange={(event) => setForm((prev) => ({ ...prev, include_dsa: event.target.checked }))}
          />
          <span>Include DSA</span>
        </label>
        <label className={styles.checkRow}>
          <input
            type="checkbox"
            checked={form.include_system_design}
            onChange={(event) => setForm((prev) => ({ ...prev, include_system_design: event.target.checked }))}
          />
          <span>Include System Design</span>
        </label>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </section>
  );
};

export default PreferencesSettings;
