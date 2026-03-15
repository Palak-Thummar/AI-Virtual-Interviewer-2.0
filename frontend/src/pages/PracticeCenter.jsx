import React, { useEffect, useState } from 'react';
import { practiceAPI, parseApiError } from '../services/api';
import styles from './PracticeCenter.module.css';

export const PracticeCenterPage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await practiceAPI.getCenter();
        setData(response?.data || null);
      } catch (err) {
        setError(parseApiError(err, 'Failed to load practice center.'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <section className={styles.page}><p>Loading practice center...</p></section>;
  }

  if (error) {
    return <section className={styles.page}><p className={styles.error}>{error}</p></section>;
  }

  const areas = data?.areas_to_improve || [];
  const topics = data?.learning_topics || [];
  const questions = data?.recommended_questions || [];
  const interviews = data?.practice_interviews || [];
  const badges = data?.achievements || [];

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Practice Center</h1>
        <p>Personalized recommendations based on your latest interview intelligence.</p>
      </header>

      <div className={styles.grid}>
        <article className={styles.card}>
          <h2>Job Readiness Index</h2>
          <p className={styles.big}>{Math.round(Number(data?.job_readiness_index || 0))}%</p>
          <p>Daily Streak: {Number(data?.daily_streak || 0)} day(s)</p>
        </article>

        <article className={styles.card}>
          <h2>Areas To Improve</h2>
          <ul>{areas.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>

        <article className={styles.card}>
          <h2>Learning Topics</h2>
          <ul>{topics.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>

        <article className={styles.card}>
          <h2>Recommended Questions</h2>
          <ul>{questions.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>

        <article className={styles.card}>
          <h2>Practice Interviews</h2>
          <ul>{interviews.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>

        <article className={styles.card}>
          <h2>Achievements</h2>
          <div className={styles.badges}>
            {badges.length ? badges.map((badge) => <span key={badge.key} className={styles.badge}>{badge.title}</span>) : <span>No badges unlocked yet</span>}
          </div>
        </article>
      </div>
    </section>
  );
};

export default PracticeCenterPage;
