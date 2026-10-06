import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';
import { MapPin, PlusCircle, LayoutDashboard, LogOut, LogIn, Cpu, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Navbar: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 bg-civic-card/95 backdrop-blur-xl border-b border-civic-border h-16">
      <div className="h-full px-4 sm:px-6 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group shrink-0">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-emerald-400 p-[2px] shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-shadow">
            <div className="w-full h-full bg-civic-bg rounded-[6px] flex items-center justify-center">
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
          </div>
          <div className="hidden sm:block">
            <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent leading-none">
              CivicVision AI
            </span>
            <div className="text-[9px] font-mono text-slate-500 tracking-wider">COMMAND CENTER v2.0</div>
          </div>
        </Link>

        {/* Desktop Nav Links - minimal */}
        <div className="hidden md:flex items-center gap-1">
          <Link
            to="/map"
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isActive('/map') ? 'bg-cyan-500/10 text-cyan-400' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" /> Map
          </Link>

          {isAuthenticated && user?.role === UserRole.CITIZEN && (
            <Link to="/report" className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isActive('/report') ? 'bg-emerald-500/10 text-emerald-400' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}>
              <PlusCircle className="w-3.5 h-3.5" /> Report
            </Link>
          )}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <div className="hidden sm:flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs font-medium text-slate-200 leading-tight">{user?.full_name}</div>
                  <div className="text-[10px] font-mono text-cyan-400/70">{user?.role}</div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-civic-border flex items-center justify-center">
                  <span className="text-xs font-bold text-cyan-400">{user?.full_name?.charAt(0)}</span>
                </div>
              </div>
              <button
                onClick={() => { logout(); navigate('/login'); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 border border-civic-border transition-all"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors">
                <LogIn className="w-3.5 h-3.5" /> Log In
              </Link>
              <Link to="/register" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20 transition-all">
                Get Started
              </Link>
            </div>
          )}

          {/* Mobile Menu Toggle */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 text-slate-400 hover:text-white">
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-civic-card border-b border-civic-border overflow-hidden"
          >
            <div className="p-4 space-y-2">
              <Link to="/map" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                <MapPin className="w-4 h-4 inline mr-2" /> Public Map
              </Link>
              {isAuthenticated && user?.role === UserRole.CITIZEN && (
                <>
                  <Link to="/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                    <LayoutDashboard className="w-4 h-4 inline mr-2" /> Dashboard
                  </Link>
                  <Link to="/report" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                    <PlusCircle className="w-4 h-4 inline mr-2" /> Report Issue
                  </Link>
                </>
              )}
              {isAuthenticated && user?.role === UserRole.ADMIN && (
                <>
                  <Link to="/admin" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                    <LayoutDashboard className="w-4 h-4 inline mr-2" /> Command Center
                  </Link>
                  <Link to="/admin/issues" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                    All Issues
                  </Link>
                </>
              )}
              {isAuthenticated && user?.role === UserRole.OFFICER && (
                <Link to="/officer" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800">
                  <LayoutDashboard className="w-4 h-4 inline mr-2" /> Department Dashboard
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};
