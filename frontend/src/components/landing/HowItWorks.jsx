import React from 'react';
import styles from './Landing.module.css';

const steps = [
  {
    title: 'Choose Role',
    text: 'Select the target role and context so AI can shape interview depth and expectations.'
  },
  {
    title: 'Take AI Interview',
    text: 'Answer adaptive questions in a realistic flow with coding and theory pressure tests.'
  },
  {
    title: 'Improve with Intelligence',
    text: 'Review score insights, gap analysis, and a focused plan to improve interview outcomes.'
  }
];

export const HowItWorks = () => {
  return (
    <section className={styles.section} id="how-it-works">
      <h2 className={styles.sectionTitle}>How it works</h2>
      <p className={styles.sectionText}>A focused three-step workflow designed for consistent improvement.</p>

      <div className={styles.timeline}>
        {steps.map((step, index) => (
          <article key={step.title} className={styles.stepCard}>
            <span className={styles.stepNumber}>{index + 1}</span>
            <h3 className={styles.stepTitle}>{step.title}</h3>
            <p className={styles.stepText}>{step.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
