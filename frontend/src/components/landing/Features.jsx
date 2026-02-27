import React from 'react';
import { Brain, Briefcase, Code2, LineChart, FileScan, Activity } from 'lucide-react';
import styles from './Landing.module.css';

const featureItems = [
  {
    title: 'AI Mock Interviews',
    text: 'Practice with role-calibrated interview simulations that adapt difficulty in real time.',
    icon: Brain
  },
  {
    title: 'Role-Specific Questioning',
    text: 'Get targeted technical and behavioral prompts mapped to your exact job trajectory.',
    icon: Briefcase
  },
  {
    title: 'Coding + Theory Engine',
    text: 'Train on coding rounds and concept-heavy discussions in one continuous workflow.',
    icon: Code2
  },
  {
    title: 'Skill Intelligence Analytics',
    text: 'Visualize progress signals and weak zones with recruiter-style performance scoring.',
    icon: LineChart
  },
  {
    title: 'Resume-Aware AI',
    text: 'The system reads your resume context to generate relevant interview pressure tests.',
    icon: FileScan
  },
  {
    title: 'Performance Tracking',
    text: 'Track interview history, confidence trends, and measurable improvement over time.',
    icon: Activity
  }
];

export const Features = () => {
  return (
    <section className={styles.section} id="features">
      <h2 className={styles.sectionTitle}>Precision tools for high-stakes interview prep</h2>
      <p className={styles.sectionText}>
        Every feature is designed to replicate recruiter expectations while giving clear intelligence on what to improve next.
      </p>

      <div className={styles.featuresGrid}>
        {featureItems.map((feature) => {
          const Icon = feature.icon;
          return (
            <article key={feature.title} className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <Icon size={16} />
              </div>
              <h3 className={styles.featureTitle}>{feature.title}</h3>
              <p className={styles.featureText}>{feature.text}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export default Features;
