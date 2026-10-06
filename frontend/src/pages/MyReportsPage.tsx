import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { citizenService } from '../services/api';
import { Issue, IssueStatus, IssueType, SeverityLevel } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { Search, MapPin, FileText, AlertOctagon, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export const MyReportsPage: React.FC = () => {
  const [items, setItems] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [category, setCategory] = useState('');
  const [severity, setSeverity] = useState('');

  const load = () => {
    setLoading(true);
    citizenService.reports({
      search: search || undefined,
      status_filter: status || undefined,
      category: category || undefined,
      severity: severity || undefined,
    })
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(load, [status, category, severity]);

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white">My Reports</h1>
        <p className="text-sm text-slate-400 mt-0.5">All civic issues you have personally reported</p>
      </motion.div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="bg-civic-card border border-civic-border rounded-xl p-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input value={search} onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && load()}
            placeholder="Search title..." className="w-full bg-civic-bg border border-civic-border rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all" />
        </div>
        <select value={status} onChange={e => setStatus(e.target.value)} className="bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50">
          <option value="">All statuses</option>
          {Object.values(IssueStatus).map(v => <option key={v} value={v}>{v.replace('_', ' ')}</option>)}
        </select>
        <select value={category} onChange={e => setCategory(e.target.value)} className="bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50">
          <option value="">All categories</option>
          {Object.values(IssueType).map(v => <option key={v} value={v}>{v}</option>)}
        </select>
        <select value={severity} onChange={e => setSeverity(e.target.value)} className="bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50">
          <option value="">All severity</option>
          {Object.values(SeverityLevel).map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </motion.div>

      {/* Results */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <div key={i} className="h-24 bg-civic-card border border-civic-border rounded-xl animate-pulse" />)}
        </div>
      ) : items.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-civic-card border border-civic-border rounded-2xl p-14 text-center">
          <FileText className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 font-medium">No reports match these filters</p>
          <p className="text-sm text-slate-500 mt-1">Try adjusting the filters above</p>
        </motion.div>
      ) : (
        <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.06 } } }} className="space-y-3">
          {items.map((issue) => (
            <motion.div key={issue.id}
              variants={{ hidden: { opacity: 0, x: -12 }, visible: { opacity: 1, x: 0 } }}
              className="bg-civic-card border border-civic-border rounded-xl p-4 flex flex-col md:flex-row md:items-center gap-4 hover:border-slate-600 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono text-slate-500">#{issue.id}</span>
                  <span className="text-[10px] font-mono text-cyan-400/70 uppercase">{issue.issue_type}</span>
                </div>
                <div className="text-sm font-semibold text-white truncate">{issue.title}</div>
                <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                  <MapPin className="w-3 h-3" />
                  <span className="truncate">{issue.address || `${issue.latitude?.toFixed(4)}, ${issue.longitude?.toFixed(4)}`}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-wrap">
                <PriorityBadge score={issue.priority_score} severity={issue.severity} showScore={false} />
                <StatusBadge status={issue.status} />
              </div>

              <div className="w-full md:w-32">
                <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                  <span>Progress</span><span>{issue.progress_percentage || 0}%</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${issue.progress_percentage || 0}%` }} />
                </div>
              </div>

              <div className="flex gap-2 shrink-0">
                <Link to={`/issue/${issue.id}`} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-civic-bg border border-civic-border text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
                  Details <ChevronRight className="w-3 h-3" />
                </Link>
                <Link to={`/issue/${issue.id}/track`} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-400 hover:bg-cyan-500/20 transition-colors">
                  Track
                </Link>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
};
