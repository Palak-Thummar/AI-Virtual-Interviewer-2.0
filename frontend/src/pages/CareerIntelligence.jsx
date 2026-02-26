import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line
} from 'recharts';
import { Brain, Lightbulb, TrendingUp } from 'lucide-react';
import { analyticsAPI } from '../services/api';
import { useIntelligenceStore } from '../context/IntelligenceStore';
import styles from './CareerIntelligence.module.css';

const readinessMeta = (value) => {
  if (value > 80) {
    return { color: styles.readinessGood, label: 'Excellent readiness level' };
  }
  if (value >= 60) {
    return { color: styles.readinessMedium, label: 'Solid progress with room to improve' };
  }
  return { color: styles.readinessLow, label: 'Early stage readiness, keep practicing' };
};

const LoadingSkeleton = () => (
  <div className={styles.skeletonWrap}>
    <div className={styles.skeletonHero} />
    <div className={styles.skeletonGrid}>
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className={styles.skeletonCard} />
      ))}
    </div>
    <div className={styles.skeletonRow}>
      <div className={styles.skeletonChart} />
      <div className={styles.skeletonChart} />
    </div>
  </div>
);

export const CareerIntelligencePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const storeIntelligence = useIntelligenceStore((state) => state.intelligence);
  const setIntelligence = useIntelligenceStore((state) => state.setIntelligence);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(storeIntelligence || null);

  const fetchSummary = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await analyticsAPI.getCareerIntelligence();
      const data = response?.data || {};
      setSummary(data);
      setIntelligence(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load career intelligence');
    } finally {
      setLoading(false);
    }
  }, [setIntelligence]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary, location.key]);

  useEffect(() => {
    const handleFocus = () => {
      fetchSummary();
    };

    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        fetchSummary();
      }
    };

    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [fetchSummary]);

  const skillData = useMemo(() => {
    const skills = summary?.skill_breakdown || {};
    return Object.entries(skills).map(([name, value]) => ({ name, value }));
  }, [summary]);

  const trendData = useMemo(() => summary?.trend || [], [summary]);
  const roleComparisonData = useMemo(() => {
    const items = Array.isArray(summary?.role_breakdown) ? summary.role_breakdown : [];
    return items.map((item) => ({
      role: item?.role || '-',
      average_score: Number(item?.average_score || 0)
    }));
  }, [summary]);

  const readiness = Number(summary?.role_readiness || 0);
  const readinessPct = Math.max(0, Math.min(100, readiness));
  const readinessState = readinessMeta(readinessPct);

  const kpis = [
    {
      label: 'Total Interviews',
      value: summary?.total_interviews ?? 0,
      note: 'All sessions'
    },
    {
      label: 'Completed Interviews',
      value: summary?.completed_interviews ?? 0,
      note: `${summary?.pending_interviews ?? 0} pending`
    },
    {
      label: 'Average Score',
      value: `${summary?.average_score ?? 0}%`,
      note: 'Completed sessions only'
    },
    {
      label: 'Role Readiness',
      value: `${readinessPct}%`,
      note: 'Interview confidence index'
    }
  ];

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <section className={styles.page}>
        <header className={styles.header}>
          <h1>Career Intelligence</h1>
          <p>Your interview performance insights</p>
        </header>
        <div className={styles.errorCard}>
          <p>{error}</p>
          <button type="button" className={styles.primaryButton} onClick={fetchSummary}>
            Retry
          </button>
        </div>
      </section>
    );
  }

  if ((summary?.completed_interviews ?? 0) === 0) {
    return (
      <section className={styles.page}>
        <header className={styles.header}>
          <h1>Career Intelligence</h1>
          <p>Your interview performance insights</p>
        </header>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <Brain size={28} />
          </div>
          <p>Complete an interview to unlock career insights.</p>
          <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
            Start Interview
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Career Intelligence</h1>
        <p>Your interview performance insights</p>
      </header>

      <section className={styles.kpiGrid}>
        {kpis.map((item) => (
          <article key={item.label} className={styles.kpiCard}>
            <p className={styles.kpiValue}>{item.value}</p>
            <p className={styles.kpiLabel}>{item.label}</p>
            <p className={styles.kpiNote}>{item.note}</p>
          </article>
        ))}
      </section>

      <section className={styles.twoColumn}>
        <article className={styles.card}>
          <h2>Role Readiness</h2>
          <div className={styles.readinessWrap}>
            <div className={styles.readinessRing}>
              <svg viewBox="0 0 120 120" className={styles.readinessSvg}>
                <circle cx="60" cy="60" r="50" className={styles.readinessTrack} />
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  className={`${styles.readinessProgress} ${readinessState.color}`}
                  strokeDasharray={`${(readinessPct / 100) * 314} 314`}
                />
              </svg>
              <div className={styles.readinessCenter}>{readinessPct}%</div>
            </div>
            <p className={styles.readinessText}>{readinessState.label}</p>
          </div>
        </article>

        <article className={styles.card}>
          <h2>Strength vs Weakness</h2>
          <div className={styles.strengthGrid}>
            <div className={`${styles.skillCard} ${styles.skillStrong}`}>
              <span>Strongest Skill</span>
              <strong>{summary?.strongest_skill || '-'}</strong>
            </div>
            <div className={`${styles.skillCard} ${styles.skillWeak}`}>
              <span>Weakest Skill</span>
              <strong>{summary?.weakest_skill || '-'}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className={styles.twoColumn}>
        <article className={styles.card}>
          <h2>Skill Breakdown</h2>
          <div className={styles.chartBox}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skillData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" radius={[8, 8, 0, 0]} animationDuration={700} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className={styles.card}>
          <h2>Performance Trend</h2>
          <div className={styles.chartBox}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="attempt" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="score" stroke="#0ea5e9" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <article className={styles.card}>
        <h2>Role Comparison</h2>
        <div className={styles.chartBox}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={roleComparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="role" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="average_score" fill="#0ea5e9" radius={[8, 8, 0, 0]} animationDuration={700} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className={styles.card}>
        <h2>AI Recommendations</h2>
        <ul className={styles.recommendationList}>
          {(summary?.recommendations || []).map((item, index) => (
            <li key={`${item}-${index}`}>
              <Lightbulb size={15} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
};

export default CareerIntelligencePage;
