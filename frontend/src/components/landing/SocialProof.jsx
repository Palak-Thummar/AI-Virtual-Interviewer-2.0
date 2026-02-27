import React from 'react';
import styles from './Landing.module.css';

const stats = [
  { label: 'Interviews completed', value: '1,200+' },
  { label: 'Average score improvement', value: '34%' },
  { label: 'User satisfaction', value: '4.8/5' }
];

export const SocialProof = () => {
  return (
    <section className={styles.section} id="social-proof">
      <h2 className={styles.sectionTitle}>Trusted by candidates serious about growth</h2>
      <p className={styles.sectionText}>Clean signals that show measurable interview performance improvement.</p>

      <div className={styles.socialGrid}>
        <div className={styles.statsPanel}>
          <div className={styles.statsList}>
            {stats.map((stat) => (
              <div className={styles.statItem} key={stat.label}>
                <span className={styles.statLabel}>{stat.label}</span>
                <span className={styles.statValue}>{stat.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.testimonials}>
          <div className={styles.quote}>
            <p className={styles.quoteText}>
              “This felt closest to a real panel loop. The feedback made my weak spots obvious.”
            </p>
            <p className={styles.quoteMeta}>— Priya M., Backend Engineer</p>
          </div>

          <div className={styles.quote}>
            <p className={styles.quoteText}>
              “I improved consistency in behavioral and system rounds within two weeks.”
            </p>
            <p className={styles.quoteMeta}>— Arjun K., Product Engineer</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SocialProof;
