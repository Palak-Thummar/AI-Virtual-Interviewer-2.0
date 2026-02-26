/**
 * Stat Card Component
 * Reusable component for displaying statistics
 */

import React from 'react';
import styles from './StatCard.module.css';

export const StatCard = ({ 
  title, 
  value, 
  subtitle, 
  icon,
  trend,
  trendValue,
  variant = 'primary'
}) => {
  return (
    <div className={`${styles.card} ${styles[`card-${variant}`]}`}>
      <div className={styles.header}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <h3 className={styles.title}>{title}</h3>
      </div>
      
      <div className={styles.content}>
        <span className={styles.value}>{value}</span>
        {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
      </div>
      
      {trend && trendValue && (
        <div className={`${styles.trend} ${styles[`trend-${trend > 0 ? 'up' : 'down'}`]}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trendValue)}%
        </div>
      )}
    </div>
  );
};
