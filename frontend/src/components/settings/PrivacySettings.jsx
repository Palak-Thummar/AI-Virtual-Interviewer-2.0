import React, { useState } from 'react';
import { useSettingsStore } from '../../store/settingsStore';
import styles from './SettingsSections.module.css';

export const PrivacySettings = ({ onAccountDeleted }) => {
  const exportData = useSettingsStore((state) => state.exportData);
  const deleteAccount = useSettingsStore((state) => state.deleteAccount);

  const [loadingExport, setLoadingExport] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleExport = async () => {
    try {
      setLoadingExport(true);
      setMessage('');
      setError('');
      const data = await exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'my-account-data.json';
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage('Data export downloaded.');
    } catch (err) {
      setError(err?.response?.data?.detail?.message || err?.response?.data?.detail || 'Failed to export data');
    } finally {
      setLoadingExport(false);
    }
  };

  const handleDelete = async () => {
    if (confirmText !== 'DELETE') {
      setError('Type DELETE to confirm account deletion.');
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
      <h2 className={styles.title}>Data & Privacy</h2>
      <p className={styles.subtitle}>Export your data or permanently delete your account.</p>

      <div className={styles.actions} style={{ justifyContent: 'flex-start' }}>
        <button type="button" className={styles.secondaryButton} onClick={handleExport} disabled={loadingExport}>
          {loadingExport ? 'Preparing...' : 'Download My Data'}
        </button>
        <button type="button" className={styles.dangerButton} onClick={() => setShowModal(true)}>
          Delete My Account
        </button>
      </div>

      {message ? <div className={styles.messageSuccess}>{message}</div> : null}
      {error ? <div className={styles.messageError}>{error}</div> : null}

      {showModal ? (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>
            <h3 className={styles.title}>Confirm Account Deletion</h3>
            <p className={styles.note}>Type DELETE to confirm permanent deletion.</p>
            <input
              className={styles.input}
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
              placeholder="Type DELETE"
            />
            <div className={styles.actions}>
              <button type="button" className={styles.secondaryButton} onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button type="button" className={styles.dangerButton} onClick={handleDelete} disabled={loadingDelete}>
                {loadingDelete ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
};

export default PrivacySettings;
