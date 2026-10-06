import React, { useState, useEffect, useRef } from 'react';
import { analyticsService } from '../services/api';
import { AnalyticsDashboardData } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend } from 'recharts';
import { BarChart3, PieChart as PieIcon, AlertOctagon, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

const CHART_COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#f97316'];
const darkTooltip = {
  contentStyle: { background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', color: '#f8fafc', fontSize: 11 },
  cursor: { fill: 'rgba(6,182,212,0.04)' },
};

const ChartCard: React.FC<{ title: string; subtitle?: string; icon: React.ElementType; children: React.ReactNode; delay?: number }> = ({ title, subtitle, icon: Icon, children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
    className="bg-civic-card border border-civic-border rounded-2xl p-6"
  >
    <div className="flex items-center gap-2 mb-5">
      <Icon className="w-4 h-4 text-cyan-400" />
      <div>
        <div className="text-sm font-semibold text-white">{title}</div>
        {subtitle && <div className="text-[11px] text-slate-500">{subtitle}</div>}
      </div>
    </div>
    {children}
  </motion.div>
);

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    analyticsService.getDashboardStats()
      .then(setData)
      .catch(() => setError('Failed to load analytics data'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      <div className="h-8 w-48 bg-slate-800 rounded animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {[...Array(6)].map((_, i) => <div key={i} className="h-72 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />)}
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="p-8 flex items-center justify-center min-h-[40vh]">
      <div className="text-center space-y-3">
        <AlertOctagon className="w-10 h-10 text-red-400 mx-auto" />
        <p className="text-red-400">{error || 'No data'}</p>
        <button onClick={() => window.location.reload()} className="px-4 py-2 bg-civic-card border border-civic-border rounded-lg text-sm text-slate-300 hover:bg-slate-800">Retry</button>
      </div>
    </div>
  );

  const categoryData = Object.entries(data.issues_by_category).map(([name, value]) => ({ name: name.split(' ').slice(0, 2).join(' '), value }));
  const severityData = Object.entries(data.issues_by_severity).map(([name, value]) => ({ name, value }));
  const statusData = Object.entries(data.issues_by_status).map(([name, value]) => ({ name: name.replace('_', ' '), value }));
  const deptData = data.department_performance.map(d => ({
    name: d.department_name.split(' ').slice(0, 2).join(' '),
    Assigned: d.total_assigned, Pending: d.pending, Resolved: d.resolved
  }));

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-mono tracking-wider mb-2">
          ANALYTICS & INTELLIGENCE
        </div>
        <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
        <p className="text-sm text-slate-400 mt-0.5">Real-time infrastructure intelligence from backend data</p>
      </motion.div>

      {/* Summary row */}
      <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Issues', value: data.total_issues, color: 'text-cyan-400' },
          { label: 'Open Issues', value: data.open_issues, color: 'text-amber-400' },
          { label: 'Critical', value: data.critical_issues_count, color: 'text-red-400' },
          { label: 'Resolved', value: data.resolved_issues, color: 'text-emerald-400' },
        ].map((s, i) => (
          <motion.div key={i} variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
            className="bg-civic-card border border-civic-border rounded-xl p-4 text-center">
            <div className={`text-2xl font-bold font-mono ${s.color}`}>{s.value}</div>
            <div className="text-[11px] text-slate-500 mt-1">{s.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Category Pie */}
        <ChartCard title="Category Distribution" subtitle="By AI detection class" icon={PieIcon} delay={0.1}>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={categoryData} dataKey="value" cx="50%" cy="50%" outerRadius={80} innerRadius={40} paddingAngle={3} label={({ percent }) => percent ? `${(percent * 100).toFixed(0)}%` : ''} labelLine={false}>
                {categoryData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={darkTooltip.contentStyle} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-1.5">
            {categoryData.map((item, i) => (
              <div key={item.name} className="flex items-center gap-2 text-[11px]">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                <span className="text-slate-400 flex-1 truncate">{item.name}</span>
                <span className="text-slate-200 font-mono">{item.value}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Severity Bar */}
        <ChartCard title="Severity Distribution" subtitle="Risk level breakdown" icon={BarChart3} delay={0.15}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={severityData} barSize={36}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={darkTooltip.contentStyle} cursor={darkTooltip.cursor} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {severityData.map((item, i) => {
                  const c = item.name === 'CRITICAL' ? '#ef4444' : item.name === 'HIGH' ? '#f97316' : item.name === 'MEDIUM' ? '#eab308' : '#10b981';
                  return <Cell key={i} fill={c} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Status Bar */}
        <ChartCard title="Status Distribution" subtitle="Current ticket states" icon={TrendingUp} delay={0.2}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={statusData} layout="vertical" barSize={12}>
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" width={90} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={darkTooltip.contentStyle} cursor={darkTooltip.cursor} />
              <Bar dataKey="value" fill="#06b6d4" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Department Performance Bar Chart */}
      <ChartCard title="Department Performance" subtitle="Assigned vs Pending vs Resolved" icon={BarChart3} delay={0.25}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={deptData} barSize={20} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={darkTooltip.contentStyle} cursor={darkTooltip.cursor} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            <Bar dataKey="Assigned" fill="#06b6d4" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Pending" fill="#f59e0b" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Resolved" fill="#10b981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Resolution Rate Table */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="bg-civic-card border border-civic-border rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-civic-border">
          <div className="text-sm font-semibold text-white">Department Resolution Rates</div>
        </div>
        <div className="divide-y divide-civic-border">
          {data.department_performance.map((dept, i) => (
            <div key={dept.department_id} className="px-5 py-4 flex items-center gap-4">
              <div className="w-6 text-[10px] font-mono text-slate-600">{i + 1}</div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">{dept.department_name}</div>
                <div className="text-[11px] text-slate-500">{dept.total_assigned} total assigned</div>
              </div>
              <div className="flex items-center gap-3 w-48">
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }} animate={{ width: `${dept.resolution_rate}%` }}
                    transition={{ duration: 0.8, delay: 0.3 + i * 0.1, ease: 'easeOut' }}
                    className="h-full bg-emerald-500 rounded-full"
                  />
                </div>
                <span className="text-emerald-400 font-mono text-xs font-semibold w-10 text-right">{dept.resolution_rate}%</span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};
