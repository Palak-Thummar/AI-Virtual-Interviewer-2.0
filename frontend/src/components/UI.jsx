/**
 * UI Components - Basic reusable components
 */

import React from 'react';
import styles from './UI.module.css';

// Button Component
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  ...props
}) => (
  <button
    className={`${styles.button} ${styles[`button-${variant}`]} ${styles[`button-${size}`]} ${className}`}
    disabled={disabled || loading}
    {...props}
  >
    {loading ? '...' : children}
  </button>
);

// Card Component
export const Card = ({ children, className = '', ...props }) => (
  <div className={`${styles.card} ${className}`} {...props}>
    {children}
  </div>
);

// Input Component
export const Input = ({
  label,
  error,
  className = '',
  ...props
}) => (
  <div className={styles.formGroup}>
    {label && <label className={styles.label}>{label}</label>}
    <input
      className={`${styles.input} ${error ? styles.inputError : ''} ${className}`}
      {...props}
    />
    {error && <span className={styles.errorText}>{error}</span>}
  </div>
);

// Select Component
export const Select = ({
  label,
  options,
  error,
  className = '',
  ...props
}) => (
  <div className={styles.formGroup}>
    {label && <label className={styles.label}>{label}</label>}
    <select
      className={`${styles.input} ${error ? styles.inputError : ''} ${className}`}
      {...props}
    >
      <option value="">Select {label || 'option'}...</option>
      {options?.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
    {error && <span className={styles.errorText}>{error}</span>}
  </div>
);

// TextArea Component
export const TextArea = ({
  label,
  error,
  rows = 4,
  className = '',
  ...props
}) => (
  <div className={styles.formGroup}>
    {label && <label className={styles.label}>{label}</label>}
    <textarea
      rows={rows}
      className={`${styles.input} ${error ? styles.inputError : ''} ${className}`}
      {...props}
    />
    {error && <span className={styles.errorText}>{error}</span>}
  </div>
);

// Loading Spinner
export const Spinner = ({ size = 'md' }) => (
  <div className={`${styles.spinner} ${styles[`spinner-${size}`]}`} />
);

// Badge Component
export const Badge = ({ children, variant = 'primary', className = '' }) => (
  <span className={`${styles.badge} ${styles[`badge-${variant}`]} ${className}`}>
    {children}
  </span>
);

// Progress Bar
export const ProgressBar = ({ value, max = 100, className = '' }) => {
  const percentage = (value / max) * 100;
  return (
    <div className={`${styles.progressBar} ${className}`}>
      <div
        className={styles.progressFill}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

// Stat Card
export const StatCard = ({ title, value, icon, trend }) => (
  <Card className={styles.statCard}>
    <div className={styles.statCardContent}>
      {icon && <span className={styles.statIcon}>{icon}</span>}
      <div>
        <span className={styles.statTitle}>{title}</span>
        <span className={styles.statValue}>{value}</span>
        {trend && <span className={styles.statTrend}>{trend}</span>}
      </div>
    </div>
  </Card>
);

// Modal Component
export const Modal = ({ isOpen, onClose, title, children, size = 'md' }) => {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div
        className={`${styles.modal} ${styles[`modal-${size}`]}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.modalHeader}>
          <h2>{title}</h2>
          <button onClick={onClose} className={styles.modalClose}>×</button>
        </div>
        <div className={styles.modalBody}>
          {children}
        </div>
      </div>
    </div>
  );
};

// Alert Component
export const Alert = ({ variant = 'info', children, onClose }) => (
  <div className={`${styles.alert} ${styles[`alert-${variant}`]}`}>
    <div>{children}</div>
    {onClose && (
      <button onClick={onClose} className={styles.alertClose}>×</button>
    )}
  </div>
);
