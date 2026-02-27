/**
 * API Service
 * Centralized API client for backend communication
 */

import axios from 'axios';

const PROD_FALLBACK_API = 'https://ai-virtual-interviewer-2-0.onrender.com';
const configuredBase = (import.meta.env.VITE_API_SERVER_URL || '').trim().replace(/\/api\/?$/i, '');
const isLocalhostUrl = (url) => /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(url);

const SERVER_BASE = (
  import.meta.env.PROD && (!configuredBase || isLocalhostUrl(configuredBase))
    ? PROD_FALLBACK_API
    : (configuredBase || 'http://localhost:8000')
).replace(/\/$/, '');
const API_BASE = `${SERVER_BASE}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Skip redirect if explicitly requested (used during token verification)
    if (error.config?.skipInterceptor) {
      return Promise.reject(error);
    }
    
    // Only redirect to login on 401 (unauthorized)
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      const currentPath = window.location.pathname;
      
      // Don't redirect if already on login/register page
      if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
        window.location.href = '/login';
      }
    }
    
    // For other errors (500, etc), let the component handle them
    return Promise.reject(error);
  }
);

// ============= AUTH ENDPOINTS =============
export const authAPI = {
  register: (name, email, password) =>
    api.post('/auth/register', { name, email, password }),
  
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  
  getProfile: () =>
    api.get('/auth/me'),
  
  refresh: () =>
    api.post('/auth/refresh')
};

// ============= RESUME ENDPOINTS =============
export const resumeAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  list: () =>
    api.get('/resume/my/list'),
  
  get: (resumeId) =>
    api.get(`/resume/${resumeId}`),

  rewrite: (payload) =>
    api.post('/resume/rewrite', payload),
  
  delete: (resumeId) =>
    api.delete(`/resume/${resumeId}`)
};

// ============= INTERVIEW ENDPOINTS =============
export const interviewAPI = {
  create: (setupData) =>
    api.post('/interview/create', setupData),

  generateCompanyInterview: (payload) =>
    api.post('/interview/company-generate', payload),
  
  get: (interviewId) =>
    api.get(`/interview/${interviewId}`),
  
  resume: (interviewId) =>
    api.get(`/interview/${interviewId}/resume`),
  
  submitAnswer: (interviewId, answerData) =>
    api.post(`/interview/${interviewId}/submit-answer`, answerData),

  submit: (interviewId, payload = {}) =>
    api.post(`/interview/${interviewId}/submit`, payload),
  
  complete: (interviewId) =>
    api.post(`/interview/${interviewId}/complete`)
  ,
  delete: (interviewId) =>
    api.delete(`/interview/${interviewId}`)
};

// ============= ANALYTICS ENDPOINTS =============
export const analyticsAPI = {
  getDashboard: () =>
    api.get('/analytics/dashboard'),

  getSummary: () =>
    api.get('/analytics/summary'),

  getCareerIntelligence: () =>
    api.get('/career-intelligence'),
  
  getFullAnalytics: () =>
    api.get('/analytics/full-analytics'),
  
  getDomainStats: (domain) =>
    api.get(`/analytics/domain/${domain}`),
  
  getSuggestions: () =>
    api.get('/analytics/suggestions'),
  
  getInterviewHistory: () =>
    api.get('/analytics/interviews'),

  getInterviewHistoryList: () =>
    api.get('/interviews')
};

// ============= ANSWER LAB ENDPOINTS =============
export const answerLabAPI = {
  analyze: (payload) =>
    api.post('/answer-lab/analyze', payload)
};

// ============= CODING PRACTICE ENDPOINTS =============
export const codingAPI = {
  getProblems: () =>
    api.get('/coding/problems'),

  submit: (payload) =>
    api.post('/coding/submit', payload)
};

// ============= SETTINGS ENDPOINTS =============
export const settingsAPI = {
  getProfile: () =>
    api.get('/settings/profile'),

  updateProfile: (payload) =>
    api.put('/settings/profile', payload),

  changePassword: (payload) =>
    api.put('/settings/change-password', payload),

  getPreferences: () =>
    api.get('/settings/preferences'),

  updatePreferences: (payload) =>
    api.put('/settings/preferences', payload),

  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  getResume: () =>
    api.get('/settings/resume'),

  deleteResume: () =>
    api.delete('/settings/resume'),

  getNotifications: () =>
    api.get('/settings/notifications'),

  updateNotifications: (payload) =>
    api.put('/settings/notifications', payload),

  exportData: () =>
    api.get('/settings/export-data'),

  deleteAccount: () =>
    api.delete('/settings/account')
};

export default api;
