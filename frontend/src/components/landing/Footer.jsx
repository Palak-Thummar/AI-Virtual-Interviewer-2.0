import React from 'react';
import styles from './Landing.module.css';

export const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div>
        <p className={styles.footerTitle}>CareerIQ</p>
        <p className={styles.footerText}>Train smarter. Interview stronger.</p>
      </div>

      <nav className={styles.footerLinks} aria-label="Footer links">
        <a className={styles.footerLink} href="#features">Features</a>
        <a className={styles.footerLink} href="/privacy">Privacy</a>
        <a className={styles.footerLink} href="https://github.com/Palak-Thummar/AI-Virtual-Interviewer-2.0" target="_blank" rel="noreferrer">GitHub</a>
        <a className={styles.footerLink} href="mailto:hello@aiinterviewer.app">Contact</a>
      </nav>
    </footer>
  );
};

export default Footer;
