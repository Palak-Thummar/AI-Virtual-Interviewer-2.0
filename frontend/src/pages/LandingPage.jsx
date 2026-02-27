import React, { useEffect, useRef, useState } from 'react';
import { Hero } from '../components/landing/Hero';
import { Features } from '../components/landing/Features';
import { HowItWorks } from '../components/landing/HowItWorks';
import { SocialProof } from '../components/landing/SocialProof';
import { CTA } from '../components/landing/CTA';
import { Footer } from '../components/landing/Footer';
import styles from '../components/landing/Landing.module.css';

export const LandingPage = () => {
  const [visibleSections, setVisibleSections] = useState({});
  const refs = useRef({});

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const key = entry.target.dataset.section;
            if (key) {
              setVisibleSections((prev) => ({ ...prev, [key]: true }));
            }
          }
        });
      },
      { threshold: 0.16, rootMargin: '0px 0px -8% 0px' }
    );

    Object.values(refs.current).forEach((element) => {
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);

  const registerSection = (key) => (node) => {
    refs.current[key] = node;
  };

  const sectionClass = (key) =>
    `${styles.reveal} ${visibleSections[key] ? styles.revealVisible : ''}`;

  return (
    <div className={styles.page}>
      <div className={styles.gridOverlay} />
      <div className={styles.blob} />
      <div className={styles.blobAlt} />

      <div className={styles.container}>
        <div ref={registerSection('hero')} data-section="hero" className={sectionClass('hero')}>
          <Hero />
        </div>

        <div ref={registerSection('features')} data-section="features" className={sectionClass('features')}>
          <Features />
        </div>

        <div ref={registerSection('how')} data-section="how" className={sectionClass('how')}>
          <HowItWorks />
        </div>

        <div ref={registerSection('social')} data-section="social" className={sectionClass('social')}>
          <SocialProof />
        </div>

        <div ref={registerSection('cta')} data-section="cta" className={sectionClass('cta')}>
          <CTA />
        </div>

        <Footer />
      </div>
    </div>
  );
};

export default LandingPage;
