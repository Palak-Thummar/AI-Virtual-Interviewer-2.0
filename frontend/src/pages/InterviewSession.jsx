import React, { useEffect, useMemo } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { create } from 'zustand';
import { analyticsAPI, interviewAPI } from '../services/api';
import { useIntelligenceStore } from '../context/IntelligenceStore';
import {
  Clock3,
  Loader2,
  Sparkles,
  Target,
  Trophy
} from 'lucide-react';
import styles from './InterviewSession.module.css';

const QUESTION_TIME_SECONDS = 60;

const generateQuestionByIndex = (index, role) => {
  const questionNumber = index + 1;
  const isBehavioral = questionNumber % 3 === 0;
  const type = isBehavioral ? 'Behavioral' : 'Technical';

  if (isBehavioral) {
    return {
      id: questionNumber,
      type,
      question: `For a ${role} role, describe a challenging collaboration scenario you handled and what outcome you achieved.`
    };
  }

  if (questionNumber % 2 === 0) {
    return {
      id: questionNumber,
      type,
      question: `As a ${role}, how would you debug and resolve a production issue while minimizing user impact?`
    };
  }

  return {
    id: questionNumber,
    type,
    question: `For a ${role} position, explain your approach to designing a scalable, maintainable solution for a core feature.`
  };
};

const generateQuestions = (role, questionCount) =>
  Array.from({ length: questionCount }, (_, index) => generateQuestionByIndex(index, role));

const buildMockFeedback = (question, answer) => {
  const answerLength = answer.trim().length;
  const baseline = answerLength > 260 ? 8 : answerLength > 160 ? 7 : answerLength > 70 ? 6 : 5;
  const score = Math.min(10, Math.max(4, baseline + (question.type === 'Technical' ? 1 : 0)));

  return {
    score,
    strengths: 'Clear structure, relevant context, and confident communication in your explanation.',
    improvements: 'Add one concrete real-world example and quantify impact to strengthen credibility.',
    idealAnswer:
      question.type === 'Technical'
        ? 'Start with concise definitions, compare trade-offs, and end with when to choose each approach in production.'
        : 'Use the STAR method with measurable outcomes, collaboration details, and your learning takeaway.'
  };
};

const useInterviewSessionStore = create((set, get) => ({
  questions: [],
  role: '',
  questionCount: 0,
  currentQuestionIndex: 0,
  currentAnswer: '',
  timer: QUESTION_TIME_SECONDS,
  interviewStatus: 'idle',
  feedbackResults: [],
  finalScore: 0,
  isFeedbackVisible: false,
  initializeSession: ({ role, questionCount, questions }) =>
    set({
      role,
      questionCount,
      questions,
      currentQuestionIndex: 0,
      currentAnswer: '',
      timer: QUESTION_TIME_SECONDS,
      interviewStatus: 'idle',
      feedbackResults: [],
      finalScore: 0,
      isFeedbackVisible: false
    }),
  startInterview: () =>
    set({
      currentQuestionIndex: 0,
      currentAnswer: '',
      timer: QUESTION_TIME_SECONDS,
      interviewStatus: 'in-progress',
      feedbackResults: [],
      finalScore: 0,
      isFeedbackVisible: false
    }),
  setCurrentAnswer: (value) => set({ currentAnswer: value }),
  tickTimer: () => set((state) => ({ timer: Math.max(0, state.timer - 1) })),
  resetTimer: () => set({ timer: QUESTION_TIME_SECONDS }),
  beginEvaluation: () => set({ interviewStatus: 'evaluating' }),
  storeFeedback: (feedback) =>
    set((state) => ({
      feedbackResults: [...state.feedbackResults, feedback],
      interviewStatus: 'in-progress',
      isFeedbackVisible: true
    })),
  nextQuestion: () =>
    set((state) => ({
      currentQuestionIndex: state.currentQuestionIndex + 1,
      currentAnswer: '',
      timer: QUESTION_TIME_SECONDS,
      isFeedbackVisible: false,
      interviewStatus: 'in-progress'
    })),
  completeInterview: (scoreOverride) => {
    const { feedbackResults } = get();
    const total = feedbackResults.reduce((sum, item) => sum + item.score, 0);
    const computedScore = feedbackResults.length ? Math.round(total / feedbackResults.length) : 0;
    const finalScore =
      typeof scoreOverride === 'number' && !Number.isNaN(scoreOverride)
        ? Math.round(scoreOverride)
        : computedScore;

    set({
      interviewStatus: 'completed',
      finalScore,
      isFeedbackVisible: false
    });
  },
  endInterviewNow: () => {
    const { feedbackResults } = get();
    const total = feedbackResults.reduce((sum, item) => sum + item.score, 0);
    const finalScore = feedbackResults.length ? Math.round((total / (feedbackResults.length * 10)) * 100) : 0;
    set({ interviewStatus: 'completed', finalScore, isFeedbackVisible: false });
  }
}));

export const InterviewSessionPage = () => {
  const navigate = useNavigate();
  const { interviewId } = useParams();
  const location = useLocation();
  const isRealInterview = Boolean(interviewId && interviewId !== 'mock-session');
  const setIntelligence = useIntelligenceStore((state) => state.setIntelligence);
  const selectedRole = location.state?.role;
  const selectedQuestionCount = Number(location.state?.questionCount);

  const {
    questions,
    role,
    questionCount,
    currentQuestionIndex,
    currentAnswer,
    timer,
    interviewStatus,
    feedbackResults,
    finalScore,
    isFeedbackVisible,
    initializeSession,
    startInterview,
    setCurrentAnswer,
    tickTimer,
    beginEvaluation,
    storeFeedback,
    nextQuestion,
    completeInterview,
    endInterviewNow
  } = useInterviewSessionStore();

  useEffect(() => {
    if (!selectedRole || !Number.isInteger(selectedQuestionCount) || selectedQuestionCount <= 0) {
      navigate('/dashboard', { replace: true });
      return;
    }

    const generatedQuestions = generateQuestions(selectedRole, selectedQuestionCount);

    console.log('Selected role:', selectedRole);
    console.log('Selected questionCount:', selectedQuestionCount);
    console.log('Generated questions length:', generatedQuestions.length);

    initializeSession({
      role: selectedRole,
      questionCount: selectedQuestionCount,
      questions: generatedQuestions
    });
  }, [selectedRole, selectedQuestionCount, initializeSession, navigate, interviewId]);

  const currentQuestion = questions[currentQuestionIndex];
  const latestFeedback = feedbackResults[feedbackResults.length - 1];
  const progressPercent = questions.length
    ? ((currentQuestionIndex + (isFeedbackVisible ? 1 : 0)) / questions.length) * 100
    : 0;
  const averageScore = feedbackResults.length
    ? (feedbackResults.reduce((sum, item) => sum + item.score, 0) / feedbackResults.length).toFixed(1)
    : '0.0';

  useEffect(() => {
    if (interviewStatus !== 'in-progress' || isFeedbackVisible) return undefined;

    const interval = setInterval(() => {
      const { timer: currentTimer } = useInterviewSessionStore.getState();
      if (currentTimer <= 1) {
        clearInterval(interval);
        handleSubmit(true);
      } else {
        tickTimer();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [interviewStatus, isFeedbackVisible]);

  const handleSubmit = async (autoSubmit = false) => {
    const answerToEvaluate = autoSubmit
      ? currentAnswer.trim() || 'No answer provided. Candidate timed out.'
      : currentAnswer.trim();

    if (!answerToEvaluate || interviewStatus !== 'in-progress') return;

    beginEvaluation();

    try {
      if (isRealInterview) {
        const response = await interviewAPI.submitAnswer(interviewId, {
          question_id: currentQuestionIndex,
          answer: answerToEvaluate
        });
        const data = response?.data || {};

        storeFeedback({
          questionId: currentQuestion.id,
          question: currentQuestion.question,
          type: currentQuestion.type,
          answer: answerToEvaluate,
          score: Number(data?.score || 0),
          feedback: data?.feedback || '',
          strengths: Array.isArray(data?.strengths) ? data.strengths.join(' ') : '',
          improvements: Array.isArray(data?.improvements) ? data.improvements.join(' ') : '',
          idealAnswer: 'Focus on concise structure, relevant details, and measurable impact.'
        });
        return;
      }

      window.setTimeout(() => {
        const feedback = buildMockFeedback(currentQuestion, answerToEvaluate);
        storeFeedback({
          questionId: currentQuestion.id,
          question: currentQuestion.question,
          type: currentQuestion.type,
          answer: answerToEvaluate,
          ...feedback
        });
      }, 1300);
    } catch {
      const fallback = buildMockFeedback(currentQuestion, answerToEvaluate);
      storeFeedback({
        questionId: currentQuestion.id,
        question: currentQuestion.question,
        type: currentQuestion.type,
        answer: answerToEvaluate,
        ...fallback
      });
    }
  };

  const finalizeInterview = async () => {
    if (isRealInterview) {
      try {
        const completeResponse = await interviewAPI.complete(interviewId);
        const backendScore = Number(completeResponse?.data?.overall_score ?? 0);
        const intelligenceResponse = await analyticsAPI.getCareerIntelligence();
        setIntelligence(intelligenceResponse?.data || null);
        completeInterview(backendScore);
        return;
      } catch {
        completeInterview();
        return;
      }
    }

    completeInterview();
  };

  const handleEndInterviewNow = async () => {
    if (isRealInterview) {
      await finalizeInterview();
      return;
    }
    endInterviewNow();
  };

  const handleNext = async () => {
    if (currentQuestionIndex < questions.length - 1) {
      nextQuestion();
      return;
    }
    await finalizeInterview();
  };

  const timerClassName = `${styles.timer} ${timer < 10 ? styles.timerDanger : ''}`;
  const scoreClassName =
    latestFeedback?.score >= 80
      ? styles.scoreGood
      : latestFeedback?.score >= 60
      ? styles.scoreAverage
      : styles.scoreLow;

  const summaryText = useMemo(() => {
    if (finalScore >= 85) return 'Excellent performance. You are interview-ready for top roles.';
    if (finalScore >= 70) return 'Strong progress. Focus on clarity and depth for consistent high scores.';
    if (finalScore >= 55) return 'Good effort. Keep practicing technical precision and storytelling depth.';
    return 'Early stage progress. Practice consistently to improve confidence and quality.';
  }, [finalScore]);

  return (
    <div className={styles.page}>
      {interviewStatus !== 'idle' && interviewStatus !== 'completed' ? (
        <div className={styles.topProgressWrap}>
          <div className={styles.progressTrack}>
            <div className={styles.progressValue} style={{ width: `${Math.min(100, progressPercent)}%` }} />
          </div>
        </div>
      ) : null}

      {interviewStatus === 'idle' ? (
        <section className={styles.centerCard}>
          <span className={styles.badge}>AI Mock Session</span>
          <h1 className={styles.title}>Real-time Interview Practice</h1>
          <p className={styles.subtitle}>
            Role: {role || selectedRole} · Difficulty: Intermediate · {questionCount || selectedQuestionCount} Questions · 60 sec/question
          </p>
          <button type="button" className={styles.primaryButton} onClick={startInterview}>
            Start Interview
          </button>
        </section>
      ) : null}

      {interviewStatus === 'in-progress' && !isFeedbackVisible ? (
        <section className={styles.sessionWrap}>
          <div className={styles.stickyTimerWrap}>
            <div className={timerClassName}>
              <Clock3 size={16} />
              <span>{timer}s</span>
            </div>
          </div>

          <header className={styles.sessionHeader}>
            <p className={styles.questionCount}>
              Question {currentQuestionIndex + 1} / {questions.length}
            </p>
            <span className={styles.categoryBadge}>{currentQuestion?.type}</span>
          </header>

          <article className={styles.questionCard}>
            <p className={styles.questionText}>{currentQuestion?.question}</p>
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
              <button
                type="button"
                className={styles.primaryButton}
                onClick={() => handleSubmit(false)}
                disabled={!currentAnswer.trim()}
              >
                Submit Answer
              </button>
            </div>
          </article>
        </section>
      ) : null}

      {interviewStatus === 'evaluating' ? (
        <section className={styles.evaluatingCard}>
          <Loader2 className={styles.spinIcon} size={24} />
          <h2>Evaluating your answer...</h2>
          <p>AI is generating structured feedback and ideal response guidance.</p>
        </section>
      ) : null}

      {interviewStatus === 'in-progress' && isFeedbackVisible && latestFeedback ? (
        <section className={styles.feedbackWrap}>
          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>Your Answer</h3>
            <p className={styles.panelText}>{latestFeedback.answer}</p>
          </article>

          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>AI Feedback</h3>
            <div className={`${styles.scoreBadge} ${scoreClassName}`}>
              Score: {latestFeedback.score}/100
            </div>

            {latestFeedback.feedback ? (
              <div className={styles.feedbackBlock}>
                <h4>Overall Feedback</h4>
                <p>{latestFeedback.feedback}</p>
              </div>
            ) : null}

            <div className={styles.feedbackBlock}>
              <h4>Strengths</h4>
              <p>{latestFeedback.strengths}</p>
            </div>

            <div className={styles.feedbackBlock}>
              <h4>Improvements</h4>
              <p>{latestFeedback.improvements}</p>
            </div>

            <div className={styles.idealAnswer}>
              <h4>Ideal Answer</h4>
              <p>{latestFeedback.idealAnswer}</p>
            </div>

            <div className={styles.feedbackActions}>
              <button type="button" className={styles.secondaryButton} onClick={handleEndInterviewNow}>
                End Interview
              </button>
              <button type="button" className={styles.primaryButton} onClick={handleNext}>
                {currentQuestionIndex === questions.length - 1 ? 'Finish Interview' : 'Next Question'}
              </button>
            </div>
          </article>
        </section>
      ) : null}

      {interviewStatus === 'completed' ? (
        <section className={styles.completedCard}>
          <div className={styles.completedIconWrap}>
            <Trophy size={24} />
          </div>
          <h2 className={styles.completedTitle}>Interview Completed</h2>
          <p className={styles.completedSubtitle}>Session ID: {interviewId || 'mock-session'}</p>

          <div className={styles.scoreGrid}>
            <div className={styles.scoreItem}>
              <span>Final Score</span>
              <strong>{finalScore}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>Average Score</span>
              <strong>{averageScore}%</strong>
            </div>
            <div className={styles.scoreItem}>
              <span>Questions</span>
              <strong>{feedbackResults.length}</strong>
            </div>
          </div>

          <div className={styles.summaryBox}>
            <Target size={16} />
            <p>{summaryText}</p>
          </div>

          <div className={styles.completedActions}>
            <button type="button" className={styles.secondaryButton} onClick={() => navigate('/analytics')}>
              View Detailed Analytics
            </button>
            <button type="button" className={styles.primaryButton} onClick={startInterview}>
              Retake Interview
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
};

export default InterviewSessionPage;
