import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Menu, X, User, LogOut, ChevronDown, Sparkles } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/interviews', label: 'Interviews' },
  { to: '/analytics', label: 'Analytics' }
];

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [openMenu, setOpenMenu] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    logout();
    setShowProfile(false);
    setOpenMenu(false);
    navigate('/login');
  };

  return (
    <nav
      className={`fixed inset-x-0 top-0 z-40 transition-all duration-300 ease-in-out ${
        scrolled
          ? 'border-b border-slate-200/80 bg-white/85 shadow-sm backdrop-blur-xl'
          : 'bg-slate-50/70 backdrop-blur'
      }`}
    >
      <div className="app-container flex h-16 items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <span className="rounded-xl border border-indigo-200 bg-indigo-50 p-1.5 text-indigo-600">
            <Sparkles className="h-4 w-4" />
          </span>
          <span>AI Interviewer</span>
        </Link>

        {isAuthenticated ? (
          <>
            <div className="hidden items-center gap-2 md:flex">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `group relative rounded-full px-4 py-2 text-sm font-medium transition-all duration-300 ease-in-out ${
                      isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:text-slate-900'
                    }`
                  }
                >
                  {item.label}
                  <span className="absolute inset-x-4 -bottom-0.5 h-0.5 origin-left scale-x-0 rounded-full bg-indigo-500 transition-transform duration-300 ease-in-out group-hover:scale-x-100" />
                </NavLink>
              ))}
            </div>

            <div className="relative hidden md:block">
              <button
                type="button"
                onClick={() => setShowProfile((prev) => !prev)}
                className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 transition-all duration-300 ease-in-out hover:shadow-md"
              >
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                  <User className="h-4 w-4" />
                </span>
                <span className="max-w-24 truncate">{user?.name || 'Profile'}</span>
                <ChevronDown className="h-4 w-4" />
              </button>

              {showProfile ? (
                <div className="absolute right-0 mt-2 w-48 rounded-2xl border border-slate-200 bg-white p-2 shadow-card">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-red-500 transition-all duration-300 ease-in-out hover:bg-red-50"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              ) : null}
            </div>

            <button
              type="button"
              onClick={() => setOpenMenu((prev) => !prev)}
              className="rounded-xl border border-slate-200 bg-white p-2 text-slate-700 md:hidden"
            >
              {openMenu ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </>
        ) : (
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-full px-4 py-2 text-sm font-medium text-slate-600 transition-all duration-300 ease-in-out hover:text-slate-900"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-all duration-300 ease-in-out hover:scale-105 hover:bg-indigo-500"
            >
              Register
            </Link>
          </div>
        )}
      </div>

      {isAuthenticated && openMenu ? (
        <div className="border-t border-slate-200 bg-white px-6 py-4 md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col gap-3">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setOpenMenu(false)}
                className={({ isActive }) =>
                  `rounded-xl px-3 py-2 text-sm font-medium transition-all duration-300 ease-in-out ${
                    isActive ? 'bg-indigo-50 text-indigo-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-xl px-3 py-2 text-left text-sm font-medium text-red-500 transition-all duration-300 ease-in-out hover:bg-red-50"
            >
              Logout
            </button>
          </div>
        </div>
      ) : null}
    </nav>
  );
};
