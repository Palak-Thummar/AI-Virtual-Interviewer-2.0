import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, CheckCheck } from 'lucide-react';
import { NotificationItem } from './NotificationItem';
import styles from './NotificationPanel.module.css';

export const NotificationPanel = ({
  open,
  loading,
  notifications,
  error,
  onClose,
  onMarkRead,
  onMarkAllRead,
  onDelete
}) => {
  const { t } = useTranslation();

  return (
    <>
      <div className={`${styles.overlay} ${open ? styles.overlayVisible : ''}`} onClick={onClose} />
      <aside className={`${styles.panel} ${open ? styles.panelOpen : ''}`} aria-hidden={!open}>
        <header className={styles.header}>
          <div>
            <h3 className={styles.heading}>{t('notifications.title')}</h3>
            <p className={styles.subheading}>{t('notifications.subtitle')}</p>
          </div>
          <button type="button" className={styles.iconButton} onClick={onClose}>
            <X size={16} />
          </button>
        </header>

        <div className={styles.toolbar}>
          <button type="button" className={styles.markAllButton} onClick={onMarkAllRead}>
            <CheckCheck size={14} /> {t('notifications.markAllRead')}
          </button>
        </div>

        {loading ? <p className={styles.state}>{t('notifications.loading')}</p> : null}
        {!loading && error ? <p className={styles.stateError}>{error}</p> : null}

        {!loading && !error && notifications.length === 0 ? (
          <p className={styles.state}>{t('notifications.empty')}</p>
        ) : null}

        {!loading && !error && notifications.length > 0 ? (
          <div className={styles.list}>
            {notifications.map((item) => (
              <NotificationItem
                key={item.id}
                item={item}
                onRead={onMarkRead}
                onDelete={onDelete}
              />
            ))}
          </div>
        ) : null}
      </aside>
    </>
  );
};

export default NotificationPanel;
