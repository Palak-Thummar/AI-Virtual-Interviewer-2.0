/**
 * Interview Setup Page - THE KEY DIFFERENTIATOR
 * User uploads resume, pastes JD, and sets up interview
 */

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { resumeAPI, interviewAPI, settingsAPI } from '../services/api';
import { Button, Input, TextArea, Select, Alert, Card, Spinner, Badge } from '../components/UI';
import styles from './InterviewSetup.module.css';

export const InterviewSetupPage = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  
  // Resume upload
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeId, setResumeId] = useState('');
  const [resumeLoading, setResumeLoading] = useState(false);
  
  // Interview setup
  const [jobRole, setJobRole] = useState('');
  const [domain, setDomain] = useState('');
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
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setResumeLoading(false);
    }
  };

  // Start interview
  const handleStartInterview = async () => {
    if (!jobRole) {
      setError('Please enter job role');
      return;
    }
    if (!domain) {
      setError('Please select domain');
      return;
    }
    if (!jobDescription) {
      setError('Please paste job description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Analyze resume vs JD
      const analysisResponse = await interviewAPI.create({
        job_role: jobRole,
        domain,
        job_description: jobDescription,
        resume_id: resumeId,
        num_questions: numQuestions
      });

      setAnalysisData(analysisResponse.data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create interview');
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
    { value: 'Backend', label: 'Backend Development' },
    { value: 'Frontend', label: 'Frontend Development' },
    { value: 'Fullstack', label: 'Full Stack Development' },
    { value: 'DevOps', label: 'DevOps / Infrastructure' },
    { value: 'Data', label: 'Data Engineering / ML' },
    { value: 'Mobile', label: 'Mobile Development' }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🚀 Start Your Interview</h1>
        <p>We'll analyze your resume against the job description to create personalized questions</p>
      </div>

      <div className={styles.steps}>
        <div className={`${styles.step} ${step >= 1 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>1</span>
          <span>Resume</span>
        </div>
        <div className={`${styles.step} ${step >= 2 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>2</span>
          <span>Details</span>
        </div>
        <div className={`${styles.step} ${step >= 3 ? styles.active : ''}`}>
          <span className={styles.stepNumber}>3</span>
          <span>Review</span>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Step 1: Resume Upload */}
      {step === 1 && (
        <Card className={styles.card}>
          <h2>📄 Upload Your Resume</h2>
          <p className={styles.description}>
            We'll analyze your resume against the job description to tailor questions
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
                  {resumeFile ? resumeFile.name : 'Click to upload or drag and drop'}
                </span>
                <span className={styles.uploadNote}>PDF or DOCX (10MB max)</span>
              </div>
            </label>
          </div>

          {resumeLoading && (
            <div className={styles.loading}>
              <Spinner size="sm" />
              <span>Parsing your resume...</span>
            </div>
          )}

          {resumeId && (
            <div className={styles.success}>
              ✅ Resume uploaded successfully!
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Job Details */}
      {step === 2 && (
        <Card className={styles.card}>
          <h2>💼 Job Details</h2>

          <Input
            label="Job Role / Title"
            value={jobRole}
            onChange={(e) => setJobRole(e.target.value)}
            placeholder="e.g., Senior Backend Engineer"
          />

          <Select
            label="Technical Domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            options={domainOptions}
          />

          <Input
            type="number"
            label="Number of Questions"
            value={numQuestions}
            onChange={(e) => setNumQuestions(Math.min(20, Math.max(1, parseInt(e.target.value))))}
            min="1"
            max="20"
          />

          <TextArea
            label="Paste Job Description"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the full job description here..."
            rows={8}
          />

          <div className={styles.actions}>
            <Button
              variant="secondary"
              onClick={() => setStep(1)}
            >
              ← Back
            </Button>
            <Button
              variant="primary"
              onClick={handleStartInterview}
              loading={loading}
            >
              {loading ? 'Analyzing...' : 'Generate Questions →'}
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3: Review & Start */}
      {step === 3 && analysisData && (
        <>
          <Card className={styles.card}>
            <h2>✨ Interview Ready</h2>
            <div className={styles.reviewInfo}>
              <Badge variant="primary">{analysisData.questions?.length || numQuestions} Questions</Badge>
              <Badge>{analysisData.domain}</Badge>
              <Badge>{analysisData.job_role}</Badge>
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
              ← Back to Edit
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmStart}
              size="lg"
            >
              Start Interview 🎯
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
