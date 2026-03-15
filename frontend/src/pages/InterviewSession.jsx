import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { Clock3, Loader2, Target, Trophy, Mic, MicOff, ChevronDown, ChevronUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { interviewAPI, parseApiError } from '../services/api';
import { useIntelligenceStore } from '../context/IntelligenceStore';
import styles from './InterviewSession.module.css';

const QUESTION_TIME_SECONDS = 60;

export const InterviewSessionPage = () => {
  const { t } = useTranslation();
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
  const [feedbackExpanded, setFeedbackExpanded] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [finalScore, setFinalScore] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [recognitionInstance, setRecognitionInstance] = useState(null);

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
          interview_type: data.interview_type || 'general',
          programming_language: data.programming_language || 'python',
          questions: Array.isArray(data.questions) ? data.questions : [],
          answers: Array.isArray(data.answers) ? data.answers : []
        });

        setCurrentQuestionIndex(Number(data.current_question_index || 0));
        setTimer(QUESTION_TIME_SECONDS);
      } catch (err) {
        setError(parseApiError(err, 'Failed to load interview session.'));
      } finally {
        setLoading(false);
      }
    };

    loadInterview();
  }, [interviewId, isResuming, navigate]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript.trim()) {
        setCurrentAnswer((prev) => `${prev}${prev ? ' ' : ''}${transcript}`.trim());
      }
    };
    recognition.onend = () => setIsRecording(false);

    setRecognitionInstance(recognition);
    setSpeechSupported(true);

    return () => {
      recognition.stop();
    };
  }, []);

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
        skipped: false,
        answer_type: interview?.interview_type === 'coding' ? 'code' : (interview?.interview_type === 'voice' ? 'voice' : 'text'),
        language: interview?.programming_language || 'python',
        audio_url: interview?.interview_type === 'voice' ? 'captured-via-web-speech-api' : null
      });
      const data = response?.data || {};

      const answerRecord = {
        question_id: currentQuestionIndex,
        question: currentQuestion,
        answer: currentAnswer.trim(),
        score: Number(data?.score || 0),
        feedback: data?.feedback || '',
        strengths: Array.isArray(data?.strengths) ? data.strengths : [],
        weaknesses: Array.isArray(data?.weaknesses) ? data.weaknesses : [],
        improvements: Array.isArray(data?.improvements) ? data.improvements : [],
        improvement_tips: Array.isArray(data?.improvement_tips) ? data.improvement_tips : [],
        ideal_answer: data?.ideal_answer || '',
        runtime_ms: data?.runtime_ms ?? null,
        test_case_success: data?.test_case_success ?? null,
      };

      appendAnswerLocally(answerRecord);
      setFeedback(answerRecord);
      setCurrentAnswer('');
      setTimer(QUESTION_TIME_SECONDS);
    } catch (err) {
      setError(parseApiError(err, 'Failed to submit answer.'));
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
      setError(parseApiError(err, 'Failed to skip question.'));
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
      setError(parseApiError(err, 'Failed to submit interview.'));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleRecording = () => {
    if (!recognitionInstance) return;
    if (isRecording) {
      recognitionInstance.stop();
      setIsRecording(false);
      return;
    }
    recognitionInstance.start();
    setIsRecording(true);
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

  const resumeBanner = isResuming ? t('session.resumeBanner', { question: currentQuestionIndex + 1 }) : '';

  if (loading) {
    return (
      <div className={styles.page}>
        <section className={styles.evaluatingCard}>
          <Loader2 className={styles.spinIcon} size={24} />
          <h2>{t('session.loading')}</h2>
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
            {t('nav.interviews')}
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
          <h2 className={styles.completedTitle}>{t('session.completed.title')}</h2>
          <p className={styles.completedSubtitle}>{t('session.completed.sessionId', { id: interviewId })}</p>

          <div className={styles.scoreGrid}>
            <div className={styles.scoreItem}>
              <span>{t('session.completed.finalScore')}</span>
              <strong>{Math.round(finalScore)}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>{t('session.completed.averageScore')}</span>
              <strong>{averageScore}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>{t('session.completed.answered')}</span>
              <strong>{completedAnswers}</strong>
            </div>
          </div>

          <div className={styles.summaryBox}>
            <Target size={16} />
            <p>{summaryText}</p>
          </div>

          <div className={styles.completedActions}>
            <button type="button" className={styles.secondaryButton} onClick={() => navigate(`/results/${interviewId}`)}>
              {t('common.viewReport')}
            </button>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/career-intelligence')}>
              {t('session.completed.viewCareer')}
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
          {resumeBanner ? <p className={styles.questionCount}>{resumeBanner}</p> : null}
          <div className={styles.stickyTimerWrap}>
            <div className={timerClassName}>
              <Clock3 size={16} />
              <span>{timer}s</span>
            </div>
          </div>

          <header className={styles.sessionHeader}>
            <p className={styles.questionCount}>
              {t('session.questionCounter', { current: currentQuestionIndex + 1, total: interview?.questions?.length || 0 })}
            </p>
            <span className={styles.categoryBadge}>{interview?.type === 'company' ? t('session.company') : t('session.general')}</span>
          </header>

          <article className={styles.questionCard}>
            <p className={styles.questionText}>{currentQuestion}</p>
          </article>

          <article className={styles.answerCard}>
            {interview?.interview_type === 'coding' ? (
              <Editor
                height="320px"
                language={(interview?.programming_language || 'python').toLowerCase()}
                value={currentAnswer}
                onChange={(value) => setCurrentAnswer(value || '')}
                options={{ minimap: { enabled: false }, fontSize: 14, automaticLayout: true }}
              />
            ) : (
              <textarea
                className={styles.answerInput}
                value={currentAnswer}
                onChange={(event) => setCurrentAnswer(event.target.value)}
                placeholder={t('session.answerPlaceholder')}
                rows={7}
              />
            )}

            {interview?.interview_type === 'voice' ? (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={toggleRecording}
                  disabled={!speechSupported}
                >
                  {isRecording ? <MicOff size={15} /> : <Mic size={15} />} {isRecording ? 'Stop Recording' : 'Start Recording'}
                </button>
              </div>
            ) : null}

            <div className={styles.answerMeta}>
              <span>{t('session.characters', { count: currentAnswer.length })}</span>
              <div style={{ display: 'flex', gap: 8 }}>
                {hasMultipleQuestions ? (
                  <button type="button" className={styles.secondaryButton} onClick={handleSkipQuestion} disabled={submitting}>
                    {t('session.skipQuestion')}
                  </button>
                ) : null}
                <button
                  type="button"
                  className={styles.primaryButton}
                  onClick={handleSubmitAnswer}
                  disabled={!currentAnswer.trim() || submitting}
                >
                  {submitting ? t('session.submitting') : t('session.submitAnswer')}
                </button>
              </div>
            </div>
          </article>
        </section>
      ) : (
        <section className={styles.feedbackWrap}>
          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>{t('session.feedback.yourAnswer')}</h3>
            <p className={styles.panelText}>{feedback.answer}</p>
          </article>

          <article className={styles.panel}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className={styles.panelTitle}>{t('session.feedback.aiFeedback')}</h3>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setFeedbackExpanded((prev) => !prev)}
              >
                {feedbackExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />} {feedbackExpanded ? 'Collapse' : 'Expand'}
              </button>
            </div>
            <div className={`${styles.scoreBadge} ${scoreClassName}`}>{t('session.feedback.score', { score: Number(feedback.score || 0) })}</div>

            {feedback.runtime_ms != null ? (
              <div className={styles.feedbackBlock}>
                <h4>Runtime</h4>
                <p>{Number(feedback.runtime_ms).toFixed(0)} ms</p>
              </div>
            ) : null}

            {feedback.test_case_success != null ? (
              <div className={styles.feedbackBlock}>
                <h4>Test Case Success</h4>
                <p>{Number(feedback.test_case_success).toFixed(0)}%</p>
              </div>
            ) : null}

            {feedbackExpanded && feedback.feedback ? (
              <div className={styles.feedbackBlock}>
                <h4>{t('session.feedback.overall')}</h4>
                <p>{feedback.feedback}</p>
              </div>
            ) : null}

            {feedbackExpanded && Array.isArray(feedback.strengths) && feedback.strengths.length > 0 ? (
              <div className={styles.feedbackBlock}>
                <h4>{t('session.feedback.strengths')}</h4>
                <p>{feedback.strengths.join(', ')}</p>
              </div>
            ) : null}

            {feedbackExpanded && Array.isArray(feedback.weaknesses) && feedback.weaknesses.length > 0 ? (
              <div className={styles.feedbackBlock}>
                <h4>Weaknesses</h4>
                <p>{feedback.weaknesses.join(', ')}</p>
              </div>
            ) : null}

            {feedbackExpanded && Array.isArray(feedback.improvement_tips || feedback.improvements) && (feedback.improvement_tips || feedback.improvements).length > 0 ? (
              <div className={styles.feedbackBlock}>
                <h4>{t('session.feedback.improvements')}</h4>
                <p>{(feedback.improvement_tips || feedback.improvements).join(', ')}</p>
              </div>
            ) : null}

            {feedbackExpanded && feedback.ideal_answer ? (
              <div className={styles.feedbackBlock}>
                <h4>Ideal Answer</h4>
                <p>{feedback.ideal_answer}</p>
              </div>
            ) : null}

            <div className={styles.feedbackActions}>
              <button type="button" className={styles.primaryButton} onClick={handleNext} disabled={submitting}>
                {currentQuestionIndex === (interview?.questions?.length || 1) - 1 ? t('session.submitInterview') : t('session.nextQuestion')}
              </button>
            </div>
          </article>
        </section>
      )}
    </div>
  );
};

export default InterviewSessionPage;
