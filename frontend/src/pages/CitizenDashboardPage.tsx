import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { citizenService } from '../services/api';
import { Issue } from '../types';
import { PlusCircle, MapPin, FileText, Clock, ChevronRight, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { StatusBadge } from '../components/common/StatusBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';

const fadeUp = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } };

const fmt = (d?: string | null) => d ? new Date(d).toLocaleDateString() : '—';

export const CitizenDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [reports, setReports] = useState<Issue[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([citizenService.stats(), citizenService.reports({ limit: 6 })])
      .then(([s, r]) => { setStats(s); setReports(r); })
      .catch(() => setError('Unable to load your dashboard. Please try again.'));
  }, []);

  if (error) return (
    <div className="p-8 flex items-center justify-center min-h-[40vh]">
      <div className="text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
        <p className="text-red-400 font-medium">{error}</p>
        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-civic-card border border-civic-border rounded-lg text-sm text-slate-300 hover:bg-slate-800 transition-colors">Retry</button>
      </div>
    </div>
  );

  if (!stats) return (
    <div className="p-8 space-y-6">
      <div className="h-8 w-64 bg-slate-800 rounded-lg animate-pulse" />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => <div key={i} className="h-20 bg-civic-card border border-civic-border rounded-xl animate-pulse" />)}
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-48 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />)}
      </div>
    </div>
  );

  const statCards = [
    { label: 'Total Reports', value: stats.total_issues ?? 0, color: 'text-cyan-400' },
    { label: 'Under Review', value: stats.under_review ?? 0, color: 'text-purple-400' },
    { label: 'Assigned', value: stats.assigned ?? 0, color: 'text-indigo-400' },
    { label: 'In Progress', value: stats.in_progress ?? 0, color: 'text-blue-400' },
    { label: 'Resolved', value: stats.resolved ?? 0, color: 'text-emerald-400' },
    { label: 'High Priority', value: stats.high_priority ?? 0, color: 'text-amber-400' },
  ];

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-mono tracking-wider mb-2">
            CITIZEN PORTAL
          </div>
          <h1 className="text-2xl font-bold text-white">My Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Track every civic issue you have reported</p>
        </div>
        <Link to="/report" className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-cyan-500 to-emerald-500 text-slate-950 text-sm transition-all shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-emerald-400">
          <PlusCircle className="w-4 h-4" /> Report New Issue
        </Link>
      </motion.div>

      {/* Stats */}
      <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((s, i) => (
          <motion.div key={i} variants={fadeUp} className="bg-civic-card border border-civic-border rounded-xl p-4 text-center hover:border-slate-600 transition-colors">
            <div className={`text-2xl font-bold font-mono ${s.color}`}>{s.value}</div>
            <div className="text-[11px] text-slate-500 mt-1">{s.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Actions */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ delay: 0.2 }}
        className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/report" className="group flex items-center gap-4 p-4 bg-civic-card border border-civic-border rounded-xl hover:border-cyan-500/30 transition-all">
          <div className="w-10 h-10 bg-cyan-500/10 rounded-lg flex items-center justify-center text-cyan-400 group-hover:bg-cyan-500/20 transition-colors">
            <PlusCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-medium text-white">Report Issue</div>
            <div className="text-[11px] text-slate-500">Upload and submit</div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-600 ml-auto group-hover:text-slate-400 transition-colors" />
        </Link>
        <Link to="/my-reports" className="group flex items-center gap-4 p-4 bg-civic-card border border-civic-border rounded-xl hover:border-purple-500/30 transition-all">
          <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center text-purple-400 group-hover:bg-purple-500/20 transition-colors">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-medium text-white">My Reports</div>
            <div className="text-[11px] text-slate-500">View all submissions</div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-600 ml-auto group-hover:text-slate-400 transition-colors" />
        </Link>
        <Link to="/map" className="group flex items-center gap-4 p-4 bg-civic-card border border-civic-border rounded-xl hover:border-emerald-500/30 transition-all">
          <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500/20 transition-colors">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-medium text-white">Public Map</div>
            <div className="text-[11px] text-slate-500">Geographic overview</div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-600 ml-auto group-hover:text-slate-400 transition-colors" />
        </Link>
      </motion.div>

      {/* Recent Reports */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-white">Recent Reports</h2>
          <Link to="/my-reports" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
            View all <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        {reports.length === 0 ? (
          <motion.div initial="hidden" animate="visible" variants={fadeUp}
            className="bg-civic-card border border-civic-border rounded-2xl p-12 text-center">
            <FileText className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No reports yet</p>
            <p className="text-sm text-slate-500 mt-1">Submit your first civic issue report</p>
            <Link to="/report" className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-sm hover:bg-cyan-500/20 transition-colors">
              <PlusCircle className="w-4 h-4" /> Report Issue
            </Link>
          </motion.div>
        ) : (
          <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
            className="grid md:grid-cols-2 gap-4">
            {reports.map((issue) => (
              <motion.div key={issue.id} variants={fadeUp}
                className="bg-civic-card border border-civic-border rounded-2xl p-5 flex flex-col gap-3 hover:border-slate-600 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-[10px] font-mono text-slate-500">Issue #{issue.id}</div>
                    <h3 className="text-sm font-semibold text-white mt-0.5 truncate">{issue.title}</h3>
                    <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                      <MapPin className="w-3 h-3 shrink-0" />
                      <span className="truncate">{issue.address || `${issue.latitude}, ${issue.longitude}`}</span>
                    </div>
                  </div>
                  <StatusBadge status={issue.status} />
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  <PriorityBadge score={issue.priority_score} severity={issue.severity} />
                  <span className="text-[11px] text-slate-500">{issue.department?.name || 'Dept. pending'}</span>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                    <span>Resolution Progress</span><span>{issue.progress_percentage || 0}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500 rounded-full transition-all" style={{ width: `${issue.progress_percentage || 0}%` }} />
                  </div>
                </div>

                {issue.latest_update && (
                  <p className="text-xs text-slate-400 bg-civic-bg/50 rounded-lg px-3 py-2 border border-civic-border line-clamp-1">
                    {issue.latest_update}
                  </p>
                )}

                <div className="flex gap-2 mt-auto">
                  <Link to={`/issue/${issue.id}`} className="flex-1 text-center py-1.5 rounded-lg bg-civic-bg border border-civic-border text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
                    View Details
                  </Link>
                  <Link to={`/issue/${issue.id}/track`} className="flex-1 text-center py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-400 hover:bg-cyan-500/20 transition-colors">
                    Track Issue
                  </Link>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
};
