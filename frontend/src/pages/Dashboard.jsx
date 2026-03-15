import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
import { analyticsAPI, parseApiError, resumeAPI, settingsAPI } from '../services/api';
import { Modal, TextArea } from '../components/UI';
import styles from './Dashboard.module.css';

const statusClassMap = {
  completed: styles.statusSuccess,
  pending: styles.statusWarning
};

export const DashboardPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);
  const [resume, setResume] = useState(null);
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [jobDescription, setJobDescription] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError('');
        const [summaryResponse, resumeResponse, resumeListResponse] = await Promise.all([
          analyticsAPI.getSummary(),
          settingsAPI.getResume(),
          resumeAPI.list()
        ]);
        const resumeList = resumeListResponse?.data?.resumes || [];
        const fallbackResume = resumeList.length > 0 ? { resume_id: resumeList[0].id, file_name: resumeList[0].file_name } : null;
        setSummary(summaryResponse?.data || null);
        setResume(resumeResponse?.data?.resume_id ? resumeResponse.data : fallbackResume);
      } catch (err) {
        setError(parseApiError(err, 'Failed to load dashboard.'));
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const kpis = useMemo(() => {
    const total = Number(summary?.total_interviews || 0);
    const avg = Number(summary?.average_score || 0);
    const readiness = Number(summary?.job_readiness_index ?? summary?.role_readiness ?? 0);
    const strongest = summary?.strongest_skill || '-';
    const streak = Number(summary?.daily_streak || 0);

    return [
      { label: t('dashboard.kpis.totalInterviews'), value: total, icon: BriefcaseBusiness },
      { label: t('dashboard.kpis.averageScore'), value: `${avg}%`, icon: Gauge },
      { label: 'Job Readiness Score', value: `${readiness}%`, icon: Trophy },
      { label: t('dashboard.kpis.strongestSkill'), value: strongest, icon: BrainCircuit },
      { label: 'Daily Practice Streak', value: `${streak} day(s)`, icon: Sparkles }
    ];
  }, [summary, t]);

  const trend = Array.isArray(summary?.trend) ? summary.trend : [];
  const skills = summary?.skill_breakdown || {};
  const skillBreakdown = Object.entries(skills).map(([skill, value]) => ({ skill, value: Number(value || 0) }));
  const recent = Array.isArray(summary?.recent_interviews) ? summary.recent_interviews : [];

  const handleAnalyzeResume = async () => {
    if (!resume?.resume_id) {
      navigate('/settings?section=resume');
      return;
    }
    setAnalysisResult(null);
    setAnalysisError('');
    setAnalysisOpen(true);
  };

  const runResumeAnalysis = async () => {
    if (!jobDescription.trim()) {
      setAnalysisError(t('setup.validation.jobDescription'));
      return;
    }

    try {
      setAnalysisLoading(true);
      setAnalysisError('');
      const response = await resumeAPI.analyze(resume.resume_id, {
        resume_id: resume.resume_id,
        job_description: jobDescription.trim()
      });
      setAnalysisResult(response?.data || null);
    } catch (err) {
      setAnalysisError(parseApiError(err, 'Failed to run resume analysis.'));
    } finally {
      setAnalysisLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <Loader2 className={styles.spin} size={26} />
          <p className={styles.emptyTitle}>{t('common.loading')}</p>
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
            {t('common.retry')}
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
          <h2 className={styles.heroTitle}>{t('dashboard.title')}</h2>
          <p className={styles.heroSubtitle}>{t('dashboard.subtitle')}</p>
          <div className={styles.heroActions}>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
              {t('common.startNewInterview')}
            </button>
            <button type="button" className={styles.secondaryButton} onClick={handleAnalyzeResume}>
              {t('dashboard.analyzeResume')}
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

      {(summary?.achievements || []).length ? (
        <section className={styles.tableCard}>
          <h3 className={styles.sectionTitle}>Achievements</h3>
          <div className={styles.heroActions}>
            {(summary?.achievements || []).map((badge) => (
              <span key={badge.key} className={styles.statusBadge}>{badge.title}</span>
            ))}
          </div>
        </section>
      ) : null}

      {!hasCompleted ? (
        <section className={styles.tableCard}>
          <div className={styles.emptyState}>
            <div className={styles.emptyIllustration}>
              <Sparkles size={28} />
            </div>
            <p className={styles.emptyTitle}>{t('dashboard.emptyTitle')}</p>
            <p className={styles.heroSubtitle}>{t('dashboard.emptySubtitle')}</p>
            <button type="button" className={styles.primaryButton} onClick={() => navigate('/setup')}>
              {t('common.startInterview')}
            </button>
          </div>
        </section>
      ) : (
        <>
          <section className={styles.gridTwo}>
            <article className={styles.chartCard}>
              <h3 className={styles.sectionTitle}>{t('dashboard.performanceTrend')}</h3>
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
              <h3 className={styles.sectionTitle}>{t('dashboard.skillBreakdown')}</h3>
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
            <h3 className={styles.sectionTitle}>{t('dashboard.recentActivity')}</h3>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>{t('history.role')}</th>
                    <th>{t('history.score')}</th>
                    <th>{t('history.date')}</th>
                    <th>{t('history.status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.length > 0 ? recent.map((item) => {
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
                  }) : (
                    <tr>
                      <td colSpan="4">{t('dashboard.noRecentActivity')}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <Modal isOpen={analysisOpen} onClose={() => setAnalysisOpen(false)} title={t('dashboard.resumeAnalysisTitle')}>
        <div style={{ display: 'grid', gap: 16 }}>
          {!resume?.resume_id ? <div>{t('dashboard.resumeMissing')}</div> : null}
          {resume?.resume_id ? (
            <>
              <p>{t('dashboard.analyzeResumeDescription')}</p>
              <TextArea
                label={t('dashboard.jobDescription')}
                value={jobDescription}
                onChange={(event) => setJobDescription(event.target.value)}
                placeholder={t('dashboard.jobDescriptionPlaceholder')}
                rows={6}
              />
              {analysisError ? <div className={styles.emptyTitle}>{analysisError}</div> : null}
              {analysisResult ? (
                <div className={styles.tableCard} style={{ padding: 16 }}>
                  <p><strong>{t('results.atsScore')}</strong> {Math.round(Number(analysisResult?.ats_score || 0))}%</p>
                  <p><strong>{t('results.matchedSkills')}</strong> {(analysisResult?.matched_skills || []).join(', ') || '-'}</p>
                  <p><strong>{t('results.missingSkills')}</strong> {(analysisResult?.missing_skills || []).join(', ') || '-'}</p>
                  <p><strong>{t('results.keywordGaps')}</strong> {(analysisResult?.keyword_gaps || []).join(', ') || '-'}</p>
                </div>
              ) : null}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button type="button" className={styles.secondaryButton} onClick={() => setAnalysisOpen(false)}>
                  {t('common.cancel')}
                </button>
                <button type="button" className={styles.primaryButton} onClick={runResumeAnalysis} disabled={analysisLoading}>
                  {analysisLoading ? t('common.loading') : t('dashboard.runAnalysis')}
                </button>
              </div>
            </>
          ) : null}
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage;
