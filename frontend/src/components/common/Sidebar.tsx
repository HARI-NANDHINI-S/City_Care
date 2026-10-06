import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Map as MapIcon, ClipboardList, Activity, Settings, User, AlertTriangle,
  FileText, CheckCircle2, Cpu, ChevronLeft, ChevronRight, Brain, BarChart3, PlusCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  if (!user) return null;

  const isAdmin = user.role === UserRole.ADMIN;
  const isOfficer = user.role === UserRole.OFFICER;
  const isCitizen = user.role === UserRole.CITIZEN;

  const navGroups = [
    {
      title: 'OVERVIEW',
      items: [
        { name: 'Command Center', path: isAdmin ? '/admin' : isOfficer ? '/officer' : '/dashboard', icon: LayoutDashboard },
      ]
    },
    ...(isCitizen ? [{
      title: 'CITIZEN',
      items: [
        { name: 'Report Issue', path: '/report', icon: PlusCircle },
        { name: 'My Reports', path: '/my-reports', icon: FileText },
      ]
    }] : []),
    {
      title: 'CIVIC ISSUES',
      items: [
        ...(isAdmin ? [{ name: 'All Issues', path: '/admin/issues', icon: ClipboardList }] : []),
        { name: 'Geographic Map', path: '/map', icon: MapIcon },
      ]
    },
    ...(isAdmin ? [{
      title: 'INTELLIGENCE',
      items: [
        { name: 'Analytics', path: '/admin/analytics', icon: BarChart3 },
        { name: 'Model Intelligence', path: '/model-intelligence', icon: Brain },
      ]
    }] : []),
  ];

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 64 : 256 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="bg-civic-card border-r border-civic-border hidden md:flex flex-col h-[calc(100vh-64px)] overflow-hidden relative"
    >
      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute top-3 right-3 z-10 w-6 h-6 flex items-center justify-center rounded-md bg-civic-border/50 text-slate-400 hover:text-white hover:bg-civic-border transition-colors"
      >
        {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>

      <div className="flex-1 py-6 overflow-y-auto">
        {navGroups.map((group, idx) => (
          <div key={idx} className="mb-6 px-3">
            {!collapsed && (
              <motion.h3
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="px-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 font-mono"
              >
                {group.title}
              </motion.h3>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    title={collapsed ? item.name : undefined}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                        isActive
                          ? 'bg-cyan-500/10 text-cyan-400 font-medium border border-cyan-500/20'
                          : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent'
                      } ${collapsed ? 'justify-center' : ''}`
                    }
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    {!collapsed && <span className="truncate">{item.name}</span>}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Bottom Section */}
      {!collapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-3 border-t border-civic-border"
        >
          <div className="px-3 py-2 rounded-lg bg-cyan-500/5 border border-cyan-500/10">
            <div className="text-[10px] font-mono text-cyan-400/60 uppercase tracking-wider">System</div>
            <div className="text-xs text-slate-300 font-medium mt-0.5">{user.full_name}</div>
            <div className="text-[10px] text-slate-500 font-mono">{user.role}</div>
          </div>
        </motion.div>
      )}
    </motion.aside>
  );
};
