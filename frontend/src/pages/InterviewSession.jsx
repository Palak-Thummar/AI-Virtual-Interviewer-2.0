import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Clock3, Loader2, Target, Trophy } from 'lucide-react';
import { interviewAPI } from '../services/api';
import { useIntelligenceStore } from '../context/IntelligenceStore';
import styles from './InterviewSession.module.css';

const QUESTION_TIME_SECONDS = 60;

export const InterviewSessionPage = () => {
  const navigate = useNavigate();
  const { interviewId } = useParams();
  const location = useLocation();
  const isResuming = new URLSearchParams(location.search).get('resume') === 'true';
  const setIntelligence = useIntelligenceStore((state) => state.setIntelligence);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [interview, setInterview] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [timer, setTimer] = useState(QUESTION_TIME_SECONDS);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [completed, setCompleted] = useState(false);
  const [finalScore, setFinalScore] = useState(0);

  useEffect(() => {
    const loadInterview = async () => {
      try {
        setLoading(true);
        setError('');

        const response = isResuming
          ? await interviewAPI.resume(interviewId)
          : await interviewAPI.get(interviewId);

        const data = response?.data || {};

        if (data?.status === 'completed') {
          navigate(`/results/${interviewId}`, { replace: true });
          return;
        }

        setInterview({
          id: data.id,
          role: data.role || data.job_role || '',
          type: data.type || 'general',
          questions: Array.isArray(data.questions) ? data.questions : [],
          answers: Array.isArray(data.answers) ? data.answers : []
        });

        setCurrentQuestionIndex(Number(data.current_question_index || 0));
        setTimer(QUESTION_TIME_SECONDS);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load interview session.');
      } finally {
        setLoading(false);
      }
    };

    loadInterview();
  }, [interviewId, isResuming, navigate]);

  useEffect(() => {
    if (loading || completed || feedback || !interview?.questions?.length) return;

    const interval = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleSkipQuestion();
          return QUESTION_TIME_SECONDS;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [loading, completed, feedback, interview?.questions?.length, currentQuestionIndex]);

  const currentQuestion = interview?.questions?.[currentQuestionIndex] || '';
  const hasMultipleQuestions = (interview?.questions?.length || 0) > 1;

  const completedAnswers = useMemo(() => {
    return Array.isArray(interview?.answers) ? interview.answers.length : 0;
  }, [interview?.answers]);

  const progressPercent = useMemo(() => {
    const total = interview?.questions?.length || 0;
    if (!total) return 0;
    return ((currentQuestionIndex + (feedback ? 1 : 0)) / total) * 100;
  }, [interview?.questions?.length, currentQuestionIndex, feedback]);

  const averageScore = useMemo(() => {
    if (!Array.isArray(interview?.answers) || interview.answers.length === 0) return '0.0';
    const total = interview.answers.reduce((sum, item) => sum + Number(item?.score || 0), 0);
    return (total / interview.answers.length).toFixed(1);
  }, [interview?.answers]);

  const appendAnswerLocally = (entry) => {
    setInterview((prev) => ({
      ...prev,
      answers: [...(prev?.answers || []), entry]
    }));
  };

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim() || submitting) return;

    setSubmitting(true);
    setError('');

    try {
      const response = await interviewAPI.submitAnswer(interviewId, {
        question_id: currentQuestionIndex,
        answer: currentAnswer.trim(),
        skipped: false
      });
      const data = response?.data || {};

      const answerRecord = {
        question_id: currentQuestionIndex,
        question: currentQuestion,
        answer: currentAnswer.trim(),
        score: Number(data?.score || 0),
        feedback: data?.feedback || '',
        strengths: Array.isArray(data?.strengths) ? data.strengths : [],
        improvements: Array.isArray(data?.improvements) ? data.improvements : []
      };

      appendAnswerLocally(answerRecord);
      setFeedback(answerRecord);
      setCurrentAnswer('');
      setTimer(QUESTION_TIME_SECONDS);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSkipQuestion = async () => {
    if (submitting || !hasMultipleQuestions) return;

    setSubmitting(true);
    setError('');

    try {
      await interviewAPI.submitAnswer(interviewId, {
        question_id: currentQuestionIndex,
        answer: '',
        skipped: true
      });

      if (currentQuestionIndex < (interview?.questions?.length || 0) - 1) {
        setCurrentQuestionIndex((prev) => prev + 1);
        setCurrentAnswer('');
        setFeedback(null);
        setTimer(QUESTION_TIME_SECONDS);
      } else {
        await handleSubmitInterview();
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to skip question.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    if (currentQuestionIndex < (interview?.questions?.length || 0) - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setCurrentAnswer('');
      setFeedback(null);
      setTimer(QUESTION_TIME_SECONDS);
      return;
    }

    await handleSubmitInterview();
  };

  const handleSubmitInterview = async () => {
    if (submitting) return;

    setSubmitting(true);
    setError('');

    try {
      const response = await interviewAPI.submit(interviewId, {});
      const data = response?.data || {};
      const score = Number(data?.overall_score || 0);

      if (data?.intelligence) {
        setIntelligence(data.intelligence);
      }

      setFinalScore(score);
      setCompleted(true);
      setFeedback(null);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit interview.');
    } finally {
      setSubmitting(false);
    }
  };

  const timerClassName = `${styles.timer} ${timer < 10 ? styles.timerDanger : ''}`;
  const scoreClassName =
    Number(feedback?.score || 0) >= 80
      ? styles.scoreGood
      : Number(feedback?.score || 0) >= 60
      ? styles.scoreAverage
      : styles.scoreLow;

  const summaryText = useMemo(() => {
    if (finalScore >= 85) return 'Excellent performance. You are interview-ready for top roles.';
    if (finalScore >= 70) return 'Strong progress. Focus on clarity and depth for consistent high scores.';
    if (finalScore >= 55) return 'Good effort. Keep practicing technical precision and storytelling depth.';
    return 'Early stage progress. Practice consistently to improve confidence and quality.';
  }, [finalScore]);

  if (loading) {
    return (
      <div className={styles.page}>
        <section className={styles.evaluatingCard}>
          <Loader2 className={styles.spinIcon} size={24} />
          <h2>Loading interview...</h2>
        </section>
      </div>
    );
  }

  if (error && !interview) {
    return (
      <div className={styles.page}>
        <section className={styles.evaluatingCard}>
          <h2>{error}</h2>
          <button type="button" className={styles.primaryButton} onClick={() => navigate('/interviews')}>
            Back to Interviews
          </button>
        </section>
      </div>
    );
  }

  if (completed) {
    return (
      <div className={styles.page}>
        <section className={styles.completedCard}>
          <div className={styles.completedIconWrap}>
            <Trophy size={24} />
          </div>
          <h2 className={styles.completedTitle}>Interview Completed</h2>
          <p className={styles.completedSubtitle}>Session ID: {interviewId}</p>

          <div className={styles.scoreGrid}>
            <div className={styles.scoreItem}>
              <span>Final Score</span>
              <strong>{Math.round(finalScore)}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>Average Score</span>
              <strong>{averageScore}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>Answered</span>
              <strong>{completedAnswers}</strong>
            </div>
          </div>

          <div className={styles.summaryBox}>
            <Target size={16} />
            <p>{summaryText}</p>
          </div>

          <div className={styles.completedActions}>
            <button type="button" className={styles.secondaryButton} onClick={() => navigate(`/results/${interviewId}`)}>
              View Report
            </button>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/career-intelligence')}>
              View Career Intelligence
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.topProgressWrap}>
        <div className={styles.progressTrack}>
          <div className={styles.progressValue} style={{ width: `${Math.min(100, progressPercent)}%` }} />
        </div>
      </div>

      {error ? (
        <section className={styles.evaluatingCard} style={{ marginBottom: 14 }}>
          <h2>{error}</h2>
        </section>
      ) : null}

      {!feedback ? (
        <section className={styles.sessionWrap}>
          <div className={styles.stickyTimerWrap}>
            <div className={timerClassName}>
              <Clock3 size={16} />
              <span>{timer}s</span>
            </div>
          </div>

          <header className={styles.sessionHeader}>
            <p className={styles.questionCount}>
              Question {currentQuestionIndex + 1} / {interview?.questions?.length || 0}
            </p>
            <span className={styles.categoryBadge}>{interview?.type === 'company' ? 'Company' : 'General'}</span>
          </header>

          <article className={styles.questionCard}>
            <p className={styles.questionText}>{currentQuestion}</p>
          </article>

          <article className={styles.answerCard}>
            <textarea
              className={styles.answerInput}
              value={currentAnswer}
              onChange={(event) => setCurrentAnswer(event.target.value)}
              placeholder="Type your answer here..."
              rows={7}
            />
            <div className={styles.answerMeta}>
              <span>{currentAnswer.length} characters</span>
              <div style={{ display: 'flex', gap: 8 }}>
                {hasMultipleQuestions ? (
                  <button type="button" className={styles.secondaryButton} onClick={handleSkipQuestion} disabled={submitting}>
                    Skip Question
                  </button>
                ) : null}
                <button
                  type="button"
                  className={styles.primaryButton}
                  onClick={handleSubmitAnswer}
                  disabled={!currentAnswer.trim() || submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit Answer'}
                </button>
              </div>
            </div>
          </article>
        </section>
      ) : (
        <section className={styles.feedbackWrap}>
          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>Your Answer</h3>
            <p className={styles.panelText}>{feedback.answer}</p>
          </article>

          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>AI Feedback</h3>
            <div className={`${styles.scoreBadge} ${scoreClassName}`}>Score: {Number(feedback.score || 0)}/100</div>

            {feedback.feedback ? (
              <div className={styles.feedbackBlock}>
                <h4>Overall Feedback</h4>
                <p>{feedback.feedback}</p>
              </div>
            ) : null}

            {Array.isArray(feedback.strengths) && feedback.strengths.length > 0 ? (
              <div className={styles.feedbackBlock}>
                <h4>Strengths</h4>
                <p>{feedback.strengths.join(', ')}</p>
              </div>
            ) : null}

            {Array.isArray(feedback.improvements) && feedback.improvements.length > 0 ? (
              <div className={styles.feedbackBlock}>
                <h4>Improvements</h4>
                <p>{feedback.improvements.join(', ')}</p>
              </div>
            ) : null}

            <div className={styles.feedbackActions}>
              <button type="button" className={styles.primaryButton} onClick={handleNext} disabled={submitting}>
                {currentQuestionIndex === (interview?.questions?.length || 1) - 1 ? 'Submit Interview' : 'Next Question'}
              </button>
            </div>
          </article>
        </section>
      )}
    </div>
  );
};

export default InterviewSessionPage;
