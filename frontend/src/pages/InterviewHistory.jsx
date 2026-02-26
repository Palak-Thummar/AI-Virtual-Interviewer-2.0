import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { Loader2, X } from 'lucide-react';
import { analyticsAPI } from '../services/api';
import styles from './InterviewHistory.module.css';

const defaultSkillBreakdown = {
  DSA: 0,
  'System Design': 0,
  Behavioral: 0,
  Communication: 0
};

export const InterviewHistoryPage = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [interviews, setInterviews] = useState([]);
  const [selectedInterview, setSelectedInterview] = useState(null);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await analyticsAPI.getInterviewHistoryList();
      const list = Array.isArray(response?.data) ? response.data : [];
      setInterviews(list);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load interview history.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const summary = useMemo(() => {
    const total = interviews.length;
    const completed = interviews.filter((item) => item?.status === 'completed').length;
    const pending = total - completed;
    const completedScores = interviews
      .filter((item) => item?.status === 'completed')
      .map((item) => Number(item?.score || 0));
    const averageScore = completedScores.length
      ? Math.round((completedScores.reduce((sum, score) => sum + score, 0) / completedScores.length) * 100) / 100
      : 0;

    return {
      total,
      completed,
      pending,
      averageScore
    };
  }, [interviews]);

  const timelineData = useMemo(() => {
    const completedItems = interviews
      .filter((item) => item?.status === 'completed')
      .slice()
      .reverse();

    return completedItems.map((item) => ({
      date: item?.date || '-',
      score: Number(item?.score || 0)
    }));
  }, [interviews]);

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>Interview History</h1>
        <p>Track your progress over time</p>
      </header>

      {loading ? (
        <div className={styles.loadingCard}>
          <Loader2 className={styles.spin} size={22} />
          <p>Loading interview history...</p>
        </div>
      ) : null}

      {!loading && error ? (
        <div className={styles.errorCard}>
          <p>{error}</p>
          <button type="button" className={styles.primaryButton} onClick={fetchHistory}>
            Retry
          </button>
        </div>
      ) : null}

      {!loading && !error && interviews.length === 0 ? (
        <div className={styles.emptyCard}>
          <p>No interviews completed yet.</p>
        </div>
      ) : null}

      {!loading && !error && interviews.length > 0 ? (
        <>
          <section className={styles.summaryStrip}>
            <article className={styles.summaryItem}>
              <span>Total Interviews</span>
              <strong>{summary.total}</strong>
            </article>
            <article className={styles.summaryItem}>
              <span>Completed</span>
              <strong>{summary.completed}</strong>
            </article>
            <article className={styles.summaryItem}>
              <span>Pending</span>
              <strong>{summary.pending}</strong>
            </article>
            <article className={styles.summaryItem}>
              <span>Average Score</span>
              <strong>{summary.averageScore}%</strong>
            </article>
          </section>

          <article className={styles.card}>
            <h2>Performance Timeline</h2>
            <div className={styles.chartWrap}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className={styles.card}>
            <h2>Interview Table</h2>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Role</th>
                    <th>Company</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {interviews.map((item) => {
                    const rawStatus = String(item?.status || '').toLowerCase();
                    const status = rawStatus === 'completed' ? 'completed' : 'pending';
                    const statusClass = status === 'completed' ? styles.statusCompleted : styles.statusPending;
                    return (
                      <tr key={item?.id || `${item?.date}-${item?.role}`}>
                        <td>{item?.date || '-'}</td>
                        <td>{item?.role || '-'}</td>
                        <td>{item?.company || '-'}</td>
                        <td>{Number(item?.score || 0)}%</td>
                        <td>
                          <span className={`${styles.statusBadge} ${statusClass}`}>{status || 'pending'}</span>
                        </td>
                        <td>
                          <button
                            type="button"
                            className={styles.secondaryButton}
                            onClick={() => setSelectedInterview(item)}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </article>
        </>
      ) : null}

      {selectedInterview ? (
        <div className={styles.modalBackdrop} onClick={() => setSelectedInterview(null)}>
          <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>{selectedInterview?.role || 'Interview Details'}</h3>
              <button type="button" className={styles.iconButton} onClick={() => setSelectedInterview(null)}>
                <X size={16} />
              </button>
            </div>

            <div className={styles.modalBody}>
              <div className={styles.detailRow}>
                <span>Company</span>
                <strong>{selectedInterview?.company || '-'}</strong>
              </div>
              <div className={styles.detailRow}>
                <span>Status</span>
                <strong>{selectedInterview?.status || '-'}</strong>
              </div>
              <div className={styles.detailRow}>
                <span>Score</span>
                <strong>{Number(selectedInterview?.score || 0)}%</strong>
              </div>

              <div className={styles.breakdownBlock}>
                <h4>Skill Breakdown</h4>
                <ul>
                  {Object.entries(selectedInterview?.skill_breakdown || defaultSkillBreakdown).map(([key, value]) => (
                    <li key={key}>
                      <span>{key}</span>
                      <strong>{Number(value || 0)}%</strong>
                    </li>
                  ))}
                </ul>
              </div>

              {Array.isArray(selectedInterview?.strengths) && selectedInterview.strengths.length > 0 ? (
                <div className={styles.textBlock}>
                  <h4>Strengths</h4>
                  <p>{selectedInterview.strengths.join(', ')}</p>
                </div>
              ) : null}

              {Array.isArray(selectedInterview?.weaknesses) && selectedInterview.weaknesses.length > 0 ? (
                <div className={styles.textBlock}>
                  <h4>Weaknesses</h4>
                  <p>{selectedInterview.weaknesses.join(', ')}</p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
};

export default InterviewHistoryPage;
