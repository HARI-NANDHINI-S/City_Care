import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { issueService, departmentService } from '../services/api';
import { Issue, Department, IssueStatus, IssueType } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { Search, RefreshCw, Eye, AlertOctagon, ChevronUp, ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';

type SortField = 'id' | 'priority_score' | 'created_at';

export const AdminIssueManagementPage: React.FC = () => {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [sortField, setSortField] = useState<SortField>('priority_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const data = await issueService.listIssues({
        search: search.trim() || undefined,
        status_filter: statusFilter !== 'ALL' ? statusFilter : undefined,
        type_filter: typeFilter !== 'ALL' ? typeFilter : undefined,
      });
      setIssues(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
    departmentService.listDepartments().then(setDepartments).catch(console.error);
  }, []);

  const handleSort = (field: SortField) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const sorted = [...issues].sort((a, b) => {
    const mult = sortDir === 'asc' ? 1 : -1;
    if (sortField === 'priority_score') return mult * (a.priority_score - b.priority_score);
    if (sortField === 'id') return mult * (a.id - b.id);
    return mult * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  });

  const SortIcon = ({ field }: { field: SortField }) => (
    sortField === field
      ? (sortDir === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />)
      : <ChevronDown className="w-3 h-3 opacity-30" />
  );

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white">Issue Management</h1>
        <p className="text-sm text-slate-400 mt-0.5">Priority queue, inspect duplicates, reassign departments</p>
      </motion.div>

      {/* Filter Bar */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="bg-civic-card border border-civic-border rounded-xl p-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          <input type="text" placeholder="Search title or address..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchIssues()}
            className="w-full bg-civic-bg border border-civic-border rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all" />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50">
          <option value="ALL">All Statuses</option>
          {Object.values(IssueStatus).map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50">
          <option value="ALL">All Categories</option>
          {Object.values(IssueType).map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          onClick={fetchIssues}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium transition-colors">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Apply
        </motion.button>
      </motion.div>

      {/* Table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
        className="bg-civic-card border border-civic-border rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-civic-bg text-slate-500 uppercase tracking-wide font-medium border-b border-civic-border">
              <tr>
                <th className="py-3 px-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('id')}>
                  <span className="flex items-center gap-1">ID <SortIcon field="id" /></span>
                </th>
                <th className="py-3 px-4">Category & Title</th>
                <th className="py-3 px-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('priority_score')}>
                  <span className="flex items-center gap-1">Priority <SortIcon field="priority_score" /></span>
                </th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('created_at')}>
                  <span className="flex items-center gap-1">Reported <SortIcon field="created_at" /></span>
                </th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-civic-border text-slate-300">
              {loading ? (
                [...Array(8)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(7)].map((_, j) => (
                      <td key={j} className="py-3 px-4"><div className="h-4 bg-slate-800 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : sorted.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-14 text-slate-500">
                    <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-slate-700" />
                    No issues match the current filters
                  </td>
                </tr>
              ) : (
                sorted.map((issue, i) => (
                  <motion.tr key={issue.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-cyan-400/80">#{issue.id}</td>
                    <td className="py-3 px-4 max-w-xs">
                      <div className="text-[10px] text-slate-500 uppercase font-mono">{issue.issue_type}</div>
                      <div className="font-medium text-white truncate mt-0.5">{issue.title}</div>
                      <div className="text-[10px] text-slate-500 truncate">{issue.address || `GPS (${issue.latitude?.toFixed(4)}, ${issue.longitude?.toFixed(4)})`}</div>
                    </td>
                    <td className="py-3 px-4"><PriorityBadge score={issue.priority_score} severity={issue.severity} /></td>
                    <td className="py-3 px-4 text-xs text-purple-300/80">{issue.department?.name || 'Unassigned'}</td>
                    <td className="py-3 px-4"><StatusBadge status={issue.status} /></td>
                    <td className="py-3 px-4 font-mono text-slate-500">{new Date(issue.created_at).toLocaleDateString()}</td>
                    <td className="py-3 px-4 text-right">
                      <Link to={`/issue/${issue.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-civic-bg hover:bg-slate-800 text-cyan-400 text-xs font-medium border border-civic-border transition-colors">
                        <Eye className="w-3 h-3" /> Inspect
                      </Link>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {!loading && sorted.length > 0 && (
          <div className="px-4 py-3 border-t border-civic-border text-xs text-slate-500 flex items-center justify-between">
            <span>Showing {sorted.length} issues</span>
            <span className="font-mono">Sorted by {sortField.replace('_', ' ')} {sortDir}</span>
          </div>
        )}
      </motion.div>
    </div>
  );
};
