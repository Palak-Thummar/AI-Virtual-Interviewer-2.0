/**
 * Results Page
 * Shows interview results with resume analysis - THE KEY DIFFERENTIATOR
 */

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { interviewAPI, parseApiError } from '../services/api';
import { Card, Badge, Spinner, ProgressBar, Button, Alert } from '../components/UI';
import { useNavigate } from 'react-router-dom';
import styles from './Results.module.css';

export const ResultsPage = () => {
  const { t } = useTranslation();
  const { interviewId } = useParams();
  const navigate = useNavigate();

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadResults = async () => {
      try {
        // Try to complete/get results first
        let data;
        try {
          const response = await interviewAPI.complete(interviewId);
          data = response.data || response;
        } catch (completeErr) {
          // If complete fails, try fetching the interview directly
          const getResponse = await interviewAPI.get(interviewId);
          data = getResponse.data || getResponse;
          
          // If the interview is already completed, use its data
          const computedScore = Number(data?.overall_score ?? data?.score ?? data?.total_score ?? 0);
          if (data && (data.status === 'completed' || computedScore > 0)) {
            // Format the interview data into results format
            data = {
              ...data,
              interview_id: data.id,
              overall_score: computedScore,
              job_role: data.job_role || data.role || '',
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
        const errorMsg = parseApiError(err, 'Failed to load results. Redirecting to dashboard...');
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
        <span>{t('results.generating')}</span>
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
            {t('results.goDashboardNow')}
          </Button>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className={styles.center}>
        <Alert variant="error">{t('results.notFound')}</Alert>
        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/dashboard')}>
            {t('results.goDashboard')}
          </Button>
        </div>
      </div>
    );
  }

  const overallScore = Number(results?.overall_score ?? results?.score ?? results?.total_score ?? 0);
  let scoreColor = 'error';
  if (overallScore >= 80) scoreColor = 'success';
  else if (overallScore >= 65) scoreColor = 'warning';

  return (
    <div className={styles.container}>
      {/* Overall Score */}
      <div className={styles.scoreSection}>
        <Card className={styles.scoreCard}>
          <div className={styles.scoreCircle}>
            <div className={`${styles.score} ${styles[`score-${scoreColor}`]}`}>
              {Math.round(overallScore)}
            </div>
            <span className={styles.scoreLabel}>{t('results.overallScore')}</span>
          </div>
        </Card>

        <Card className={styles.infoCard}>
          <h2>{results.job_role || results.role || '-'}</h2>
          <span className={styles.domain}>{results.domain}</span>
          <div className={styles.badges}>
            <Badge variant="primary">
              {t('results.questionsAnswered', { count: results.question_scores?.length || 0 })}
            </Badge>
            <Badge variant="success">{t('results.interviewComplete')}</Badge>
          </div>
        </Card>
      </div>

      {/* RESUME MATCH ANALYSIS - KEY DIFFERENTIATOR */}
      <Card className={styles.analysisCard}>
        <h3 className={styles.sectionTitle}>{t('results.resumeMatch')}</h3>
        <p className={styles.subtitle}>
          {t('results.resumeMatchSubtitle')}
        </p>

        <div className={styles.metricsGrid}>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('results.atsScore')}</span>
            <ProgressBar value={results.skill_match?.ats_score || 0} max={100} />
            <span className={styles.metricValue}>
              {Math.round(results.skill_match?.ats_score || 0)}%
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('results.matchedSkills')}</span>
            <div className={styles.skillsList}>
              {results.skill_match?.matched_skills?.slice(0, 3).map((skill, idx) => (
                <Badge key={idx} variant="success">{skill}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {t('results.skillsMatched', { count: results.skill_match?.matched_skills?.length || 0 })}
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('results.missingSkills')}</span>
            <div className={styles.skillsList}>
              {results.skill_match?.missing_skills?.slice(0, 3).map((skill, idx) => (
                <Badge key={idx} variant="warning">{skill}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {t('results.skillsToDevelop', { count: results.skill_match?.missing_skills?.length || 0 })}
            </span>
          </div>

          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('results.keywordGaps')}</span>
            <div className={styles.skillsList}>
              {results.skill_match?.keyword_gaps?.slice(0, 3).map((kw, idx) => (
                <Badge key={idx} variant="warning">{kw}</Badge>
              ))}
            </div>
            <span className={styles.count}>
              {t('results.keywordsToAdd', { count: results.skill_match?.keyword_gaps?.length || 0 })}
            </span>
          </div>
        </div>

        {results.skill_match?.experience_gap && (
          <div className={styles.experienceGap}>
            <span className={styles.label}>{t('results.experienceGap')}</span>
            <span>{results.skill_match.experience_gap}</span>
          </div>
        )}
      </Card>

      {/* Resume Suggestions */}
      <Card className={styles.suggestionsCard}>
        <h3 className={styles.sectionTitle}>{t('results.resumeSuggestions')}</h3>

        <div className={styles.suggestionsGrid}>
          <div className={styles.suggestionGroup}>
            <h4>{t('results.improvements')}</h4>
            <ul>
              {results.resume_suggestions?.improvement_suggestions?.slice(0, 5).map((sugg, idx) => (
                <li key={idx}>✓ {sugg}</li>
              ))}
            </ul>
          </div>

          <div className={styles.suggestionGroup}>
            <h4>{t('results.atsTips')}</h4>
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
        <h3 className={styles.sectionTitle}>{t('results.questionPerformance')}</h3>

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
                <strong>{t('results.strengths')}</strong> {q.strengths.join(', ')}
              </div>
            )}
            {q.improvements?.length > 0 && (
              <div className={styles.improvements}>
                <strong>{t('results.toImprove')}</strong> {q.improvements.join(', ')}
              </div>
            )}
          </div>
        ))}
      </Card>

      {/* Actions */}
      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          {t('results.backDashboard')}
        </Button>
        <Button variant="primary" onClick={() => navigate('/setup')}>
          {t('results.takeAnother')}
        </Button>
      </div>
    </div>
  );
};
