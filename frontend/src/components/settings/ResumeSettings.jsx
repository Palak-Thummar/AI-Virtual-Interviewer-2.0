import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const ResumeSettings = () => {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);
  const resume = useSettingsStore((state) => state.resume);
  const uploadResume = useSettingsStore((state) => state.uploadResume);
  const deleteResume = useSettingsStore((state) => state.deleteResume);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFile = async (file) => {
    if (!file) return;
    try {
      setLoading(true);
      setMessage('');
      setError('');
      await uploadResume(file);
      setMessage(t('settings.resume.uploadSuccess'));
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    await handleFile(file);
  };

  const handleDelete = async () => {
    try {
      setLoading(true);
      setMessage('');
      setError('');
      await deleteResume();
      setMessage(t('settings.resume.deleteSuccess'));
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to delete resume');
    } finally {
      setLoading(false);
    }
  };

  const uploadedAt = resume?.uploaded_at ? new Date(resume.uploaded_at).toLocaleString() : '-';

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t('settings.resume.title')}</h2>
      <p className={styles.subtitle}>{t('settings.resume.subtitle')}</p>

      <input
        ref={fileInputRef}
        type="file"
        className={styles.fileInput}
        accept=".pdf,.docx"
        style={{ display: 'none' }}
        onChange={(event) => handleFile(event.target.files?.[0])}
      />

      <div
        className={styles.dropZone}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') fileInputRef.current?.click();
        }}
      >
        {t('settings.resume.dropzone')}
      </div>

      <div className={styles.grid}>
        <div className={styles.field}>
          <label>{t('settings.resume.fileName')}</label>
          <input className={styles.input} value={resume?.file_name || '-'} disabled />
        </div>
        <div className={styles.field}>
          <label>{t('settings.resume.lastUpdated')}</label>
          <input className={styles.input} value={uploadedAt} disabled />
        </div>
      </div>

      <div className={styles.field}>
        <label>{t('settings.resume.extractedSkills')}</label>
        <div className={styles.skillWrap}>
          {(resume?.extracted_skills || []).map((skill) => (
            <span key={skill} className={styles.skillTag}>
              {skill}
            </span>
          ))}
          {(resume?.extracted_skills || []).length === 0 ? <span className={styles.note}>{resume?.file_name ? t('settings.resume.noSkills') : t('settings.resume.empty')}</span> : null}
        </div>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      <div className={styles.actions}>
        <button type="button" className={styles.secondaryButton} onClick={() => fileInputRef.current?.click()} disabled={loading}>
          {t('settings.resume.replace')}
        </button>
        <button type="button" className={styles.dangerButton} onClick={handleDelete} disabled={loading}>
          {t('settings.resume.delete')}
        </button>
      </div>
    </section>
  );
};

export default ResumeSettings;
