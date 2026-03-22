import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const PrivacySettings = ({ onAccountDeleted }) => {
  const { t } = useTranslation();
  const deleteAccount = useSettingsStore((state) => state.deleteAccount);

  const [loadingDelete, setLoadingDelete] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleDelete = async () => {
    if (confirmText !== 'DELETE') {
      setError(t('settings.privacy.typeDelete'));
      return;
    }

    try {
      setLoadingDelete(true);
      setError('');
      await deleteAccount();
      onAccountDeleted?.();
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to delete account');
    } finally {
      setLoadingDelete(false);
    }
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.title}>{t('settings.privacy.deleteAccount')}</h2>
      <p className={styles.subtitle}>{t('settings.privacy.confirmText')}</p>

      <div className={styles.actions} style={{ justifyContent: 'flex-start' }}>
        <button type="button" className={styles.dangerButton} onClick={() => setShowModal(true)}>
          {t('settings.privacy.deleteAccount')}
        </button>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      {showModal ? (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>
            <h3 className={styles.title}>{t('settings.privacy.confirmTitle')}</h3>
            <p className={styles.note}>{t('settings.privacy.confirmText')}</p>
            <input
              className={styles.input}
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
              placeholder={t('settings.privacy.placeholder')}
            />
            <div className={styles.actions}>
              <button type="button" className={styles.secondaryButton} onClick={() => setShowModal(false)}>
                {t('common.cancel')}
              </button>
              <button type="button" className={styles.dangerButton} onClick={handleDelete} disabled={loadingDelete}>
                {loadingDelete ? t('settings.privacy.deleting') : t('settings.privacy.deleteConfirm')}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
};

export default PrivacySettings;
