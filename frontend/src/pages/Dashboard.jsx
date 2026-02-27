import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar
} from 'recharts';
import { BriefcaseBusiness, BrainCircuit, Gauge, Loader2, Sparkles, Trophy } from 'lucide-react';
import { analyticsAPI } from '../services/api';
import styles from './Dashboard.module.css';

const statusClassMap = {
  completed: styles.statusSuccess,
  pending: styles.statusWarning
};

export const DashboardPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await analyticsAPI.getSummary();
        setSummary(response?.data || null);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load dashboard.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const kpis = useMemo(() => {
    const total = Number(summary?.total_interviews || 0);
    const avg = Number(summary?.average_score || 0);
    const readiness = Number(summary?.role_readiness || 0);
    const strongest = summary?.strongest_skill || '-';

    return [
      { label: 'Total Interviews', value: total, icon: BriefcaseBusiness },
      { label: 'Average Score', value: `${avg}%`, icon: Gauge },
      { label: 'Role Readiness', value: `${readiness}%`, icon: Trophy },
      { label: 'Strongest Skill', value: strongest, icon: BrainCircuit }
    ];
  }, [summary]);

  const trend = Array.isArray(summary?.trend) ? summary.trend : [];
  const skills = summary?.skill_breakdown || {};
  const skillBreakdown = Object.entries(skills).map(([skill, value]) => ({ skill, value: Number(value || 0) }));
  const recent = Array.isArray(summary?.recent_interviews) ? summary.recent_interviews : [];

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <Loader2 className={styles.spin} size={26} />
          <p className={styles.emptyTitle}>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>{error}</p>
          <button type="button" className={styles.primaryButton} onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hasCompleted = Number(summary?.completed_interviews || 0) > 0;

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h2 className={styles.heroTitle}>CareerIQ Dashboard</h2>
          <p className={styles.heroSubtitle}>Live intelligence from your completed interview sessions.</p>
          <div className={styles.heroActions}>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
              Start New Interview
            </button>
          </div>
        </div>
      </section>

      <section className={styles.kpiGrid}>
        {kpis.map((item) => {
          const Icon = item.icon;
          return (
            <article className={styles.kpiCard} key={item.label}>
              <div className={styles.kpiIconWrap}>
                <Icon size={18} />
              </div>
              <p className={styles.kpiValue}>{item.value}</p>
              <p className={styles.kpiLabel}>{item.label}</p>
            </article>
          );
        })}
      </section>

      {!hasCompleted ? (
        <section className={styles.tableCard}>
          <div className={styles.emptyState}>
            <div className={styles.emptyIllustration}>
              <Sparkles size={28} />
            </div>
            <p className={styles.emptyTitle}>No completed interviews yet.</p>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
              Begin Interview
            </button>
          </div>
        </section>
      ) : (
        <>
          <section className={styles.gridTwo}>
            <article className={styles.chartCard}>
              <h3 className={styles.sectionTitle}>Performance Trend</h3>
              <div className={styles.chartWrap}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trend} margin={{ top: 10, right: 18, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="attempt" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ r: 4, fill: '#6366f1' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className={styles.chartCard}>
              <h3 className={styles.sectionTitle}>Skill Breakdown</h3>
              <div className={styles.chartWrap}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={skillBreakdown} margin={{ top: 10, right: 18, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="skill" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#6366f1" radius={[8, 8, 0, 0]} animationDuration={700} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </section>

          <section className={styles.tableCard}>
            <h3 className={styles.sectionTitle}>Recent Activity</h3>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Score</th>
                    <th>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((item) => {
                    const status = String(item?.status || '').toLowerCase() || 'completed';
                    return (
                      <tr key={item.interview_id}>
                        <td>{item.role || '-'}</td>
                        <td>{Number(item.score || 0)}%</td>
                        <td>{item.date || '-'}</td>
                        <td>
                          <span className={`${styles.statusBadge} ${statusClassMap[status] || styles.statusMuted}`}>
                            {status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default DashboardPage;
