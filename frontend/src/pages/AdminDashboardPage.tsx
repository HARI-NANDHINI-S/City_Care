import React, { useState, useEffect, useRef } from 'react';
import { analyticsService } from '../services/api';
import { AnalyticsDashboardData } from '../types';
import { LayoutDashboard, AlertOctagon, CheckCircle2, Clock, Activity, Building, ShieldCheck, ArrowUpRight, TrendingUp, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const fadeUp = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

// Animated counter hook
function useCountUp(target: number, duration = 1200) {
  const [count, setCount] = useState(0);
  const startTime = useRef<number | null>(null);
  useEffect(() => {
    if (target === 0) return;
    const step = (ts: number) => {
      if (!startTime.current) startTime.current = ts;
      const elapsed = ts - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      setCount(Math.round(progress * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    return () => { startTime.current = null; };
  }, [target, duration]);
  return count;
}

const StatCard: React.FC<{
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
  sub?: string;
  delay?: number;
}> = ({ label, value, icon: Icon, color, sub, delay = 0 }) => {
  const count = useCountUp(value);
  return (
    <motion.div
      initial="hidden" animate="visible"
      variants={fadeUp}
      transition={{ delay, duration: 0.4 }}
      className="bg-civic-card border border-civic-border rounded-2xl p-5 flex flex-col gap-3 hover:border-slate-600 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-4 h-4" />
        </div>
        <ArrowUpRight className="w-4 h-4 text-slate-600" />
      </div>
      <div>
        <div className="text-3xl font-bold text-white font-mono">{count}</div>
        <div className="text-xs font-medium text-slate-300 mt-0.5">{label}</div>
        {sub && <div className="text-[11px] text-slate-500 mt-1">{sub}</div>}
      </div>
    </motion.div>
  );
};

const CHART_COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316'];

const darkTooltipStyle = {
  contentStyle: { background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', color: '#f8fafc', fontSize: 12 },
  cursor: { fill: 'rgba(6,182,212,0.05)' },
};

export const AdminDashboardPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    analyticsService.getDashboardStats()
      .then(setData)
      .catch(() => setError('Failed to load dashboard analytics'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="h-8 w-64 bg-slate-800 rounded-lg animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-28 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
          <div className="h-64 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[40vh]">
        <div className="text-center space-y-3">
          <AlertOctagon className="w-10 h-10 text-red-400 mx-auto" />
          <p className="text-red-400 font-medium">{error || 'No data available'}</p>
          <button onClick={() => window.location.reload()} className="px-4 py-2 bg-civic-card border border-civic-border rounded-lg text-sm text-slate-300 hover:bg-slate-800 transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const categoryData = Object.entries(data.issues_by_category).map(([name, value]) => ({ name, value }));
  const severityData = Object.entries(data.issues_by_severity).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-[10px] font-mono tracking-wider mb-2">
            <ShieldCheck className="w-3 h-3" /> ADMINISTRATOR COMMAND CENTER
          </div>
          <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Real-time municipal infrastructure intelligence</p>
        </div>
        <Link to="/admin/issues" className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium bg-purple-600 hover:bg-purple-500 text-white text-sm transition-all shadow-lg shadow-purple-600/20">
          <LayoutDashboard className="w-4 h-4" /> Manage Issues
        </Link>
      </motion.div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Issues" value={data.total_issues} icon={Activity} color="bg-cyan-500/10 text-cyan-400" sub="All municipal zones" delay={0} />
        <StatCard label="Open Issues" value={data.open_issues} icon={Clock} color="bg-amber-500/10 text-amber-400" sub="Awaiting action" delay={0.06} />
        <StatCard label="Critical Urgency" value={data.critical_issues_count} icon={AlertOctagon} color="bg-red-500/10 text-red-400" sub="Priority score > 80" delay={0.12} />
        <StatCard label="In Progress" value={data.in_progress_issues} icon={Zap} color="bg-blue-500/10 text-blue-400" sub="Active repair crews" delay={0.18} />
        <StatCard label="Resolved" value={data.resolved_issues} icon={CheckCircle2} color="bg-emerald-500/10 text-emerald-400" sub="Completed tickets" delay={0.24} />
        <StatCard label="Category Types" value={Object.keys(data.issues_by_category).length} icon={TrendingUp} color="bg-purple-500/10 text-purple-400" sub="Defect categories" delay={0.30} />
        <StatCard label="Departments" value={data.department_performance.length} icon={Building} color="bg-indigo-500/10 text-indigo-400" sub="Municipal bodies" delay={0.36} />
        <StatCard label="Resolution Rate" value={Math.round((data.resolved_issues / Math.max(data.total_issues, 1)) * 100)} icon={ShieldCheck} color="bg-teal-500/10 text-teal-400" sub="% tickets resolved" delay={0.42} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ delay: 0.3 }} className="bg-civic-card border border-civic-border rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-200 mb-5 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
            Issue Category Distribution
          </h3>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="50%" height={180}>
              <PieChart>
                <Pie data={categoryData} dataKey="value" cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3}>
                  {categoryData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={darkTooltipStyle.contentStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {categoryData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-2 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-slate-400 truncate flex-1">{item.name}</span>
                  <span className="text-slate-200 font-mono font-medium">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Severity Distribution */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ delay: 0.36 }} className="bg-civic-card border border-civic-border rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-slate-200 mb-5 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
            Severity Level Distribution
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={severityData} barSize={32}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={darkTooltipStyle.contentStyle} cursor={darkTooltipStyle.cursor} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {severityData.map((item, i) => {
                  const c = item.name === 'CRITICAL' ? '#ef4444' : item.name === 'HIGH' ? '#f97316' : item.name === 'MEDIUM' ? '#eab308' : '#10b981';
                  return <Cell key={i} fill={c} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Department Performance Table */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ delay: 0.4 }} className="bg-civic-card border border-civic-border rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-civic-border flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Building className="w-4 h-4 text-purple-400" />
            Department Performance
          </h3>
          <Link to="/admin/analytics" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
            Full Analytics <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-civic-bg text-slate-500 uppercase tracking-wide font-medium border-b border-civic-border">
              <tr>
                <th className="py-3 px-5">Department</th>
                <th className="py-3 px-4">Assigned</th>
                <th className="py-3 px-4">Pending</th>
                <th className="py-3 px-4">In Progress</th>
                <th className="py-3 px-4">Resolved</th>
                <th className="py-3 px-4">Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-civic-border text-slate-300">
              {data.department_performance.map((dept, i) => (
                <motion.tr
                  key={dept.department_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.45 + i * 0.05 }}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="py-3.5 px-5 font-medium text-white">{dept.department_name}</td>
                  <td className="py-3.5 px-4 font-mono">{dept.total_assigned}</td>
                  <td className="py-3.5 px-4 text-amber-400 font-mono">{dept.pending}</td>
                  <td className="py-3.5 px-4 text-cyan-400 font-mono">{dept.in_progress}</td>
                  <td className="py-3.5 px-4 text-emerald-400 font-mono">{dept.resolved}</td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${dept.resolution_rate}%` }} />
                      </div>
                      <span className="text-emerald-400 font-mono font-semibold">{dept.resolution_rate}%</span>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};
