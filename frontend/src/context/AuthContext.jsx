import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authAPI, parseApiError } from '../services/api';

const AuthContext = createContext(null);

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
        const response = await authAPI.verifyToken(storedToken);
        
        setUser(response.data);
        setToken(storedToken);
      } catch (err) {
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
      const response = await authAPI.register(name.trim(), email.trim().toLowerCase(), password.trim());
      
      const { access_token, user } = response.data;
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      return { success: true, user };
    } catch (err) {
      const message = parseApiError(err, 'Registration failed.');
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
      const response = await authAPI.login(email.trim().toLowerCase(), password.trim());
      
      const { access_token, user } = response.data;
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      return { success: true, user };
    } catch (err) {
      const message = parseApiError(err, 'Login failed.');
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
      const response = await authAPI.verifyToken(token);
      setUser(response.data);
      return response.data;
    } catch {
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
