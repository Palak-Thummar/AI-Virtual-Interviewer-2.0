import React from 'react';
import styles from './Landing.module.css';

export const CTA = () => {
  return (
    <section className={styles.section} id="cta">
      <div className={styles.ctaWrap}>
        <h2 className={styles.ctaTitle}>Stop Guessing. Start Training with AI Precision.</h2>
        <a href="/register" className={styles.ctaButton}>Start Free Today</a>
      </div>
    </section>
  );
};

export default CTA;
