import React, { useMemo } from 'react';
import { Trash2, CheckCircle2 } from 'lucide-react';
import styles from './NotificationPanel.module.css';

const parseTimestamp = (value) => {
  if (!value) return null;
  const raw = String(value);
  const hasTz = /Z$|[+-]\d{2}:?\d{2}$/.test(raw);
  const normalized = hasTz ? raw : `${raw}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const timeAgo = (value) => {
  const createdAt = parseTimestamp(value);
  if (!createdAt) return 'just now';

  const diffMs = Math.max(0, Date.now() - createdAt.getTime());
  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

export const NotificationItem = ({ item, onRead, onDelete }) => {
  const createdText = useMemo(() => timeAgo(item?.created_at), [item?.created_at]);

  return (
    <article className={`${styles.item} ${!item.read ? styles.itemUnread : ''}`}>
      <div className={styles.itemBody}>
        <h4 className={styles.itemTitle}>{item.title}</h4>
        <p className={styles.itemMessage}>{item.message}</p>
        <p className={styles.itemTime}>{createdText}</p>
      </div>

      <div className={styles.itemActions}>
        {!item.read ? (
          <button type="button" className={styles.actionButton} onClick={() => onRead(item.id)} title="Mark as read">
            <CheckCircle2 size={16} />
          </button>
        ) : null}
        <button type="button" className={styles.actionButton} onClick={() => onDelete(item.id)} title="Delete">
          <Trash2 size={16} />
        </button>
      </div>
    </article>
  );
};

export default NotificationItem;
