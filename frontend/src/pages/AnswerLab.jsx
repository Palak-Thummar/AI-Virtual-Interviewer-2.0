import React, { useMemo, useRef, useState } from 'react';
import { Copy, Loader2, Sparkles } from 'lucide-react';
import { answerLabAPI } from '../services/api';
import styles from './AnswerLab.module.css';

const getScoreClass = (score) => {
  if (score > 8) return styles.scoreGood;
  if (score >= 6) return styles.scoreMedium;
  return styles.scoreLow;
};

export const AnswerLabPage = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [type, setType] = useState('Technical');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const resultRef = useRef(null);

  const charCount = answer.length;
  const isDisabled = !question.trim() || !answer.trim() || loading;

  const subScores = useMemo(
    () => [
      { label: 'Clarity', value: result?.clarity_score ?? 0 },
      { label: 'Structure', value: result?.structure_score ?? 0 },
      { label: 'Technical Depth', value: result?.technical_depth_score ?? 0 }
    ],
    [result]
  );

  const handleAnalyze = async () => {
    if (isDisabled) return;

    setLoading(true);
    setError('');

    try {
      const response = await answerLabAPI.analyze({
        question: question.trim(),
        answer: answer.trim(),
        type
      });

      const payload = response?.data || {};
      setResult(payload);

      window.setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to analyze answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyImproved = async () => {
    const text = result?.improved_answer;
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Answer Lab</h1>
        <p>Refine your responses with AI coaching</p>
      </header>

      <article className={styles.inputCard}>
        <div className={styles.formGroup}>
          <label htmlFor="question">Question</label>
          <textarea
            id="question"
            className={styles.textarea}
            rows={4}
            placeholder="Paste the interview question..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroupGrow}>
            <label htmlFor="answer">Your Answer</label>
            <textarea
              id="answer"
              className={`${styles.textarea} ${styles.answerTextarea}`}
              rows={9}
              placeholder="Paste your full answer..."
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
            />
            <p className={styles.charCount}>{charCount} characters</p>
          </div>

          <div className={styles.typeGroup}>
            <label htmlFor="type">Answer Type</label>
            <select id="type" className={styles.select} value={type} onChange={(event) => setType(event.target.value)}>
              <option value="Technical">Technical</option>
              <option value="Behavioral">Behavioral</option>
            </select>
          </div>
        </div>

        <div className={styles.actionRow}>
          <button type="button" className={styles.primaryButton} onClick={handleAnalyze} disabled={isDisabled}>
            Analyze Answer
          </button>
        </div>

        {error ? <p className={styles.errorText}>{error}</p> : null}
      </article>

      {loading ? (
        <article className={styles.loadingCard}>
          <Loader2 className={styles.spin} size={20} />
          <p>AI is analyzing your answer...</p>
        </article>
      ) : null}

      {!result ? (
        <article className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <Sparkles size={24} />
          </div>
          <p>Paste your answer to receive AI feedback.</p>
        </article>
      ) : (
        <div ref={resultRef} className={styles.resultsWrap}>
          <article className={`${styles.card} ${styles.fadeInCard}`}>
            <h2>Score Overview</h2>
            <div className={styles.scoreRow}>
              <div className={`${styles.overallScore} ${getScoreClass(result?.overall_score ?? 0)}`}>
                {result?.overall_score ?? 0}
              </div>
              <div className={styles.subScoreGrid}>
                {subScores.map((item) => (
                  <div key={item.label} className={styles.subScoreItem}>
                    <span>{item.label}</span>
                    <strong className={getScoreClass(item.value)}>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </article>

          <section className={styles.twoColumn}>
            <article className={`${styles.card} ${styles.greenAccent}`}>
              <h2>Strengths</h2>
              <ul className={styles.list}>
                {(result?.strengths || []).map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </article>

            <article className={`${styles.card} ${styles.redAccent}`}>
              <h2>Weaknesses</h2>
              <ul className={styles.list}>
                {(result?.weaknesses || []).map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </article>
          </section>

          <article className={styles.card}>
            <div className={styles.cardHeaderRow}>
              <h2>Improved Answer</h2>
              <button type="button" className={styles.copyButton} onClick={handleCopyImproved}>
                <Copy size={14} />
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <div className={styles.improvedAnswerBox}>{result?.improved_answer || '-'}</div>
          </article>

          {type === 'Behavioral' && result?.star_format_feedback ? (
            <article className={styles.insightCard}>
              <h3>STAR Format Insight</h3>
              <p>{result?.star_format_feedback}</p>
            </article>
          ) : null}
        </div>
      )}
    </section>
  );
};

export default AnswerLabPage;
