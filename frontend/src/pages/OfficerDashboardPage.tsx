import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { issueService } from '../services/api';
import { Issue, IssueStatus } from '../types';
import { useAuth } from '../context/AuthContext';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { Building, CheckCircle2, Clock, Eye, AlertCircle, Zap, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeUp = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } };

export const OfficerDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  const fetchDepartmentIssues = async () => {
    setLoading(true);
    try {
      const data = await issueService.listIssues({ dept_id: user?.department_id || undefined });
      setIssues(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDepartmentIssues(); }, [user]);

  const handleStatusUpdate = async (issueId: number, nextStatus: IssueStatus) => {
    setUpdating(issueId);
    try {
      await issueService.updateStatus(issueId, nextStatus, `Updated by officer ${user?.full_name}`);
      await fetchDepartmentIssues();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setUpdating(null);
    }
  };

  const pending = issues.filter(i => ![IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED, IssueStatus.CLOSED].includes(i.status));
  const inProgress = issues.filter(i => i.status === IssueStatus.IN_PROGRESS);
  const resolved = issues.filter(i => [IssueStatus.RESOLVED, IssueStatus.CLOSED].includes(i.status));

  const stats = [
    { label: 'Total Assigned', value: issues.length, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: 'Pending Review', value: pending.length, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'In Progress', value: inProgress.length, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Resolved', value: resolved.length, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ];

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-mono tracking-wider mb-2">
          <Building className="w-3 h-3" /> DEPARTMENT OFFICER PORTAL
        </div>
        <h1 className="text-2xl font-bold text-white">Department Task Queue</h1>
        <p className="text-sm text-slate-400 mt-0.5">Review assigned tickets, dispatch repair teams, and mark issues resolved</p>
      </motion.div>

      {/* Stats Row */}
      <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div key={i} variants={fadeUp} className="bg-civic-card border border-civic-border rounded-xl p-4 flex items-center gap-3">
            <div className={`w-9 h-9 rounded-lg ${s.bg} ${s.color} flex items-center justify-center font-bold text-lg font-mono`}>
              {s.value}
            </div>
            <div className="text-xs text-slate-400 leading-snug">{s.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Issue Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : issues.length === 0 ? (
        <motion.div initial="hidden" animate="visible" variants={fadeUp}
          className="bg-civic-card border border-civic-border rounded-2xl p-14 text-center">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white">All Clear</h3>
          <p className="text-sm text-slate-400 mt-1">No issues currently assigned to your department.</p>
        </motion.div>
      ) : (
        <motion.div initial="hidden" animate="visible"
          variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {issues.map((issue) => {
            const imgUrl = issue.images?.[0]?.annotated_image_path || issue.images?.[0]?.original_image_path;
            const isUpdating = updating === issue.id;
            return (
              <motion.div key={issue.id} variants={fadeUp}
                className="bg-civic-card border border-civic-border rounded-2xl overflow-hidden flex flex-col hover:border-slate-600 transition-colors">
                {imgUrl && (
                  <div className="h-40 bg-slate-900 relative overflow-hidden">
                    <img src={imgUrl} alt={issue.title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-civic-card/80 to-transparent" />
                    <div className="absolute top-2 right-2"><StatusBadge status={issue.status} /></div>
                    <div className="absolute bottom-2 left-2 text-[10px] font-mono text-cyan-300 bg-civic-bg/80 px-2 py-0.5 rounded border border-cyan-500/20">
                      #{issue.id}
                    </div>
                  </div>
                )}
                <div className="p-4 flex-1 flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-[10px] font-mono text-cyan-400/80 uppercase">{issue.issue_type}</div>
                      <h3 className="text-sm font-semibold text-white mt-0.5 line-clamp-1">{issue.title}</h3>
                    </div>
                    <PriorityBadge score={issue.priority_score} severity={issue.severity} showScore={false} />
                  </div>

                  {issue.address && (
                    <p className="text-xs text-slate-500 line-clamp-1">{issue.address}</p>
                  )}

                  <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Clock className="w-3 h-3" />
                    {new Date(issue.created_at).toLocaleDateString()}
                    {issue.duplicate_count > 0 && (
                      <span className="ml-auto text-amber-400">{issue.duplicate_count} dup.</span>
                    )}
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                      <span>Progress</span><span>{issue.progress_percentage || 0}%</span>
                    </div>
                    <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-cyan-500 rounded-full transition-all" style={{ width: `${issue.progress_percentage || 0}%` }} />
                    </div>
                  </div>

                  <div className="mt-auto grid grid-cols-2 gap-2">
                    <button
                      onClick={() => handleStatusUpdate(issue.id, IssueStatus.IN_PROGRESS)}
                      disabled={issue.status === IssueStatus.IN_PROGRESS || isUpdating}
                      className="py-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-medium hover:bg-cyan-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isUpdating ? <span className="inline-block w-3 h-3 border border-cyan-400 border-t-transparent rounded-full animate-spin" /> : 'In Progress'}
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(issue.id, IssueStatus.RESOLVED)}
                      disabled={issue.status === IssueStatus.RESOLVED || isUpdating}
                      className="py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium hover:bg-emerald-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isUpdating ? <span className="inline-block w-3 h-3 border border-emerald-400 border-t-transparent rounded-full animate-spin" /> : 'Resolved'}
                    </button>
                  </div>

                  <Link to={`/issue/${issue.id}`}
                    className="flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-civic-bg border border-civic-border text-slate-400 text-xs font-medium hover:text-slate-200 hover:bg-slate-800 transition-colors">
                    <Eye className="w-3 h-3" /> View Full Details <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
};
