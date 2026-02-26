import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Sparkles } from 'lucide-react';

export const RegisterPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});

    const newErrors = {};
    if (!name) newErrors.name = 'Name is required';
    if (!email) newErrors.email = 'Email is required';
    if (!password) newErrors.password = 'Password is required';
    if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    if (password && password.length < 6) newErrors.password = 'Password must be at least 6 characters';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const result = await register(name, email, password);
    if (result.success) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="grid min-h-screen bg-slate-50 lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-indigo-600" />
        <div className="absolute -right-20 top-10 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute bottom-16 left-10 h-72 w-72 rounded-full bg-indigo-300/20 blur-3xl" />
        <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1 text-sm backdrop-blur">
            <Sparkles className="h-4 w-4" />
            AI Interviewer Platform
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl font-bold tracking-tight">Build confidence with every practice round.</h1>
            <p className="max-w-md text-white/85">Create your account and unlock role-specific mock interviews, analytics, and targeted improvement plans.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-card"
        >
          <h2 className="headline-2">Create account</h2>
          <p className="mt-1 body-text">Set up your workspace and start your first interview session.</p>

          {error ? (
            <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-500">{error}</div>
          ) : null}

          <form onSubmit={handleSubmit} autoComplete="off" className="mt-6 space-y-5">
            <div className="relative">
              <input
                id="full-name"
                type="text"
                name="register-name"
                autoComplete="off"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder=" "
                className="peer h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pt-4 text-slate-800 outline-none transition-all duration-300 ease-in-out focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
              <label htmlFor="full-name" className="pointer-events-none absolute left-4 top-3 text-sm text-slate-500 transition-all duration-300 ease-in-out peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-focus:top-2 peer-focus:text-xs peer-focus:text-indigo-600">
                Full Name
              </label>
              {errors.name ? <p className="mt-1 text-xs text-red-500">{errors.name}</p> : null}
            </div>

            <div className="relative">
              <input
                id="email"
                type="email"
                name="register-email"
                autoComplete="off"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder=" "
                className="peer h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pt-4 text-slate-800 outline-none transition-all duration-300 ease-in-out focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
              <label htmlFor="email" className="pointer-events-none absolute left-4 top-3 text-sm text-slate-500 transition-all duration-300 ease-in-out peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-focus:top-2 peer-focus:text-xs peer-focus:text-indigo-600">
                Email
              </label>
              {errors.email ? <p className="mt-1 text-xs text-red-500">{errors.email}</p> : null}
            </div>

            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                name="register-password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder=" "
                className="peer h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pt-4 pr-11 text-slate-800 outline-none transition-all duration-300 ease-in-out focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
              <label htmlFor="password" className="pointer-events-none absolute left-4 top-3 text-sm text-slate-500 transition-all duration-300 ease-in-out peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-focus:top-2 peer-focus:text-xs peer-focus:text-indigo-600">
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-3 text-slate-500 transition-all duration-300 ease-in-out hover:text-slate-700"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
              {errors.password ? <p className="mt-1 text-xs text-red-500">{errors.password}</p> : null}
            </div>

            <div className="relative">
              <input
                id="confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                name="register-confirm-password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder=" "
                className="peer h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pt-4 pr-11 text-slate-800 outline-none transition-all duration-300 ease-in-out focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
              <label htmlFor="confirm-password" className="pointer-events-none absolute left-4 top-3 text-sm text-slate-500 transition-all duration-300 ease-in-out peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-focus:top-2 peer-focus:text-xs peer-focus:text-indigo-600">
                Confirm Password
              </label>
              <button
                type="button"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                className="absolute right-3 top-3 text-slate-500 transition-all duration-300 ease-in-out hover:text-slate-700"
              >
                {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
              {errors.confirmPassword ? <p className="mt-1 text-xs text-red-500">{errors.confirmPassword}</p> : null}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:scale-105 hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-indigo-600 transition-all duration-300 ease-in-out hover:text-indigo-500">
              Login here
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};
