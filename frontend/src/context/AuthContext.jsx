/**
 * Auth Context
 * Manages authentication state across the application
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);
const SERVER_BASE = 'http://localhost:8000';
const authClient = axios.create({
  baseURL: SERVER_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);  // Start as true
  const [error, setError] = useState(null);

  // Verify token on app load
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('token');
      
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        // Verify token directly without using the interceptor
        // This prevents redirect loops during token verification
        const response = await authClient.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${storedToken}` },
          timeout: 5000,
          // Disable the response interceptor for this request
          skipInterceptor: true
        });
        
        setUser(response.data);
        setToken(storedToken);
      } catch (err) {
        console.error('Token verification failed:', err.message);
        // Token is invalid, clear it
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, []);

  // Register user
  const register = useCallback(async (name, email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authClient.post('/api/auth/register', {
        name,
        email,
        password
      });
      
      const { access_token, user } = response.data;
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      return { success: true, user };
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Login user
  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authClient.post('/api/auth/login', {
        email,
        password
      });
      
      const { access_token, user } = response.data;
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      return { success: true, user };
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  // Logout user
  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  }, []);

  // Get current profile
  const getProfile = useCallback(async () => {
    if (!token) return null;
    try {
      const response = await authClient.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
        skipInterceptor: true
      });
      setUser(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch profile:', err);
      return null;
    }
  }, [token]);

  const value = {
    user,
    token,
    loading,
    error,
    register,
    login,
    logout,
    getProfile,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
