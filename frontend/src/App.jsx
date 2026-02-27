/**
 * Main App Component
 * Router and global app setup
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { InterviewProvider } from './context/InterviewContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/Dashboard';
import { InterviewSetupPage } from './pages/InterviewSetupPage';
import { InterviewSessionPage } from './pages/InterviewSession';
import { ResultsPage } from './pages/ResultsPage';
import { CareerIntelligencePage } from './pages/CareerIntelligence';
import { AnswerLabPage } from './pages/AnswerLab';
import { CodingPracticePage } from './pages/CodingPractice';
import { ResumeRewriterPage } from './pages/ResumeRewriter';
import { CompanyPrepPage } from './pages/CompanyPrep';
import { InterviewHistoryPage } from './pages/InterviewHistory';
import { SettingsPage } from './pages/Settings';
import './styles/globals.css';

const ProtectedLayout = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="rounded-2xl border border-slate-200 bg-white px-8 py-6 text-slate-600 shadow-card">
          Loading...
        </div>
      </div>
    );
  }
  return isAuthenticated ? <AppLayout /> : <Navigate to="/login" replace />;
};

// App Routes
const AppRoutes = () => (
  <Routes>
    {/* Public Landing */}
    <Route path="/" element={<LandingPage />} />

    {/* Auth Routes */}
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />

    {/* Protected Routes */}
    <Route element={<ProtectedLayout />}>
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/interviews" element={<InterviewHistoryPage />} />
      <Route path="/company-prep" element={<CompanyPrepPage />} />
      <Route path="/setup" element={<InterviewSetupPage />} />
      <Route path="/coding-practice" element={<CodingPracticePage />} />
      <Route path="/interview/:interviewId" element={<InterviewSessionPage />} />
      <Route path="/results/:interviewId" element={<ResultsPage />} />
      <Route path="/career-intelligence" element={<CareerIntelligencePage />} />
      <Route path="/analytics" element={<CareerIntelligencePage />} />
      <Route path="/answer-lab" element={<AnswerLabPage />} />
      <Route path="/resume-rewriter" element={<ResumeRewriterPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Route>

    {/* Redirects */}
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

// Main App
export const App = () => {
  return (
    <Router>
      <AuthProvider>
        <InterviewProvider>
          <AppRoutes />
        </InterviewProvider>
      </AuthProvider>
    </Router>
  );
};

export default App;
