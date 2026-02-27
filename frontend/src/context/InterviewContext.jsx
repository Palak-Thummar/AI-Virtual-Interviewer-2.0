/**
 * Interview Context
 * Manages interview state and data
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';

const InterviewContext = createContext(null);
const PROD_FALLBACK_API = 'https://ai-virtual-interviewer-2-0.onrender.com';
const configuredBase = (import.meta.env.VITE_API_SERVER_URL || '').trim().replace(/\/api\/?$/i, '');
const isLocalhostUrl = (url) => /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(url);

const SERVER_BASE = (
  import.meta.env.PROD && (!configuredBase || isLocalhostUrl(configuredBase))
    ? PROD_FALLBACK_API
    : (configuredBase || 'http://localhost:8000')
).replace(/\/$/, '');
const interviewClient = axios.create({
  baseURL: SERVER_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const InterviewProvider = ({ children }) => {
  const [interview, setInterview] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Create new interview
  const createInterview = useCallback(async (setupData, token) => {
    setLoading(true);
    setError(null);
    try {
      const response = await interviewClient.post('/api/interview/create', setupData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setInterview(response.data);
      setCurrentQuestion(0);
      return { success: true, data: response.data };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create interview';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Submit answer
  const submitAnswer = useCallback(async (interviewId, answerData, token) => {
    setLoading(true);
    setError(null);
    try {
      const response = await interviewClient.post(
        `/api/interview/${interviewId}/submit-answer`,
        answerData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      return { success: true, evaluation: response.data };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to submit answer';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Complete interview
  const completeInterview = useCallback(async (interviewId, token) => {
    setLoading(true);
    setError(null);
    try {
      const response = await interviewClient.post(
        `/api/interview/${interviewId}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      return { success: true, results: response.data };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to complete interview';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Get interview details
  const getInterview = useCallback(async (interviewId, token) => {
    try {
      const response = await interviewClient.get(
        `/api/interview/${interviewId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setInterview(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch interview:', err);
      return null;
    }
  }, []);

  const value = {
    interview,
    currentQuestion,
    loading,
    error,
    createInterview,
    submitAnswer,
    completeInterview,
    getInterview,
    setCurrentQuestion
  };

  return (
    <InterviewContext.Provider value={value}>
      {children}
    </InterviewContext.Provider>
  );
};

export const useInterview = () => {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error('useInterview must be used within InterviewProvider');
  }
  return context;
};
