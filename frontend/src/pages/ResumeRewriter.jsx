import React, { useMemo, useRef, useState } from 'react';
import { Copy, Loader2, Sparkles } from 'lucide-react';
import { resumeAPI } from '../services/api';
import styles from './ResumeRewriter.module.css';

const getImpactClass = (score) => {
  if (score > 8) return styles.impactHigh;
  if (score >= 6) return styles.impactMedium;
  return styles.impactLow;
};

const cardItems = [
  { key: 'improved_bullet', title: 'Improved Version' },
  { key: 'quantified_version', title: 'Quantified Version' },
  { key: 'ats_optimized_version', title: 'ATS Optimized Version' }
];

export const ResumeRewriterPage = () => {
  const [bullet, setBullet] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [copiedKey, setCopiedKey] = useState('');

  const resultsRef = useRef(null);

  const canRewrite = bullet.trim() && targetRole.trim() && !loading;

  const impactScore = Number(result?.impact_score ?? 0);
  const impactText = useMemo(() => {
    if (impactScore > 8) return 'Strong impact and recruiter-ready phrasing.';
    if (impactScore >= 6) return 'Good base; can be strengthened with more measurable outcomes.';
    return 'Needs stronger action language and business impact.';
  }, [impactScore]);

  const handleRewrite = async () => {
    if (!canRewrite) return;

    setLoading(true);
    setError('');

    try {
      const response = await resumeAPI.rewrite({
        bullet: bullet.trim(),
        target_role: targetRole.trim()
      });
      setResult(response?.data || null);

      window.setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 80);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to rewrite bullet. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyText = async (key, value) => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey(''), 1400);
    } catch {
      setCopiedKey('');
    }
  };

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Resume Rewriter</h1>
        <p>Optimize your resume bullets with AI</p>
      </header>

      <article className={styles.inputCard}>
        <div className={styles.fieldGroup}>
          <label htmlFor="bullet">Resume Bullet</label>
          <textarea
            id="bullet"
            className={styles.textarea}
            rows={6}
            placeholder="Paste a resume bullet..."
            value={bullet}
            onChange={(event) => setBullet(event.target.value)}
          />
          <span className={styles.charCount}>{bullet.length} characters</span>
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="target-role">Target Role</label>
          <input
            id="target-role"
            className={styles.input}
            type="text"
            placeholder="e.g., Backend Developer"
            value={targetRole}
            onChange={(event) => setTargetRole(event.target.value)}
          />
        </div>

        <div className={styles.actionsRow}>
          <button
            type="button"
            className={styles.primaryButton}
            onClick={handleRewrite}
            disabled={!canRewrite}
          >
            Rewrite Bullet
          </button>
        </div>

        {error ? <p className={styles.errorText}>{error}</p> : null}
      </article>

      {loading ? (
        <article className={styles.loadingCard}>
          <Loader2 className={styles.spin} size={20} />
          <p>Optimizing your resume bullet...</p>
        </article>
      ) : null}

      {!result ? (
        <article className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <Sparkles size={24} />
          </div>
          <p>Paste a resume bullet to improve it.</p>
        </article>
      ) : (
        <div className={styles.resultsWrap} ref={resultsRef}>
          <article className={`${styles.card} ${styles.fadeIn}`}>
            <h2>Impact Score</h2>
            <div className={styles.impactRow}>
              <div className={`${styles.impactScore} ${getImpactClass(impactScore)}`}>{impactScore}</div>
              <p className={styles.impactText}>{impactText}</p>
            </div>
          </article>

          {cardItems.map((item) => {
            const value = result?.[item.key] || '';
            return (
              <article key={item.key} className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2>{item.title}</h2>
                  <button
                    type="button"
                    className={styles.copyButton}
                    onClick={() => copyText(item.key, value)}
                  >
                    <Copy size={14} />
                    {copiedKey === item.key ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className={styles.outputBox}>{value || '-'}</div>
              </article>
            );
          })}

          <article className={styles.card}>
            <h2>Suggested Keywords</h2>
            <div className={styles.keywordWrap}>
              {(result?.suggested_keywords || []).map((keyword, index) => (
                <span key={`${keyword}-${index}`} className={styles.keywordPill}>
                  {keyword}
                </span>
              ))}
            </div>
          </article>
        </div>
      )}
    </section>
  );
};

export default ResumeRewriterPage;
