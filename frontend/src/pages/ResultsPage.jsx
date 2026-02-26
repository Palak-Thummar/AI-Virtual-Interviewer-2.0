/**
 * Results Page
 * Shows interview results with resume analysis - THE KEY DIFFERENTIATOR
 */

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { interviewAPI } from '../services/api';
import { Card, Badge, Spinner, ProgressBar, Button, Alert } from '../components/UI';
import { useNavigate } from 'react-router-dom';
import styles from './Results.module.css';

export const ResultsPage = () => {
  const { interviewId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadResults = async () => {
      try {
        console.log('Fetching results for interview:', interviewId);
        
        // Try to complete/get results first
        let data;
        try {
          const response = await interviewAPI.complete(interviewId);
          data = response.data || response;
          console.log('Results received from complete:', data);
        } catch (completeErr) {
          // If complete fails, try fetching the interview directly
          console.log('Complete failed, trying get approach...');
          const getResponse = await interviewAPI.get(interviewId);
          data = getResponse.data || getResponse;
          console.log('Interview data received from get:', data);
          
          // If the interview is already completed, use its data
          if (data && (data.status === 'completed' || data.overall_score > 0)) {
            // Format the interview data into results format
            data = {
              ...data,
              interview_id: data.id,
              question_scores: data.answers?.map((ans, idx) => ({
                question_id: ans.question_id,
                score: ans.score || 0,
                feedback: ans.feedback || '',
                strengths: ans.strengths || [],
                improvements: ans.improvements || []
              })) || [],
              skill_match: data.skill_match || {
                matched_skills: [],
                missing_skills: [],
                ats_score: 0,
                keyword_gaps: [],
                experience_gap: ''
              },
              resume_suggestions: data.resume_suggestions || {
                improvement_suggestions: [],
                ats_optimization_tips: []
              }
            };
          } else {
            throw completeErr;
          }
        }
        
        setResults(data);
      } catch (err) {
        console.error('Load results error:', {
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
          message: err.message,
          config: err.config
        });
        const errorMsg = err.response?.data?.detail || 'Failed to load results. Redirecting to dashboard...';
        setError(errorMsg);
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      } finally {
        setLoading(false);
      }
    };
    loadResults();
  }, [interviewId, navigate]);

  if (loading) {
    return (
      <div className={styles.center}>
        <Spinner size="lg" />
        <span>Generating your results...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <Alert variant="error">
          {error}
        </Alert>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/dashboard')}>
            Go to Dashboard Now
          </Button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className={styles.center}>
        <Alert variant="error">Results not found</Alert>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/dashboard')}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const scorePercentage = (results.overall_score / 100) * 100;
  let scoreColor = 'error';
  if (results.overall_score >= 80) scoreColor = 'success';
  else if (results.overall_score >= 65) scoreColor = 'warning';

  return (
    <div className={styles.container}>
      {/* Overall Score */}
      <div className={styles.scoreSection}>
        <Card className={styles.scoreCard}>
          <div className={styles.scoreCircle}>
            <div className={`${styles.score} ${styles[`score-${scoreColor}`]}`}>
              {Math.round(results.overall_score)}
            </div>
            <span className={styles.scoreLabel}>Overall Score</span>
          </div>
        </Card>

        <Card className={styles.infoCard}>
          <h2>{results.job_role}</h2>
          <span className={styles.domain}>{results.domain}</span>
          <div className={styles.badges}>
            <Badge variant="primary">
              {results.question_scores?.length || 0} Questions Answered
            </Badge>
            <Badge variant="success">Interview Complete</Badge>
          </div>
        </Card>
      </div>

      {/* RESUME MATCH ANALYSIS - KEY DIFFERENTIATOR */}
      <Card className={styles.analysisCard}>
        <h3 className={styles.sectionTitle}>📊 Resume Match Analysis</h3>
        <p className={styles.subtitle}>
          How well your resume aligns with the job requirements
        </p>

        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>ATS Score</span>
            <ProgressBar value={results.skill_match?.ats_score || 0} max={100} />
            <span className={styles.metricValue}>
              {Math.round(results.skill_match?.ats_score || 0)}%
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>Matched Skills</span>
            <div className={styles.skillsList}>
              {results.skill_match?.matched_skills?.slice(0, 3).map((skill, idx) => (
                <Badge key={idx} variant="success">{skill}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {results.skill_match?.matched_skills?.length || 0} skills matched
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>Missing Skills</span>
            <div className={styles.skillsList}>
              {results.skill_match?.missing_skills?.slice(0, 3).map((skill, idx) => (
                <Badge key={idx} variant="warning">{skill}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {results.skill_match?.missing_skills?.length || 0} skills to develop
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>Keyword Gaps</span>
            <div className={styles.skillsList}>
              {results.skill_match?.keyword_gaps?.slice(0, 3).map((kw, idx) => (
                <Badge key={idx} variant="warning">{kw}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {results.skill_match?.keyword_gaps?.length || 0} keywords to add
            </span>
          </div>
        </div>

        {results.skill_match?.experience_gap && (
          <div className={styles.experienceGap}>
            <span className={styles.label}>Experience Gap:</span>
            <span>{results.skill_match.experience_gap}</span>
          </div>
        )}
      </Card>

      {/* Resume Suggestions */}
      <Card className={styles.suggestionsCard}>
        <h3 className={styles.sectionTitle}>🎯 Resume Improvement Suggestions</h3>

        <div className={styles.suggestionsGrid}>
          <div className={styles.suggestionGroup}>
            <h4>Improvements</h4>
            <ul>
              {results.resume_suggestions?.improvement_suggestions?.slice(0, 5).map((sugg, idx) => (
                <li key={idx}>✓ {sugg}</li>
              ))}
            </ul>
          </div>

          <div className={styles.suggestionGroup}>
            <h4>ATS Optimization Tips</h4>
            <ul>
              {results.resume_suggestions?.ats_optimization_tips?.slice(0, 5).map((tip, idx) => (
                <li key={idx}>⚡ {tip}</li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Question Performance */}
      <Card className={styles.performanceCard}>
        <h3 className={styles.sectionTitle}>💬 Question Performance</h3>

        {results.question_scores?.map((q, idx) => (
          <div key={idx} className={styles.questionResult}>
            <div className={styles.questionHeader}>
              <span className={styles.qIndex}>Q{idx + 1}</span>
              <div className={styles.scoreBar}>
                <ProgressBar value={q.score} max={100} />
                <span className={styles.qScore}>{Math.round(q.score)}/100</span>
              </div>
            </div>
            {q.feedback && (
              <p className={styles.feedback}>{q.feedback}</p>
            )}
            {q.strengths?.length > 0 && (
              <div className={styles.strengths}>
                <strong>Strengths:</strong> {q.strengths.join(', ')}
              </div>
            )}
            {q.improvements?.length > 0 && (
              <div className={styles.improvements}>
                <strong>To improve:</strong> {q.improvements.join(', ')}
              </div>
            )}
          </div>
        ))}
      </Card>

      {/* Actions */}
      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
        <Button variant="primary" onClick={() => navigate('/setup')}>
          Take Another Interview
        </Button>
      </div>
    </div>
  );
};
