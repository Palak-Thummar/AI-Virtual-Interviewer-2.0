/**
 * Interview Session Page
 * Main interview interface where user answers questions
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { interviewAPI } from '../services/api';
import { Button, TextArea, Card, Spinner, ProgressBar, Alert } from '../components/UI';
import styles from './InterviewSession.module.css';

export const InterviewSessionPage = () => {
  const { interviewId } = useParams();
  const [searchParams] = useSearchParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const isResuming = searchParams.get('resume') === 'true';

  const [interview, setInterview] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(120); // 2 minutes per question

  // Load interview
  useEffect(() => {
    const loadInterview = async () => {
      try {
        let data;
        if (isResuming) {
          // Load from resume endpoint which returns current index
          const resumeData = await interviewAPI.resume(interviewId);
          data = resumeData.data || resumeData;
          setCurrentQuestionIndex(data.current_question_index || 0);
        } else {
          // Regular load from get endpoint
          const getRes = await interviewAPI.get(interviewId);
          data = getRes.data || getRes;
          setCurrentQuestionIndex(0);
        }
        setInterview(data);
      } catch (err) {
        console.error('Failed to load interview:', err);
        setError('Failed to load interview');
      } finally {
        setLoading(false);
      }
    };
    loadInterview();
  }, [interviewId, isResuming]);

  // Timer
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleSkipQuestion();
          return 120;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) {
      setError('Please provide an answer');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await interviewAPI.submitAnswer(interviewId, {
        question_id: currentQuestionIndex,
        answer
      });

      if (currentQuestionIndex < interview.questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setAnswer('');
        setTimeLeft(120);
      } else {
        // All questions answered - navigate to results page
        setTimeout(() => {
          navigate(`/results/${interviewId}`);
        }, 500);
      }
    } catch (err) {
      setError('Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkipQuestion = () => {
    if (currentQuestionIndex < interview.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setAnswer('');
      setTimeLeft(120);
    } else {
      navigate(`/results/${interviewId}`);
    }
  };

  if (loading) {
    return (
      <div className={styles.center}>
        <Spinner size="lg" />
        <span>Loading interview...</span>
      </div>
    );
  }

  if (!interview) {
    return (
      <div className={styles.center}>
        <Alert variant="error">Interview not found</Alert>
      </div>
    );
  }

  const currentQuestion = interview.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / interview.questions.length) * 100;
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>{interview.job_role} - {interview.domain}</h2>
          <span className={styles.question}>
            Question {currentQuestionIndex + 1} of {interview.questions.length}
          </span>
        </div>
        <div className={styles.timer}>
          <span className={styles.timerValue}>
            {minutes}:{seconds.toString().padStart(2, '0')}
          </span>
          <span className={styles.timerLabel}>Time Left</span>
        </div>
      </div>

      {isResuming && (
        <Alert variant="info">
          ✅ Resuming interview from where you left off (Question {currentQuestionIndex + 1})
        </Alert>
      )}

      <ProgressBar value={progress} className={styles.progressBar} />

      <Card className={styles.questionCard}>
        <h3 className={styles.question}>{currentQuestion}</h3>
      </Card>

      {error && <Alert variant="error">{error}</Alert>}

      <Card className={styles.answerCard}>
        <TextArea
          label="Your Answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Type your answer here... You can take up to 2 minutes."
          rows={6}
          disabled={submitting}
        />

        <div className={styles.hint}>
          💡 Tip: Provide detailed, specific examples from your experience. Be clear and articulate.
        </div>
      </Card>

      <div className={styles.actions}>
        <Button
          variant="secondary"
          onClick={handleSkipQuestion}
          disabled={submitting}
        >
          Skip Question
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmitAnswer}
          loading={submitting}
          disabled={!answer.trim()}
        >
          {currentQuestionIndex === interview.questions.length - 1
            ? 'Submit & View Results'
            : 'Submit Answer'}
        </Button>
      </div>

      <div className={styles.note}>
        Your answers are being evaluated in real-time. We measure relevance, technical accuracy, and communication clarity.
      </div>
    </div>
  );
};
