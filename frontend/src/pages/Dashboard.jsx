import React, { useMemo } from 'react';
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
import { BriefcaseBusiness, BrainCircuit, Gauge, Sparkles, Trophy } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import styles from './Dashboard.module.css';

const mockDashboardResponse = {
  summary: {
    totalInterviews: 24,
    averageScore: 82,
    roleReadiness: 87,
    strongestSkill: 'System Design'
  },
  performanceTrend: [
    { attempt: 'Attempt 1', score: 62 },
    { attempt: 'Attempt 2', score: 68 },
    { attempt: 'Attempt 3', score: 73 },
    { attempt: 'Attempt 4', score: 76 },
    { attempt: 'Attempt 5', score: 81 },
    { attempt: 'Attempt 6', score: 84 },
    { attempt: 'Attempt 7', score: 86 }
  ],
  skillBreakdown: [
    { skill: 'DSA', value: 78 },
    { skill: 'System Design', value: 86 },
    { skill: 'Behavioral', value: 82 },
    { skill: 'Communication', value: 80 }
  ],
  recentActivity: [
    {
      id: 'i_1',
      role: 'Frontend Engineer',
      score: 84,
      date: '2026-02-20T09:30:00.000Z',
      status: 'Completed'
    },
    {
      id: 'i_2',
      role: 'SDE-1',
      score: 79,
      date: '2026-02-18T15:20:00.000Z',
      status: 'Completed'
    },
    {
      id: 'i_3',
      role: 'Product Engineer',
      score: 88,
      date: '2026-02-14T12:05:00.000Z',
      status: 'Completed'
    },
    {
      id: 'i_4',
      role: 'Full Stack Engineer',
      score: 74,
      date: '2026-02-10T18:00:00.000Z',
      status: 'Needs Work'
    },
    {
      id: 'i_5',
      role: 'Backend Engineer',
      score: 81,
      date: '2026-02-06T10:40:00.000Z',
      status: 'Completed'
    }
  ]
};

const statusClassMap = {
  Completed: styles.statusSuccess,
  'Needs Work': styles.statusWarning,
  Pending: styles.statusMuted
};

const formatDate = (value) =>
  new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const dashboardData = useMemo(() => mockDashboardResponse, []);
  const { summary, performanceTrend, skillBreakdown, recentActivity } = dashboardData;

  const hasInterviews = recentActivity.length > 0;

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <h2 className={styles.heroTitle}>Welcome back, {user?.name || 'Candidate'}</h2>
          <p className={styles.heroSubtitle}>
            Keep building momentum—every interview session gets you closer to your next offer.
          </p>
          <div className={styles.heroActions}>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={() => navigate('/setup')}
            >
              Start New Interview
            </button>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => navigate('/setup')}
            >
              Analyze Resume
            </button>
          </div>
        </div>
      </section>

      <section className={styles.kpiGrid}>
        <article className={styles.kpiCard}>
          <div className={styles.kpiIconWrap}>
            <BriefcaseBusiness size={18} />
          </div>
          <p className={styles.kpiValue}>{summary.totalInterviews}</p>
          <p className={styles.kpiLabel}>Total Interviews</p>
        </article>

        <article className={styles.kpiCard}>
          <div className={styles.kpiIconWrap}>
            <Gauge size={18} />
          </div>
          <p className={styles.kpiValue}>{summary.averageScore}%</p>
          <p className={styles.kpiLabel}>Average Score</p>
        </article>

        <article className={styles.kpiCard}>
          <div className={styles.kpiIconWrap}>
            <Trophy size={18} />
          </div>
          <p className={styles.kpiValue}>{summary.roleReadiness}%</p>
          <p className={styles.kpiLabel}>Role Readiness</p>
        </article>

        <article className={styles.kpiCard}>
          <div className={styles.kpiIconWrap}>
            <BrainCircuit size={18} />
          </div>
          <p className={styles.kpiValue}>{summary.strongestSkill}</p>
          <p className={styles.kpiLabel}>Strongest Skill</p>
        </article>
      </section>

      <section className={styles.gridTwo}>
        <article className={styles.chartCard}>
          <h3 className={styles.sectionTitle}>Performance Trend</h3>
          <div className={styles.chartWrap}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceTrend} margin={{ top: 10, right: 18, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="attempt" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 12,
                    boxShadow: '0 12px 28px -20px rgba(15, 23, 42, 0.45)'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#6366f1"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#6366f1' }}
                  activeDot={{ r: 6 }}
                />
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
                <Tooltip
                  contentStyle={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 12,
                    boxShadow: '0 12px 28px -20px rgba(15, 23, 42, 0.45)'
                  }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[8, 8, 0, 0]} animationDuration={700} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className={styles.tableCard}>
        <h3 className={styles.sectionTitle}>Recent Activity</h3>

        {hasInterviews ? (
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
                {recentActivity.slice(0, 5).map((item) => (
                  <tr key={item.id}>
                    <td>{item.role}</td>
                    <td>{item.score}%</td>
                    <td>{formatDate(item.date)}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${statusClassMap[item.status] || styles.statusMuted}`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={styles.emptyState}>
            <div className={styles.emptyIllustration}>
              <Sparkles size={28} />
            </div>
            <p className={styles.emptyTitle}>You haven&apos;t started your first interview yet.</p>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
              Begin Interview
            </button>
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
