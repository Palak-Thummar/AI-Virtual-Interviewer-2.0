/**
 * Interview Setup Page - THE KEY DIFFERENTIATOR
 * User uploads resume, pastes JD, and sets up interview
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { interviewAPI, parseApiError, resumeAPI, settingsAPI } from '../services/api';
import { Button, Input, TextArea, Select, Alert, Card, Spinner, Badge } from '../components/UI';
import styles from './InterviewSetup.module.css';

export const InterviewSetupPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  
  // Resume upload
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeId, setResumeId] = useState('');
  const [resumeLoading, setResumeLoading] = useState(false);
  
  // Interview setup
  const [jobRole, setJobRole] = useState('');
  const [domain, setDomain] = useState('');
  const [programmingLanguage, setProgrammingLanguage] = useState('Python');
  const [jobDescription, setJobDescription] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: Resume, 2: JD, 3: Review

  useEffect(() => {
    const loadDefaults = async () => {
      try {
        const response = await settingsAPI.getPreferences();
        const preferred = Number(response?.data?.default_question_count || 5);
        setNumQuestions(Math.min(20, Math.max(1, preferred)));
      } catch {
      }
    };

    loadDefaults();
  }, []);

  // Upload resume
  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setResumeFile(file);
    setResumeLoading(true);
    setError('');

    try {
      const response = await resumeAPI.upload(file);
      setResumeId(response.data.resume_id);
      setStep(2);
    } catch (err) {
      setError(parseApiError(err, 'Failed to upload resume.'));
    } finally {
      setResumeLoading(false);
    }
  };

  // Start interview
  const handleStartInterview = async () => {
    if (!resumeId) {
      setError(t('setup.validation.resume'));
      return;
    }
    if (!jobRole) {
      setError(t('setup.validation.jobRole'));
      return;
    }
    if (!domain) {
      setError(t('setup.validation.domain'));
      return;
    }
    if (!jobDescription) {
      setError(t('setup.validation.jobDescription'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Analyze resume vs JD
      const analysisResponse = await interviewAPI.create({
        job_role: jobRole,
        domain,
        programming_language: programmingLanguage,
        job_description: jobDescription,
        resume_id: resumeId,
        num_questions: numQuestions
      });

      setAnalysisData(analysisResponse.data);
      setStep(3);
    } catch (err) {
      setError(parseApiError(err, 'Failed to create interview.'));
    } finally {
      setLoading(false);
    }
  };

  // Confirm and start
  const handleConfirmStart = () => {
    if (analysisData?.interview_id) {
      navigate(`/interview/${analysisData.interview_id}`, {
        state: {
          role: analysisData.job_role || jobRole,
          questionCount: Number(numQuestions)
        }
      });
    }
  };

  const domainOptions = [
    { value: 'Backend', label: t('setup.domains.backend') },
    { value: 'Frontend', label: t('setup.domains.frontend') },
    { value: 'Fullstack', label: t('setup.domains.fullstack') },
    { value: 'DevOps', label: t('setup.domains.devops') },
    { value: 'Data', label: t('setup.domains.data') },
    { value: 'Mobile', label: t('setup.domains.mobile') }
  ];

  const programmingLanguageOptions = [
    { value: 'Python', label: 'Python' },
    { value: 'Java', label: 'Java' },
    { value: 'C++', label: 'C++' },
    { value: 'JavaScript', label: 'JavaScript' },
    { value: 'Go', label: 'Go' }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>{t('setup.title')}</h1>
        <p>{t('setup.subtitle')}</p>
      </div>

      <div className={styles.steps}>
        <div className={`${styles.step} ${step >= 1 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>1</span>
          <span>{t('setup.steps.resume')}</span>
        </div>
        <div className={`${styles.step} ${step >= 2 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>2</span>
          <span>{t('setup.steps.details')}</span>
        </div>
        <div className={`${styles.step} ${step >= 3 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>3</span>
          <span>{t('setup.steps.review')}</span>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Step 1: Resume Upload */}
      {step === 1 && (
        <Card className={styles.card}>
          <h2>{t('setup.uploadTitle')}</h2>
          <p className={styles.description}>
            {t('setup.uploadDescription')}
          </p>

          <div className={styles.uploadArea}>
            <label htmlFor="resume-upload" className={styles.uploadLabel}>
              <input
                id="resume-upload"
                type="file"
                accept=".pdf,.docx"
                onChange={handleResumeUpload}
                disabled={resumeLoading}
                className={styles.fileInput}
              />
              <div className={styles.uploadContent}>
                <span className={styles.uploadIcon}>📎</span>
                <span className={styles.uploadText}>
                  {resumeFile ? resumeFile.name : t('setup.uploadPrompt')}
                </span>
                <span className={styles.uploadNote}>{t('setup.uploadNote')}</span>
              </div>
            </label>
          </div>

          {resumeLoading && (
            <div className={styles.loading}>
              <Spinner size="sm" />
              <span>{t('setup.uploading')}</span>
            </div>
          )}

          {resumeId && (
            <div className={styles.success}>
              {t('setup.uploadSuccess')}
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Job Details */}
      {step === 2 && (
        <Card className={styles.card}>
          <h2>{t('setup.detailsTitle')}</h2>

          <Input
            label={t('setup.jobRole')}
            value={jobRole}
            onChange={(e) => setJobRole(e.target.value)}
            placeholder="Senior Backend Engineer"
          />

          <Select
            label={t('setup.domain')}
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            options={domainOptions}
            placeholder={t('setup.domain')}
          />

          <Select
            label={t('setup.programmingLanguage')}
            value={programmingLanguage}
            onChange={(e) => setProgrammingLanguage(e.target.value)}
            options={programmingLanguageOptions}
            placeholder={t('setup.programmingLanguage')}
          />

          <Input
            type="number"
            label={t('setup.questionCount')}
            value={numQuestions}
            onChange={(e) => setNumQuestions(Math.min(20, Math.max(1, parseInt(e.target.value))))}
            min="1"
            max="20"
          />

          <TextArea
            label={t('setup.jobDescription')}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder={t('dashboard.jobDescriptionPlaceholder')}
            rows={8}
          />

          <div className={styles.actions}>
            <Button
              variant="secondary"
              onClick={() => setStep(1)}
            >
              {t('setup.back')}
            </Button>
            <Button
              variant="primary"
              onClick={handleStartInterview}
              loading={loading}
            >
              {loading ? t('setup.analyzing') : t('setup.generateQuestions')}
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3: Review & Start */}
      {step === 3 && analysisData && (
        <>
          <Card className={styles.card}>
            <h2>{t('setup.reviewTitle')}</h2>
            <div className={styles.reviewInfo}>
              <Badge variant="primary">{analysisData.questions?.length || numQuestions} Questions</Badge>
              <Badge>{analysisData.domain}</Badge>
              <Badge>{analysisData.job_role}</Badge>
              <Badge>{analysisData.programming_language || programmingLanguage}</Badge>
            </div>
          </Card>

          {/* Resume vs JD Analysis - THE KEY DIFFERENTIATOR */}
          {/* <Card className={styles.analysisCard}> */}
            {/* <h3>📊 Resume Match Analysis</h3> */}
            {/* <p className={styles.analysisNote}>
              How well your resume aligns with the job description
            </p> */}
            
            {/* <div className={styles.analysisGrid}>
              <div className={styles.analysisItem}>
                <span className={styles.label}>Matched Skills</span>
                <span className={styles.value}>
                  {analysisData.skill_match?.matched_skills?.length || 0}
                </span>
              </div>
              <div className={styles.analysisItem}>
                <span className={styles.label}>Missing Skills</span>
                <span className={styles.value}>
                  {analysisData.skill_match?.missing_skills?.length || 0}
                </span>
              </div>
              <div className={styles.analysisItem}>
                <span className={styles.label}>ATS Score</span>
                <span className={styles.value}>
                  {analysisData.skill_match?.ats_score || 0}%
                </span>
              </div>
            </div> */}
          {/* </Card> */}

          <div className={styles.actions}>
            <Button
              variant="secondary"
              onClick={() => setStep(2)}
            >
              {t('setup.backToEdit')}
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmStart}
              size="lg"
            >
              {t('setup.startInterview')}
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
