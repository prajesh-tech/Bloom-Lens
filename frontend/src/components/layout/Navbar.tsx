import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { BrainCircuit, UploadCloud, History, Settings, Home, Menu, X, Sun, Moon } from 'lucide-react';
import { Badge } from '../common/Badge';
import { useTheme } from '../../context/ThemeContext';

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const isMock = import.meta.env.VITE_USE_MOCK_API !== 'false';

  const navItems = [
    { label: 'Overview', path: '/', icon: Home },
    { label: 'Analyze Paper', path: '/analyze', icon: UploadCloud },
    { label: 'History', path: '/history', icon: History },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200/80 dark:border-slate-800 shadow-xs transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <NavLink to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-slate-900 dark:bg-sky-950 flex items-center justify-center text-white group-hover:bg-slate-800 transition-colors shadow-xs">
              <BrainCircuit className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">BloomLens</span>
              <span className="block text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest -mt-1">V1 Analytics</span>
            </div>
          </NavLink>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`
                }
              >
                <item.icon className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Right Header Status, Theme Toggle & Badges */}
          <div className="flex items-center gap-3">
            {/* Desktop Dark / Light Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
              title={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
              aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
            >
              {theme === 'light' ? <Moon className="w-5 h-5 text-slate-600" /> : <Sun className="w-5 h-5 text-amber-400" />}
            </button>

            <div className="hidden sm:flex items-center gap-3">
              {isMock ? (
                <Badge variant="warning" size="sm" className="font-mono text-[11px]">
                  ⚡ Mock Mode (1.5s delay)
                </Badge>
              ) : (
                <Badge variant="success" size="sm" className="font-mono text-[11px]">
                  ● Backend Connected
                </Badge>
              )}
            </div>
          </div>

          {/* Mobile Hamburger Toggle */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
              aria-label="Toggle Mobile Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium ${
                  isActive ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`
              }
            >
              <item.icon className="w-5 h-5 text-slate-500 dark:text-slate-400" />
              <span>{item.label}</span>
            </NavLink>
          ))}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between px-3 py-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Theme</span>
            <button
              type="button"
              onClick={toggleTheme}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-sm font-medium text-slate-700 dark:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
              aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
            >
              {theme === 'light' ? (
                <>
                  <Moon className="w-4 h-4 text-slate-600" /> Dark Mode
                </>
              ) : (
                <>
                  <Sun className="w-4 h-4 text-amber-400" /> Light Mode
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
