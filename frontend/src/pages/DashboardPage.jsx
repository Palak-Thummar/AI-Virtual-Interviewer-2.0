import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Calendar,
  CirclePlay,
  FileText,
  Layers,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  Trash2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { analyticsAPI, resumeAPI, interviewAPI } from '../services/api';
import { AppLayout, PageHeader, StaggerGrid, StaggerItem } from '../components/AppLayout';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [inProgressInterviews, setInProgressInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [analyticsData, resumesData, interviewsData] = await Promise.all([
          analyticsAPI.getDashboard(),
          resumeAPI.list(),
          analyticsAPI.getInterviewHistory()
        ]);

        setAnalytics(analyticsData.data || analyticsData);
        setResumes(resumesData.data?.resumes || resumesData.resumes || []);

        const allInterviews = interviewsData.data?.interviews || interviewsData.interviews || [];
        const inProgress = allInterviews.filter((item) => item.status === 'in_progress');
        setInProgressInterviews(inProgress);
      } catch (err) {
        console.error('Dashboard error:', err.response?.data || err.message);
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleDeleteResume = async (resumeId) => {
    const ok = window.confirm('Delete this resume? This action cannot be undone.');
    if (!ok) return;

    setDeletingId(resumeId);
    setDeleteError('');
    setSuccessMsg('');
    try {
      await resumeAPI.delete(resumeId);
      setResumes((prev) => prev.filter((item) => item.id !== resumeId && item._id !== resumeId));
      setSuccessMsg('Resume deleted');
    } catch (err) {
      console.error('Delete resume error', err.response || err.message);
      setDeleteError(err.response?.data?.detail || 'Failed to delete resume');
    } finally {
      setDeletingId(null);
    }
  };

  const handleResumeInterview = (interviewId) => {
    navigate(`/interview/${interviewId}?resume=true`);
  };

  const handleDeleteInterview = async (interviewId) => {
    const ok = window.confirm('Delete this in-progress interview? This cannot be undone.');
    if (!ok) return;

    setDeletingId(interviewId);
    setDeleteError('');
    setSuccessMsg('');
    try {
      await interviewAPI.delete(interviewId);
      setInProgressInterviews((prev) =>
        prev.filter((item) => item.id !== interviewId && item.interview_id !== interviewId)
      );
      setSuccessMsg('Interview deleted');
    } catch (err) {
      console.error('Delete interview error', err.response || err.message);
      setDeleteError(err.response?.data?.detail || 'Failed to delete interview');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="rounded-2xl border border-slate-200 bg-white px-8 py-6 text-slate-600 shadow-card">Loading dashboard...</div>
      </div>
    );
  }

  const stats = analytics
    ? [
        {
          title: 'Average Score',
          value: `${Math.round(analytics.average_score || 0)}%`,
          subtitle: analytics.average_score >= 70 ? 'Improving trend' : 'Needs attention',
          icon: TrendingUp,
          iconBg: 'bg-indigo-50 text-indigo-600'
        },
        {
          title: 'Best Score',
          value: `${Math.round(analytics.best_score || 0)}%`,
          subtitle: 'Top interview performance',
          icon: Trophy,
          iconBg: 'bg-violet-50 text-violet-500'
        },
        {
          title: 'Interviews',
          value: analytics.interview_count || 0,
          subtitle: 'Sessions completed',
          icon: Target,
          iconBg: 'bg-emerald-50 text-emerald-500'
        },
        {
          title: 'Domains',
          value: Object.keys(analytics.domain_performance || {}).length,
          subtitle: 'Coverage across topics',
          icon: Layers,
          iconBg: 'bg-slate-100 text-slate-700'
        }
      ]
    : [];

  return (
    <AppLayout>
      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-2xl border border-indigo-200/60 bg-gradient-to-r from-indigo-600 to-violet-500 px-8 py-9 text-white shadow-soft"
      >
        <div className="absolute -right-16 top-10 h-40 w-40 rounded-full bg-white/15 blur-2xl" />
        <div className="absolute -left-12 bottom-0 h-32 w-32 rounded-full bg-white/10 blur-2xl" />

        <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
              <Sparkles className="h-4 w-4" />
              AI Interview Workspace
            </div>
            <h1 className="text-4xl font-bold tracking-tight">Welcome back, {user?.name || 'there'}.</h1>
            <p className="max-w-xl text-sm text-white/85 sm:text-base">
              Track your progress, continue in-progress sessions, and sharpen your interview skills with focused practice.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/setup')}
            className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-indigo-600 shadow-lg transition-all duration-300 ease-in-out hover:scale-105"
          >
            <CirclePlay className="h-4 w-4" />
            Start Interview
          </button>
        </div>
      </motion.section>

      <div className="mt-10">
        <PageHeader title="Dashboard" description="Your interview analytics and active preparation items." />
      </div>

      {error ? (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-500">{error}</div>
      ) : null}

      <StaggerGrid className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <StaggerItem key={stat.title}>
              <div className="surface-card group p-6 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-2xl">
                <div className="flex items-start justify-between">
                  <div className={`inline-flex h-11 w-11 items-center justify-center rounded-full ${stat.iconBg}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                <p className="mt-4 text-3xl font-bold tracking-tight text-slate-800">{stat.value}</p>
                <p className="mt-1 text-sm font-medium text-slate-700">{stat.title}</p>
                <p className="mt-1 text-xs text-slate-500">{stat.subtitle}</p>
              </div>
            </StaggerItem>
          );
        })}
      </StaggerGrid>

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <section className="surface-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="headline-2">In Progress Interviews</h2>
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600">
              {inProgressInterviews.length}
            </span>
          </div>

          {inProgressInterviews.length > 0 ? (
            <div className="space-y-4">
              {inProgressInterviews.map((interview, idx) => {
                const interviewId = interview.id || interview.interview_id || interview._id;
                return (
                  <div
                    key={idx}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-soft"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-1">
                        <h3 className="text-base font-semibold text-slate-800">{interview.job_role || 'Interview'}</h3>
                        <p className="text-sm text-slate-500">{interview.domain || 'General'}</p>
                        <p className="inline-flex items-center gap-1 text-xs text-slate-500">
                          <Calendar className="h-3.5 w-3.5" />
                          Started {interview.date ? new Date(interview.date).toLocaleDateString() : '-'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleResumeInterview(interviewId)}
                          className="inline-flex items-center gap-1 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white transition-all duration-300 ease-in-out hover:scale-105 hover:bg-indigo-500"
                        >
                          Resume
                          <ArrowRight className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteInterview(interviewId)}
                          disabled={deletingId === interviewId}
                          className="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-500 transition-all duration-300 ease-in-out hover:bg-red-50 disabled:opacity-60"
                        >
                          {deletingId === interviewId ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="body-text">No in-progress interviews right now.</p>
          )}
        </section>

        <section className="surface-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="headline-2">Recent Interviews</h2>
            <button
              type="button"
              onClick={() => navigate('/interviews')}
              className="text-sm font-medium text-indigo-600 transition-all duration-300 ease-in-out hover:text-indigo-500"
            >
              View all
            </button>
          </div>

          {analytics?.recent_interviews?.length > 0 ? (
            <div className="space-y-3">
              {analytics.recent_interviews.slice(0, 5).map((interview, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => navigate(`/results/${interview.interview_id || interview.id}`)}
                  className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-soft"
                >
                  <div>
                    <p className="font-medium text-slate-800">{interview.job_role}</p>
                    <p className="text-xs text-slate-500">{interview.domain} • {interview.date}</p>
                  </div>
                  <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-500">
                    {Math.round(interview.score || 0)}%
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="body-text">No interviews yet. Start your first session.</p>
          )}
        </section>
      </div>

      <section className="surface-card mt-6 p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="headline-2">Your Resumes</h2>
          <span className="text-sm text-slate-500">{resumes.length} uploaded</span>
        </div>

        {successMsg ? (
          <div className="mb-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-500">{successMsg}</div>
        ) : null}

        {deleteError ? (
          <div className="mb-3 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-500">{deleteError}</div>
        ) : null}

        {resumes.length > 0 ? (
          <div className="space-y-3">
            {resumes.map((resume, idx) => {
              const resumeId = resume.id || resume._id;
              return (
                <div
                  key={idx}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-soft"
                >
                  <div className="flex items-center gap-3">
                    <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                      <FileText className="h-4 w-4" />
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{resume.file_name}</p>
                      <p className="text-xs text-slate-500">{resume.uploaded_at || 'Uploaded'}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteResume(resumeId)}
                    disabled={deletingId === resumeId}
                    className="inline-flex items-center gap-1 rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-500 transition-all duration-300 ease-in-out hover:bg-red-50 disabled:opacity-60"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {deletingId === resumeId ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="body-text">Upload a resume to start personalized interview analysis.</p>
        )}
      </section>
    </AppLayout>
  );
};
