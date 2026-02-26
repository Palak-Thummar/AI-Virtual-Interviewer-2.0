import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { motion } from 'framer-motion';
import { ArrowDownRight, ArrowUpRight, RefreshCcw, TrendingUp } from 'lucide-react';
import { analyticsAPI } from '../services/api';
import { AppLayout, PageHeader, StaggerGrid, StaggerItem } from '../components/AppLayout';

const DOMAIN_COLORS = ['#4f46e5', '#8b5cf6', '#10b981', '#0ea5e9', '#f59e0b', '#ef4444'];

export const AnalyticsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);
  const itemsPerPage = 5;

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setRefreshing(true);
      setLoading(true);
      setError('');
      const res = await analyticsAPI.getFullAnalytics();
      setData(res.data);
    } catch (err) {
      console.error('Analytics fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="rounded-2xl border border-slate-200 bg-white px-8 py-6 text-slate-600 shadow-card">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-500">
          <p>{error}</p>
          <button
            type="button"
            onClick={fetchAnalytics}
            className="mt-4 rounded-xl bg-red-500 px-4 py-2 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:scale-105 hover:bg-red-400"
          >
            Retry
          </button>
        </div>
      </AppLayout>
    );
  }

  if (!data) {
    return (
      <AppLayout>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-600">No analytics data available yet.</div>
      </AppLayout>
    );
  }

  const stats = data.stats || {};
  const scoreTrend = data.score_trend || [];
  const domainPerformance = data.domain_performance || [];
  const interviewHistory = data.interview_history || [];
  const performanceSummary = data.performance_summary || {};
  const strengths = data.strengths || '';
  const improvements = data.improvements || '';

  const totalPages = Math.ceil(interviewHistory.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedHistory = interviewHistory.slice(startIndex, startIndex + itemsPerPage);

  const performanceTrend = performanceSummary.improvement_percentage || 0;

  const kpis = [
    { title: 'Total Interviews', value: stats.total_interviews || 0, accent: 'text-slate-800' },
    { title: 'Completed', value: stats.completed || 0, accent: 'text-emerald-500' },
    { title: 'Average Score', value: `${stats.average_score || 0}%`, accent: 'text-indigo-600' },
    { title: 'Best Score', value: `${stats.best_score || 0}%`, accent: 'text-violet-500' }
  ];

  return (
    <AppLayout>
      <PageHeader
        title="Analytics"
        description="Deep insights into interview performance, trends, and improvement opportunities."
        action={
          <button
            type="button"
            onClick={fetchAnalytics}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-all duration-300 ease-in-out hover:scale-105 hover:shadow-soft"
          >
            <RefreshCcw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((item) => (
          <StaggerItem key={item.title}>
            <div className="surface-card p-5 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-2xl">
              <p className="text-sm text-slate-500">{item.title}</p>
              <p className={`mt-2 text-3xl font-bold tracking-tight ${item.accent}`}>{item.value}</p>
            </div>
          </StaggerItem>
        ))}
      </StaggerGrid>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        {scoreTrend.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="surface-card p-6"
          >
            <h2 className="headline-2 mb-4">Score Trend</h2>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={scoreTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 12,
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 10px 24px -12px rgba(15,23,42,0.25)'
                    }}
                    formatter={(value) => [`${value}%`, 'Score']}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#4f46e5"
                    strokeWidth={3}
                    dot={{ fill: '#4f46e5', r: 4 }}
                    activeDot={{ r: 6 }}
                    animationDuration={700}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        ) : null}

        {domainPerformance.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="surface-card p-6"
          >
            <h2 className="headline-2 mb-4">Domain Performance</h2>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={domainPerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 12,
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 10px 24px -12px rgba(15,23,42,0.25)'
                    }}
                    formatter={(value) => [`${value}%`, 'Score']}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} animationDuration={700}>
                    {domainPerformance.map((entry, index) => (
                      <Cell key={`cell-${entry.name}`} fill={DOMAIN_COLORS[index % DOMAIN_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        ) : null}
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="surface-card p-6 lg:col-span-2">
          <h2 className="headline-2 mb-4">Recent History</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-2 py-3">Role</th>
                  <th className="px-2 py-3">Domain</th>
                  <th className="px-2 py-3">Score</th>
                  <th className="px-2 py-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {paginatedHistory.map((interview, index) => (
                  <tr key={`${interview.job_role}-${index}`} className="border-t border-slate-100">
                    <td className="px-2 py-3 font-medium text-slate-700">{interview.job_role || '-'}</td>
                    <td className="px-2 py-3 text-slate-600">{interview.domain || '-'}</td>
                    <td className="px-2 py-3 font-semibold text-indigo-600">{interview.score || 0}%</td>
                    <td className="px-2 py-3 text-slate-500">
                      {interview.date ? new Date(interview.date).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 ? (
            <div className="mt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-600 transition-all duration-300 ease-in-out hover:bg-slate-50 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-slate-500">Page {currentPage} of {totalPages}</span>
              <button
                type="button"
                onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-600 transition-all duration-300 ease-in-out hover:bg-slate-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          ) : null}
        </div>

        <div className="space-y-6">
          <div className="surface-card p-6">
            <h2 className="headline-2 mb-3">Trend Signal</h2>
            <p className="body-text mb-4">Performance change versus earlier sessions.</p>
            <div className="inline-flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-2">
              {performanceTrend >= 0 ? (
                <ArrowUpRight className="h-5 w-5 text-emerald-500" />
              ) : (
                <ArrowDownRight className="h-5 w-5 text-red-500" />
              )}
              <span className={`text-lg font-semibold ${performanceTrend >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                {performanceTrend >= 0 ? '+' : ''}
                {performanceTrend}%
              </span>
            </div>
          </div>

          <div className="surface-card p-6">
            <h2 className="headline-2 mb-3">Strengths</h2>
            <p className="body-text">{strengths || 'Keep practicing to unlock strengths.'}</p>
          </div>

          <div className="surface-card p-6">
            <h2 className="headline-2 mb-3">Improvements</h2>
            <p className="body-text">{improvements || 'No major issues detected yet.'}</p>
          </div>
        </div>
      </section>

      <section className="surface-card mt-6 p-6">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
          <h2 className="headline-2">Performance Summary</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Total Completed</p>
            <p className="mt-1 text-xl font-semibold text-slate-800">{performanceSummary.total_completed || 0}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Best Score</p>
            <p className="mt-1 text-xl font-semibold text-emerald-500">{performanceSummary.best_score || 0}%</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Worst Score</p>
            <p className="mt-1 text-xl font-semibold text-red-500">{performanceSummary.worst_score || 0}%</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Average Score</p>
            <p className="mt-1 text-xl font-semibold text-indigo-600">{performanceSummary.average_score || 0}%</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 sm:col-span-2 lg:col-span-2">
            <p className="text-sm text-slate-500">Last Interview</p>
            <p className="mt-1 text-xl font-semibold text-slate-800">
              {performanceSummary.last_interview_date
                ? new Date(performanceSummary.last_interview_date).toLocaleDateString()
                : '-'}
            </p>
          </div>
        </div>
      </section>
    </AppLayout>
  );
};
