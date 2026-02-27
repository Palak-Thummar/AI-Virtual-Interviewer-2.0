import React from 'react';
import { Sparkles } from 'lucide-react';
import styles from './Landing.module.css';

export const Hero = () => {
  return (
    <section className={styles.hero} id="top">
      <div>
        <span className={styles.eyebrow}>
          <Sparkles size={14} />
          CareerIQ Interview Intelligence Platform
        </span>
        <h1 className={styles.title}>
          Master Tech Interviews with AI That{' '}
          <span className={styles.gradientText}>Thinks Like a Recruiter</span>
        </h1>
        <p className={styles.subtitle}>
          Personalized AI interviews. Real-time scoring. Skill gap intelligence. Built for serious candidates.
        </p>

        <div className={styles.heroActions}>
          <a className={styles.primaryButton} href="/register">🚀 Start Training</a>
          <a className={styles.secondaryButton} href="#how-it-works">🎥 Watch Demo</a>
        </div>
      </div>

      <div className={styles.mockCard}>
        <div className={styles.mockGlow} />
        <span className={styles.floatChip}>Live Score: 84%</span>
        <span className={styles.floatChipAlt}>Gap Analysis Ready</span>

        <div className={styles.mockHeader}>
          <div className={styles.mockDots}>
            <span />
            <span />
            <span />
          </div>
          <span className={styles.mockPill}>AI Dashboard</span>
        </div>

        <div className={styles.mockPanel}>
          <p className={styles.mockLabel}>Role Simulation</p>
          <p className={styles.mockValue}>Senior Backend Engineer</p>
          <div className={styles.mockBar}>
            <span />
          </div>
        </div>

        <div className={styles.mockPanel}>
          <p className={styles.mockLabel}>Strengths</p>
          <p className={styles.mockValue}>System Design · APIs · Communication</p>
        </div>

        <div className={styles.mockPanel}>
          <p className={styles.mockLabel}>Focus Areas</p>
          <p className={styles.mockValue}>Concurrency · Edge Cases · Scalability</p>
        </div>
      </div>
    </section>
  );
};

export default Hero;
