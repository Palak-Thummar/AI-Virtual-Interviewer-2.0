import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { interviewHistoryAPI, parseApiError } from '../services/api';
import styles from './InterviewReplay.module.css';

export const InterviewReplayPage = () => {
  const { interviewId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [replay, setReplay] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const response = await interviewHistoryAPI.replay(interviewId);
        setReplay(response?.data || null);
      } catch (err) {
        setError(parseApiError(err, 'Failed to load interview replay.'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [interviewId]);

  if (loading) return <section className={styles.page}><p>Loading replay...</p></section>;
  if (error) return <section className={styles.page}><p className={styles.error}>{error}</p></section>;

  const questions = replay?.questions || [];
  const answers = replay?.answers || [];

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Interview Replay</h1>
        <p>{replay?.role || 'Interview'} | Score: {Math.round(Number(replay?.score || 0))}%</p>
      </header>

      <div className={styles.list}>
        {questions.map((question, index) => {
          const answer = answers.find((item) => Number(item.question_id) === index) || {};
          return (
            <article key={`${index}-${question}`} className={styles.card}>
              <h3>Q{index + 1}</h3>
              <p><strong>Question:</strong> {question}</p>
              <p><strong>Your Answer:</strong> {answer.answer_text || answer.answer || '-'}</p>
              <p><strong>AI Evaluation:</strong> {answer.feedback || '-'}</p>
              <p><strong>Ideal Answer:</strong> {answer.ideal_answer || '-'}</p>
            </article>
          );
        })}
      </div>

      <button type="button" className={styles.backButton} onClick={() => navigate('/interviews')}>Back to Interviews</button>
    </section>
  );
};

export default InterviewReplayPage;
