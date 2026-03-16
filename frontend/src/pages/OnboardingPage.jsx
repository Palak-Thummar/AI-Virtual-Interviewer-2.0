/**
 * OnboardingPage – shown to new users immediately after registration.
 * 3 steps: Upload Resume → Choose Target Role → Start First Interview
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { resumeAPI, authAPI, settingsAPI, parseApiError } from '../services/api';
import { Button, Select, Alert, Spinner } from '../components/UI';
import styles from './Onboarding.module.css';

const STEPS = [
  { id: 1, title: 'Upload Your Resume', subtitle: 'We\'ll tailor every interview to your background.' },
  { id: 2, title: 'Choose Your Target Role', subtitle: 'Set your goal so we can focus your practice.' },
  { id: 3, title: 'You\'re All Set!', subtitle: 'Start your first mock interview now.' }
];

const ROLE_OPTIONS = [
  { value: '', label: 'Select a role…' },
  { value: 'Software Engineer', label: 'Software Engineer' },
  { value: 'Frontend Developer', label: 'Frontend Developer' },
  { value: 'Backend Developer', label: 'Backend Developer' },
  { value: 'Full Stack Developer', label: 'Full Stack Developer' },
  { value: 'Data Scientist', label: 'Data Scientist' },
  { value: 'ML Engineer', label: 'ML Engineer' },
  { value: 'DevOps Engineer', label: 'DevOps Engineer' },
  { value: 'Product Manager', label: 'Product Manager' },
  { value: 'Other', label: 'Other' }
];

const EXPERIENCE_OPTIONS = [
  { value: '', label: 'Select experience level…' },
  { value: 'Entry Level (0-2 yrs)', label: 'Entry Level (0-2 yrs)' },
  { value: 'Mid Level (2-5 yrs)', label: 'Mid Level (2-5 yrs)' },
  { value: 'Senior (5-8 yrs)', label: 'Senior (5-8 yrs)' },
  { value: 'Lead / Principal (8+ yrs)', label: 'Lead / Principal (8+ yrs)' }
];

export const OnboardingPage = () => {
  const navigate = useNavigate();
  const { refreshUser, user } = useAuth();

  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Step 1
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);

  // Step 2
  const [targetRole, setTargetRole] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('');

  // ── Step 1: upload resume ──
  const handleResumeChange = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) {
      setError('Only PDF or DOCX files are accepted.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File must be under 10 MB.');
      return;
    }

    setResumeFile(file);
    setError('');
    setLoading(true);
    try {
      await resumeAPI.upload(file);
      setResumeUploaded(true);
    } catch (err) {
      setError(parseApiError(err, 'Failed to upload resume. Please try again.'));
    } finally {
      setLoading(false);
    }
  }, []);

  const completeOnboardingAndNavigate = useCallback(async (targetPath) => {
    setLoading(true);
    setError('');
    try {
      await authAPI.completeOnboarding();
      if (refreshUser) await refreshUser();
      navigate(targetPath, { replace: true });
    } catch (err) {
      setError(parseApiError(err, 'Failed to complete onboarding. Please try again.'));
    } finally {
      setLoading(false);
    }
  }, [navigate, refreshUser]);

  // ── Step 2: save role ──
  const handleSaveRole = useCallback(async () => {
    if (!targetRole) {
      setError('Please select a target role.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await settingsAPI.updateProfile({
        full_name: (user?.name || user?.full_name || 'CareerIQ User').trim(),
        primary_role: targetRole,
        experience_level: experienceLevel
      });
      setStep(3);
    } catch (err) {
      setError(parseApiError(err, 'Failed to save role. You can update this later in Settings.'));
    } finally {
      setLoading(false);
    }
  }, [targetRole, experienceLevel, user]);

  // ── Step 3: complete onboarding ──
  const handleFinish = useCallback(async () => {
    completeOnboardingAndNavigate('/setup');
  }, [completeOnboardingAndNavigate]);

  const handleSkip = useCallback(() => {
    completeOnboardingAndNavigate('/dashboard');
  }, [completeOnboardingAndNavigate]);

  const current = STEPS[step - 1];

  return (
    <div className={styles.container}>
      {/* Progress bar */}
      <div className={styles.progress}>
        {STEPS.map((s) => (
          <div
            key={s.id}
            className={`${styles.progressStep} ${step >= s.id ? styles.progressActive : ''}`}
          >
            <div className={styles.progressDot}>{step > s.id ? '✓' : s.id}</div>
            <span className={styles.progressLabel}>{s.title}</span>
          </div>
        ))}
      </div>

      <div className={styles.card}>
        <h1 className={styles.title}>{current.title}</h1>
        <p className={styles.subtitle}>{current.subtitle}</p>

        {error && <Alert type="error" message={error} onDismiss={() => setError('')} />}

        {/* ── Step 1 ── */}
        {step === 1 && (
          <div className={styles.stepContent}>
            <label className={styles.uploadArea}>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleResumeChange}
                className={styles.fileInput}
                disabled={loading}
              />
              {loading ? (
                <div className={styles.uploadPlaceholder}><Spinner /><span>Uploading…</span></div>
              ) : resumeUploaded ? (
                <div className={styles.uploadSuccess}>
                  <span className={styles.checkIcon}>✓</span>
                  <span>{resumeFile?.name} uploaded successfully!</span>
                </div>
              ) : (
                <div className={styles.uploadPlaceholder}>
                  <span className={styles.uploadIcon}>📄</span>
                  <span>Click to upload your resume (PDF or DOCX)</span>
                </div>
              )}
            </label>
            <div className={styles.actions}>
              <Button variant="secondary" onClick={handleSkip} disabled={loading}>
                Skip for now
              </Button>
              <Button
                variant="primary"
                onClick={() => setStep(2)}
                disabled={!resumeUploaded || loading}
              >
                Continue →
              </Button>
            </div>
          </div>
        )}

        {/* ── Step 2 ── */}
        {step === 2 && (
          <div className={styles.stepContent}>
            <Select
              label="Target Role"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              options={ROLE_OPTIONS}
              disabled={loading}
            />
            <Select
              label="Experience Level"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              options={EXPERIENCE_OPTIONS}
              disabled={loading}
            />
            <div className={styles.actions}>
              <Button variant="secondary" onClick={() => setStep(1)} disabled={loading}>
                ← Back
              </Button>
              <Button variant="primary" onClick={handleSaveRole} disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Save & Continue →'}
              </Button>
            </div>
          </div>
        )}

        {/* ── Step 3 ── */}
        {step === 3 && (
          <div className={styles.stepContent}>
            <div className={styles.readyMessage}>
              <span className={styles.readyIcon}>🎯</span>
              <p>Your profile is set up! Start your first mock interview to unlock analytics and personalized coaching.</p>
            </div>
            <div className={styles.actions}>
              <Button variant="secondary" onClick={handleSkip} disabled={loading}>
                Go to Dashboard
              </Button>
              <Button variant="primary" onClick={handleFinish} disabled={loading}>
                {loading ? <Spinner size="sm" /> : 'Start First Interview 🚀'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingPage;
