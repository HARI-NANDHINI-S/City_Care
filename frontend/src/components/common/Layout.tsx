import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../context/AuthContext';
import { useLocation } from 'react-router-dom';

const noSidebarPaths = ['/', '/login', '/register'];

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const showSidebar = isAuthenticated && !noSidebarPaths.includes(location.pathname);

  return (
    <div className="min-h-screen bg-civic-bg text-slate-100 flex flex-col font-sans">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        {showSidebar && <Sidebar />}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <footer className="bg-civic-bg border-t border-civic-border py-4 text-center text-xs text-slate-500 shrink-0">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-3">
          <div>© 2026 CivicVision AI — Intelligent Civic Issue Detection & Maintenance Prioritisation System</div>
          <div className="flex gap-3 text-[11px]">
            <span className="text-cyan-400/70 font-medium">FastAPI</span>
            <span className="text-slate-700">•</span>
            <span className="text-emerald-400/70 font-medium">YOLO & OpenCV</span>
            <span className="text-slate-700">•</span>
            <span className="text-purple-400/70 font-medium">React & Leaflet</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
