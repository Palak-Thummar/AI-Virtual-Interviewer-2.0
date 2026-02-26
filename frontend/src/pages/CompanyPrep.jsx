import React, { useEffect, useRef, useState } from 'react';
import { Building2, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { interviewAPI, settingsAPI } from '../services/api';
import styles from './CompanyPrep.module.css';

const COMPANIES = ['Amazon', 'Google', 'Microsoft', 'TCS', 'Infosys', 'Startup'];

const STORAGE_KEY = 'company_prep_state_v1';

const loadState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const CompanyPrepPage = () => {
  const navigate = useNavigate();
  const summaryRef = useRef(null);

  const persisted = loadState();

  const [company, setCompany] = useState(persisted?.company || '');
  const [role, setRole] = useState(persisted?.role || '');
  const [difficulty, setDifficulty] = useState(persisted?.difficulty || 'Medium');
  const [questionCount, setQuestionCount] = useState(String(persisted?.questionCount || 3));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(persisted?.summary || null);

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        company,
        role,
        difficulty,
        questionCount: Number(questionCount),
        summary
      })
    );
  }, [company, role, difficulty, questionCount, summary]);

  useEffect(() => {
    const loadDefaults = async () => {
      if (persisted?.questionCount) return;
      try {
        const response = await settingsAPI.getPreferences();
        const preferred = Number(response?.data?.default_question_count || 3);
        setQuestionCount(String(Math.min(5, Math.max(1, preferred))));
      } catch {
      }
    };

    loadDefaults();
  }, [persisted?.questionCount]);

  const isDisabled = !company || !role.trim() || !difficulty || !questionCount || loading;

  const handleGenerate = async () => {
    if (isDisabled) return;

    setLoading(true);
    setError('');

    try {
      const payload = {
        company,
        role: role.trim(),
        difficulty,
        question_count: Number(questionCount)
      };

      const response = await interviewAPI.generateCompanyInterview(payload);
      const data = response?.data || null;
      setSummary(data);

      window.setTimeout(() => {
        summaryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 80);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate company interview.');
    } finally {
      setLoading(false);
    }
  };

  const handleStartInterview = () => {
    if (!summary?.interview_id) return;

    navigate(`/interview/${summary.interview_id}`, {
      state: {
        role: summary.role || role,
        questionCount: Array.isArray(summary.questions) ? summary.questions.length : Number(questionCount)
      }
    });
  };

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Company Interview Prep</h1>
        <p>Practice interviews tailored to real company patterns</p>
      </header>

      <article className={styles.card}>
        <h2 className={styles.sectionTitle}>Company Selection</h2>
        <div className={styles.companyGrid}>
          {COMPANIES.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setCompany(item)}
              className={`${styles.companyCard} ${company === item ? styles.companyCardSelected : ''}`}
            >
              <span className={styles.companyIcon}>
                <Building2 size={18} />
              </span>
              <span className={styles.companyName}>{item}</span>
            </button>
          ))}
        </div>

        {!company ? <p className={styles.helperText}>Select a company to begin.</p> : null}
      </article>

      <article className={styles.card}>
        <h2 className={styles.sectionTitle}>Configuration</h2>

        <div className={styles.formGrid}>
          <div className={styles.fieldGroup}>
            <label htmlFor="role">Role</label>
            <input
              id="role"
              type="text"
              className={styles.input}
              value={role}
              onChange={(event) => setRole(event.target.value)}
              placeholder="e.g. Backend Developer"
            />
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="difficulty">Difficulty</label>
            <select
              id="difficulty"
              className={styles.select}
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value)}
            >
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="question-count">Question Count</label>
            <select
              id="question-count"
              className={styles.select}
              value={questionCount}
              onChange={(event) => setQuestionCount(event.target.value)}
            >
              {[1, 2, 3, 4, 5].map((count) => (
                <option key={count} value={count}>
                  {count}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className={styles.actions}>
          <button type="button" className={styles.primaryButton} onClick={handleGenerate} disabled={isDisabled}>
            Generate Interview
          </button>
        </div>

        {error ? <p className={styles.errorText}>{error}</p> : null}
      </article>

      {loading ? (
        <article className={styles.loadingCard}>
          <Loader2 className={styles.spin} size={22} />
          <p>Generating company-style interview questions...</p>
        </article>
      ) : null}

      {summary?.interview_id ? (
        <article className={styles.summaryCard} ref={summaryRef}>
          <h2 className={styles.sectionTitle}>Interview Generated</h2>
          <div className={styles.summaryGrid}>
            <div className={styles.summaryItem}>
              <span>Company</span>
              <strong>{summary?.company || '-'}</strong>
            </div>
            <div className={styles.summaryItem}>
              <span>Role</span>
              <strong>{summary?.role || '-'}</strong>
            </div>
            <div className={styles.summaryItem}>
              <span>Difficulty</span>
              <strong>{difficulty}</strong>
            </div>
            <div className={styles.summaryItem}>
              <span>Question Count</span>
              <strong>{summary?.questions?.length ?? 0}</strong>
            </div>
          </div>

          <div className={styles.actions}>
            <button type="button" className={styles.primaryButton} onClick={handleStartInterview}>
              Start Company Interview
            </button>
          </div>
        </article>
      ) : null}
    </section>
  );
};

export default CompanyPrepPage;
