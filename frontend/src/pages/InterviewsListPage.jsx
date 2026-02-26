import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  FileWarning,
  PlayCircle,
  Target,
  TrendingUp
} from 'lucide-react';
import { analyticsAPI } from '../services/api';
import { AppLayout, PageHeader, StaggerGrid, StaggerItem } from '../components/AppLayout';

export const InterviewsListPage = () => {
  const navigate = useNavigate();
  const [allInterviews, setAllInterviews] = useState([]);
  const [pendingInterviews, setPendingInterviews] = useState([]);
  const [completedInterviews, setCompletedInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    const loadInterviews = async () => {
      try {
        setLoading(true);
        const response = await analyticsAPI.getInterviewHistory();
        const interviews = response.data?.interviews || response.interviews || [];

        setAllInterviews(interviews);
        setPendingInterviews(interviews.filter((item) => item.status === 'in_progress'));
        setCompletedInterviews(interviews.filter((item) => item.status === 'completed'));
      } catch (err) {
        console.error('Failed to load interviews:', err);
        setError(err.response?.data?.detail || 'Failed to load interviews');
      } finally {
        setLoading(false);
      }
    };

    loadInterviews();
  }, []);

  const getInterviewId = (interview) => interview._id || interview.interview_id || interview.id;

  const handleResumeInterview = (interview) => {
    const id = getInterviewId(interview);
    navigate(`/interview/${id}?resume=true`);
  };

  const handleViewResults = (interview) => {
    const id = getInterviewId(interview);
    navigate(`/results/${id}`);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not available';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid date';
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="rounded-2xl border border-slate-200 bg-white px-8 py-6 text-slate-600 shadow-card">Loading interviews...</div>
      </div>
    );
  }

  const currentList = activeTab === 'pending' ? pendingInterviews : completedInterviews;

  return (
    <AppLayout>
      <PageHeader
        title="Interviews"
        description="Track active sessions and review completed interviews in one place."
        action={
          <button
            type="button"
            onClick={() => navigate('/setup')}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:scale-105 hover:bg-indigo-500"
          >
            <PlayCircle className="h-4 w-4" />
            Start New Interview
          </button>
        }
      />

      {error ? (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-500">{error}</div>
      ) : null}

      <section className="surface-card p-4">
        <div className="relative grid grid-cols-2 rounded-2xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setActiveTab('pending')}
            className={`relative z-10 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-300 ease-in-out ${
              activeTab === 'pending' ? 'text-indigo-600' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span className="inline-flex items-center gap-1">
              <Clock3 className="h-4 w-4" />
              Pending ({pendingInterviews.length})
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('completed')}
            className={`relative z-10 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-300 ease-in-out ${
              activeTab === 'completed' ? 'text-indigo-600' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <span className="inline-flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4" />
              Completed ({completedInterviews.length})
            </span>
          </button>

          <motion.div
            layout
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className={`absolute bottom-1 top-1 w-[calc(50%-0.25rem)] rounded-xl bg-white shadow-soft ${
              activeTab === 'pending' ? 'left-1' : 'left-[calc(50%+0.125rem)]'
            }`}
          />
        </div>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="surface-card p-5">
          <p className="text-sm text-slate-500">Total Interviews</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-800">{allInterviews.length}</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-sm text-slate-500">In Progress</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-indigo-600">{pendingInterviews.length}</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-sm text-slate-500">Completed</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-emerald-500">{completedInterviews.length}</p>
        </div>
      </section>

      <section className="mt-8">
        {currentList.length === 0 ? (
          <div className="surface-card flex flex-col items-center justify-center px-6 py-16 text-center">
            <div className="mb-4 rounded-full bg-slate-100 p-4 text-slate-500">
              <FileWarning className="h-8 w-8" />
            </div>
            <h2 className="headline-2">No interviews in this tab</h2>
            <p className="mt-2 max-w-md body-text">
              {activeTab === 'pending'
                ? 'You have no active interviews. Start a new one and continue from where you leave off.'
                : 'Complete your next interview to unlock full performance insights and trends.'}
            </p>
          </div>
        ) : (
          <StaggerGrid className="grid gap-5 md:grid-cols-2">
            {currentList.map((interview, index) => {
              const interviewId = getInterviewId(interview);
              const progressTotal = interview.questions?.length || 0;
              const progressDone = interview.answers?.length || 0;
              const progress = progressTotal > 0 ? Math.round((progressDone / progressTotal) * 100) : 0;
              const score = Math.round(interview.overall_score || 0);

              return (
                <StaggerItem key={interviewId || index}>
                  <article className="surface-card h-full p-5 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:scale-[1.01] hover:shadow-2xl">
                    <div className="mb-4 flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-800">{interview.job_role || 'Interview'}</h3>
                        <p className="text-sm text-slate-500">{interview.domain || 'General'}</p>
                      </div>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          activeTab === 'pending'
                            ? 'bg-amber-50 text-amber-600'
                            : 'bg-emerald-50 text-emerald-500'
                        }`}
                      >
                        {activeTab === 'pending' ? 'Pending' : 'Completed'}
                      </span>
                    </div>

                    <div className="space-y-3 text-sm text-slate-500">
                      <p className="inline-flex items-center gap-1">
                        <Clock3 className="h-4 w-4" />
                        {activeTab === 'pending' ? 'Started' : 'Completed'} {formatDate(interview.updated_at || interview.created_at)}
                      </p>

                      {activeTab === 'pending' ? (
                        <>
                          <p className="inline-flex items-center gap-1">
                            <Target className="h-4 w-4" />
                            {progressDone}/{progressTotal} answered
                          </p>
                          <div className="h-2 rounded-full bg-slate-100">
                            <div
                              className="h-2 rounded-full bg-indigo-500 transition-all duration-300 ease-in-out"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </>
                      ) : (
                        <>
                          <p className="inline-flex items-center gap-1">
                            <TrendingUp className="h-4 w-4" />
                            Overall score {score}%
                          </p>
                          {interview.skill_match ? (
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div className="rounded-xl bg-emerald-50 px-3 py-2 text-emerald-600">
                                Matched: {interview.skill_match.matched_skills?.length || 0}
                              </div>
                              <div className="rounded-xl bg-red-50 px-3 py-2 text-red-500">
                                Missing: {interview.skill_match.missing_skills?.length || 0}
                              </div>
                            </div>
                          ) : null}
                        </>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() => (activeTab === 'pending' ? handleResumeInterview(interview) : handleViewResults(interview))}
                      className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-600 transition-all duration-300 ease-in-out hover:scale-105 hover:bg-indigo-100"
                    >
                      {activeTab === 'pending' ? 'Resume Interview' : 'View Results'}
                      <ArrowUpRight className="h-4 w-4" />
                    </button>
                  </article>
                </StaggerItem>
              );
            })}
          </StaggerGrid>
        )}
      </section>
    </AppLayout>
  );
};
