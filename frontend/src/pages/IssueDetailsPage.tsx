import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { issueService, departmentService } from '../services/api';
import { Issue, IssueStatus, Department } from '../types';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { MapPin, Cpu, Clock, Building, Shield, CheckCircle2, ArrowLeft, Send, AlertOctagon, Copy } from 'lucide-react';
import { motion } from 'framer-motion';

const STATUS_STEPS = [
  IssueStatus.REPORTED, IssueStatus.AI_ANALYZED, IssueStatus.UNDER_REVIEW,
  IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED, IssueStatus.CLOSED,
];

export const IssueDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();

  const [issue, setIssue] = useState<Issue | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newStatus, setNewStatus] = useState<IssueStatus>(IssueStatus.IN_PROGRESS);
  const [notes, setNotes] = useState('');
  const [selectedDeptId, setSelectedDeptId] = useState<number>(0);
  const [updating, setUpdating] = useState(false);

  const fetchIssue = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await issueService.getIssueById(parseInt(id));
      setIssue(data);
      setNewStatus(data.status);
      if (data.department_id) setSelectedDeptId(data.department_id);
    } catch {
      setError('Failed to load issue details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssue();
    departmentService.listDepartments().then(setDepartments).catch(console.error);
  }, [id]);

  const handleUpdateStatus = async () => {
    if (!issue) return;
    setUpdating(true);
    try {
      await issueService.updateStatus(issue.id, newStatus, notes);
      setNotes('');
      await fetchIssue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status.');
    } finally {
      setUpdating(false);
    }
  };

  const handleAssignDepartment = async () => {
    if (!issue || !selectedDeptId) return;
    setUpdating(true);
    try {
      await issueService.assignDepartment(issue.id, selectedDeptId, notes);
      setNotes('');
      await fetchIssue();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reassign department.');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return (
    <div className="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
      <div className="h-6 w-48 bg-slate-800 rounded animate-pulse" />
      <div className="h-24 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-96 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
        <div className="h-96 bg-civic-card border border-civic-border rounded-2xl animate-pulse" />
      </div>
    </div>
  );

  if (error || !issue) return (
    <div className="p-8 flex items-center justify-center min-h-[40vh]">
      <div className="text-center space-y-3">
        <AlertOctagon className="w-10 h-10 text-red-400 mx-auto" />
        <p className="text-red-400 font-medium">{error || 'Issue not found'}</p>
        <Link to="/map" className="text-cyan-400 text-sm hover:underline">← Back to Map</Link>
      </div>
    </div>
  );

  const currentStepIdx = STATUS_STEPS.indexOf(issue.status);
  const mainImage = issue.images?.[0];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb & Header */}
      <div>
        <Link to="/map" className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:underline mb-4">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Map
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="text-[11px] font-mono text-slate-500">#{issue.id}</span>
              <span className="text-[11px] font-mono text-cyan-400/80 uppercase">{issue.issue_type}</span>
              <PriorityBadge score={issue.priority_score} severity={issue.severity} />
              <StatusBadge status={issue.status} />
            </div>
            <h1 className="text-xl lg:text-2xl font-bold text-white">{issue.title}</h1>
            <p className="text-sm text-slate-400 flex items-center gap-1.5 mt-1">
              <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              {issue.address || `GPS (${issue.latitude?.toFixed(4)}, ${issue.longitude?.toFixed(4)})`}
            </p>
          </div>
          <Link to={`/issue/${issue.id}/track`} className="px-4 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-sm font-medium hover:bg-emerald-500/20 transition-colors">
            Track Progress
          </Link>
        </div>
      </div>

      {/* Status Stepper */}
      <div className="bg-civic-card border border-civic-border rounded-2xl p-5">
        <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-4">Lifecycle Progression</div>
        <div className="flex items-center overflow-x-auto gap-1 pb-1">
          {STATUS_STEPS.map((step, idx) => {
            const isPassed = idx <= currentStepIdx;
            const isCurrent = idx === currentStepIdx;
            return (
              <React.Fragment key={step}>
                <div className={`shrink-0 px-3 py-1.5 rounded-lg text-[10px] font-mono font-medium transition-all ${
                  isCurrent ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' :
                  isPassed ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                  'bg-civic-bg text-slate-600 border border-civic-border'
                }`}>
                  {step.replace(/_/g, ' ')}
                </div>
                {idx < STATUS_STEPS.length - 1 && (
                  <div className={`h-0.5 w-4 shrink-0 rounded-full ${idx < currentStepIdx ? 'bg-emerald-500' : 'bg-civic-border'}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: AI Analysis & History */}
        <div className="lg:col-span-2 space-y-6">
          {/* Image & AI Panel */}
          <div className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" /> AI Object Detection Analysis
            </h3>

            {mainImage && (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden border border-civic-border">
                  <img
                    src={mainImage.annotated_image_path || mainImage.original_image_path}
                    alt={issue.title}
                    className="w-full h-72 object-cover"
                  />
                  <div className="absolute top-3 left-3 bg-civic-bg/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-mono text-cyan-300 border border-cyan-500/20">
                    Confidence: {(issue.ai_confidence * 100).toFixed(1)}%
                  </div>
                  {mainImage.annotated_image_path && (
                    <div className="absolute bottom-3 left-3 bg-civic-bg/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-[10px] font-mono text-emerald-400 border border-emerald-500/20">
                      ✓ Bounding Box Overlay
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'AI Confidence', value: `${(issue.ai_confidence * 100).toFixed(1)}%`, color: 'text-emerald-400' },
                    { label: 'Priority Score', value: `${issue.priority_score}/100`, color: 'text-amber-400' },
                    { label: 'Linked Duplicates', value: `${issue.duplicate_count}`, color: 'text-cyan-400' },
                  ].map(item => (
                    <div key={item.label} className="bg-civic-bg border border-civic-border rounded-xl p-3 text-center">
                      <div className="text-[10px] text-slate-500">{item.label}</div>
                      <div className={`text-sm font-bold font-mono mt-1 ${item.color}`}>{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Location Info */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-civic-bg border border-civic-border rounded-xl p-3">
                <div className="text-[10px] text-slate-500 font-mono">LATITUDE</div>
                <div className="text-sm font-mono text-slate-200 mt-0.5">{issue.latitude?.toFixed(6)}</div>
              </div>
              <div className="bg-civic-bg border border-civic-border rounded-xl p-3">
                <div className="text-[10px] text-slate-500 font-mono">LONGITUDE</div>
                <div className="text-sm font-mono text-slate-200 mt-0.5">{issue.longitude?.toFixed(6)}</div>
              </div>
            </div>

            {issue.description && (
              <div className="bg-civic-bg border border-civic-border rounded-xl p-4">
                <div className="text-[10px] text-slate-500 font-mono mb-2">CITIZEN DESCRIPTION</div>
                <p className="text-sm text-slate-300 leading-relaxed">{issue.description}</p>
              </div>
            )}
          </div>

          {/* Audit Timeline */}
          <div className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" /> Audit Log
            </h3>
            <div className="relative space-y-1">
              <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-civic-border" />
              {issue.status_history.length === 0 ? (
                <p className="pl-8 text-xs text-slate-500">No history entries yet.</p>
              ) : issue.status_history.map((hist, i) => (
                <div key={hist.id} className="relative pl-8 pb-4">
                  <div className="absolute left-1.5 top-1 w-3 h-3 rounded-full bg-cyan-400 ring-4 ring-civic-card" />
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-cyan-300">{hist.new_status.replace(/_/g, ' ')}</span>
                    <span className="text-slate-500 font-mono">{new Date(hist.created_at).toLocaleString()}</span>
                  </div>
                  {hist.notes && <p className="text-xs text-slate-400 mt-0.5">{hist.notes}</p>}
                  <p className="text-[10px] text-slate-600 mt-0.5">by {hist.changed_by?.full_name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Department & Controls */}
        <div className="space-y-5">
          {/* Department Info */}
          <div className="bg-civic-card border border-civic-border rounded-2xl p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Building className="w-4 h-4 text-purple-400" /> Assigned Department
            </h3>
            {issue.department ? (
              <div className="bg-civic-bg border border-civic-border rounded-xl p-3 space-y-1">
                <div className="text-sm font-medium text-cyan-300">{issue.department.name}</div>
                <div className="text-xs font-mono text-slate-500">{issue.department.code}</div>
                {issue.department.contact_email && (
                  <div className="text-xs text-slate-500">{issue.department.contact_email}</div>
                )}
              </div>
            ) : (
              <div className="text-xs text-amber-400 bg-amber-500/10 p-3 rounded-xl border border-amber-500/20">
                No department assigned yet
              </div>
            )}
          </div>

          {/* Report Metadata */}
          <div className="bg-civic-card border border-civic-border rounded-2xl p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white">Report Info</h3>
            {[
              { label: 'Reported', value: new Date(issue.created_at).toLocaleString() },
              { label: 'Last Updated', value: new Date(issue.updated_at).toLocaleString() },
              { label: 'Severity', value: issue.severity },
              { label: 'Reporter ID', value: `#${issue.reporter_id}` },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between text-xs border-b border-civic-border pb-2 last:border-0 last:pb-0">
                <span className="text-slate-500">{item.label}</span>
                <span className="text-slate-300 font-mono">{item.value}</span>
              </div>
            ))}
          </div>

          {/* Admin/Officer Controls */}
          {user && (user.role === UserRole.ADMIN || user.role === UserRole.OFFICER) && (
            <div className="bg-civic-card border border-civic-border rounded-2xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" /> Control Panel
              </h3>

              <div className="space-y-3">
                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Update Status</label>
                  <select value={newStatus} onChange={(e) => setNewStatus(e.target.value as IssueStatus)}
                    className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-all">
                    {STATUS_STEPS.map(st => <option key={st} value={st}>{st.replace(/_/g, ' ')}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Notes</label>
                  <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)}
                    placeholder="Progress notes or dispatch details..."
                    className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all resize-none" />
                </div>
                <button onClick={handleUpdateStatus} disabled={updating}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-colors disabled:opacity-50">
                  {updating ? <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" /> : <Send className="w-3 h-3" />}
                  {updating ? 'Updating...' : 'Commit Status'}
                </button>
              </div>

              {user.role === UserRole.ADMIN && (
                <div className="pt-4 border-t border-civic-border space-y-3">
                  <div>
                    <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Reassign Department</label>
                    <select value={selectedDeptId} onChange={(e) => setSelectedDeptId(parseInt(e.target.value))}
                      className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-all">
                      <option value={0}>Select department...</option>
                      {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <button onClick={handleAssignDepartment} disabled={updating || !selectedDeptId}
                    className="w-full py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-colors disabled:opacity-50">
                    Reassign Department
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
