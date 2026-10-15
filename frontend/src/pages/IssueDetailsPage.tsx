import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { issueService, departmentService, citizenService } from '../services/api';
import { Issue, IssueStatus, Department } from '../types';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { MapPin, Cpu, Clock, Building, Shield, CheckCircle2, ArrowLeft, Send, AlertOctagon, Copy, CheckCheck, AlertTriangle, XCircle, AlertCircle, HelpCircle, MessageSquare, Image as ImageIcon } from 'lucide-react';
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
  const [verifiedCategory, setVerifiedCategory] = useState<string>('');
  const [triageAction, setTriageAction] = useState<'CONFIRM' | 'CORRECT' | 'REJECT_SUGGESTION' | 'REQUEST_INFO'>('CONFIRM');
  const [updating, setUpdating] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [responseText, setResponseText] = useState('');
  const [responsePhoto, setResponsePhoto] = useState('');
  const [submittingResponse, setSubmittingResponse] = useState(false);
  const [responseFeedback, setResponseFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchIssue = async (silent: boolean = false) => {
    if (!id) return;
    if (!silent) setLoading(true);
    try {
      const data = await issueService.getIssueById(parseInt(id));
      setIssue(data);
      setNewStatus(data.status);
      if (data.department_id) setSelectedDeptId(data.department_id);
      if (data.verified_category && data.verified_category !== 'REJECTED_AS_FALSE_POSITIVE') {
        setVerifiedCategory(data.verified_category);
      } else {
        setVerifiedCategory(data.issue_type);
      }
    } catch {
      setError('Failed to load issue details.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssue();
    departmentService.listDepartments().then(setDepartments).catch(console.error);
  }, [id]);

  const handleTriageDecision = async () => {
    if (!issue) return;
    setUpdating(true);
    setActionFeedback(null);
    try {
      await issueService.triageIssue(
        issue.id,
        triageAction,
        triageAction === 'CORRECT' ? verifiedCategory : (triageAction === 'CONFIRM' ? (verifiedCategory || issue.issue_type) : undefined),
        notes
      );
      setNotes('');
      await fetchIssue(true);
      const messages: Record<string, string> = {
        CONFIRM: `AI prediction confirmed as '${verifiedCategory || issue.issue_type}'.`,
        CORRECT: `Defect reclassified to '${verifiedCategory}'.`,
        REJECT_SUGGESTION: 'AI suggestion marked as false positive. Citizen complaint preserved for manual review.',
        REQUEST_INFO: 'Additional information requested from citizen.',
      };
      setActionFeedback({ type: 'success', message: messages[triageAction] || 'Triage decision recorded.' });
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to submit triage decision.' });
    } finally {
      setUpdating(false);
    }
  };

  const handleVerifyCategory = async () => {
    if (!issue || !verifiedCategory) return;
    setUpdating(true);
    setActionFeedback(null);
    try {
      await issueService.verifyCategory(issue.id, verifiedCategory, notes);
      setNotes('');
      await fetchIssue(true);
      setActionFeedback({ type: 'success', message: `Defect category verified as '${verifiedCategory}'.` });
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to verify category.' });
    } finally {
      setUpdating(false);
    }
  };

  const handleCitizenResponse = async (clarificationId: number) => {
    if (!issue || !responseText.trim()) return;
    setSubmittingResponse(true);
    setResponseFeedback(null);
    try {
      await citizenService.respondToClarification(issue.id, clarificationId, {
        response_text: responseText.trim(),
        supplementary_image_url: responsePhoto.trim() || undefined,
      });
      setResponseText('');
      setResponsePhoto('');
      setResponseFeedback({
        type: 'success',
        message: 'Your response and additional information have been submitted to municipal reviewers. The report remains in Under Review.'
      });
      await fetchIssue(true);
    } catch (err: any) {
      setResponseFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to submit clarification response.'
      });
    } finally {
      setSubmittingResponse(false);
    }
  };


  const handleUpdateStatus = async () => {
    if (!issue) return;
    setUpdating(true);
    setActionFeedback(null);
    try {
      await issueService.updateStatus(issue.id, newStatus, notes);
      setNotes('');
      await fetchIssue(true);
      setActionFeedback({ type: 'success', message: `Status successfully updated to ${newStatus.replace(/_/g, ' ')}.` });
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to update status.' });
    } finally {
      setUpdating(false);
    }
  };

  const handleAssignDepartment = async () => {
    if (!issue || !selectedDeptId) return;
    setUpdating(true);
    setActionFeedback(null);
    try {
      await issueService.assignDepartment(issue.id, selectedDeptId, notes);
      setNotes('');
      await fetchIssue(true);
      const targetDept = departments.find(d => d.id === selectedDeptId)?.name || 'selected department';
      setActionFeedback({ type: 'success', message: `Successfully reassigned to ${targetDept}.` });
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to reassign department.' });
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
              <StatusBadge status={issue.status} hasPendingClarification={issue.has_pending_clarification} />

              {issue.has_pending_clarification && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <HelpCircle className="w-3 h-3" /> Clarification Requested
                </span>
              )}

              {/* Phase 4 Verification Badge */}
              {issue.is_verified ? (
                issue.verification_status === 'CONFIRMED' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <CheckCheck className="w-3 h-3" /> Human Verified: {issue.verified_category}
                  </span>
                ) : issue.verification_status === 'CORRECTED' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    <CheckCheck className="w-3 h-3" /> Reclassified: {issue.verified_category}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <XCircle className="w-3 h-3" /> Suggestion Rejected
                  </span>
                )
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  <AlertTriangle className="w-3 h-3" /> AI Suggestion (Unverified)
                </span>
              )}
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

            {/* Whole-image classification notice (no spatial localization) */}
            {(issue.issue_type === 'Damaged Road Surface' || issue.issue_type === 'Waterlogging') && (
              <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-800/40 text-xs text-cyan-300 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-cyan-400" />
                <div>
                  <span className="font-semibold">Whole-Image Scene Classification:</span> Prediction represents whole-image context without bounding-box defect localization or measured defect area.
                </div>
              </div>
            )}

            {mainImage && (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden border border-civic-border">
                  <img
                    src={mainImage.annotated_image_path || mainImage.original_image_path}
                    alt={issue.title}
                    className="w-full h-72 object-cover"
                  />
                  <div className="absolute top-3 left-3 bg-civic-bg/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-mono text-cyan-300 border border-cyan-500/20">
                    Confidence: {(issue.ai_confidence * 100).toFixed(1)}% (Suggestion)
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
                    { label: 'Analysis Status', value: issue.ai_analysis_status || (issue.ai_confidence > 0 ? 'SUCCESS' : 'MANUAL'), color: 'text-cyan-400' },
                  ].map(item => (
                    <div key={item.label} className="bg-civic-bg border border-civic-border rounded-xl p-3 text-center">
                      <div className="text-[10px] text-slate-500">{item.label}</div>
                      <div className={`text-sm font-bold font-mono mt-1 ${item.color}`}>{item.value}</div>
                    </div>
                  ))}
                </div>

                {/* Verified Category Status */}
                {issue.is_verified ? (
                  issue.verification_status === 'CONFIRMED' ? (
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Municipal Verified Category:</span>
                        <span className="font-semibold text-emerald-300 font-mono">✓ {issue.verified_category} (Confirmed)</span>
                      </div>
                      {(issue.last_reviewed_by_name || issue.last_reviewed_at) && (
                        <div className="text-[11px] text-slate-400 flex justify-between pt-1 border-t border-emerald-500/10">
                          <span>Verified By: <span className="text-slate-300 font-medium">{issue.last_reviewed_by_name || 'Municipal Reviewer'}</span></span>
                          {issue.last_reviewed_at && (
                            <span>
                              {(() => {
                                const d = new Date(issue.last_reviewed_at);
                                return isNaN(d.getTime()) ? issue.last_reviewed_at : d.toLocaleString();
                              })()}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Municipal Reclassified Category:</span>
                        <span className="font-semibold text-purple-300 font-mono">✎ {issue.verified_category}</span>
                      </div>
                      {(issue.last_reviewed_by_name || issue.last_reviewed_at) && (
                        <div className="text-[11px] text-slate-400 flex justify-between pt-1 border-t border-purple-500/10">
                          <span>Reclassified By: <span className="text-slate-300 font-medium">{issue.last_reviewed_by_name || 'Municipal Reviewer'}</span></span>
                          {issue.last_reviewed_at && (
                            <span>
                              {(() => {
                                const d = new Date(issue.last_reviewed_at);
                                return isNaN(d.getTime()) ? issue.last_reviewed_at : d.toLocaleString();
                              })()}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                ) : issue.verified_category === 'REJECTED_AS_FALSE_POSITIVE' ? (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">AI Suggestion Status:</span>
                      <span className="font-semibold text-rose-300 font-mono">✕ Rejected as False Positive</span>
                    </div>
                    {(issue.last_reviewed_by_name || issue.last_reviewed_at) && (
                      <div className="text-[11px] text-slate-400 flex justify-between pt-1 border-t border-rose-500/10">
                        <span>Reviewed By: <span className="text-slate-300 font-medium">{issue.last_reviewed_by_name || 'Municipal Reviewer'}</span></span>
                        {issue.last_reviewed_at && (
                          <span>
                            {(() => {
                              const d = new Date(issue.last_reviewed_at);
                              return isNaN(d.getTime()) ? issue.last_reviewed_at : d.toLocaleString();
                            })()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Verification Status:</span>
                    <span className="font-semibold text-amber-300 font-mono">⚡ Pending Human Verification</span>
                  </div>
                )}
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

          {/* Phase 5 Citizen Clarification & Information Workflow */}
          {((issue.clarifications && issue.clarifications.length > 0) || issue.has_pending_clarification) && (
            <div className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-amber-400" /> Citizen Clarification & Review Requests
                </h3>
                {issue.has_pending_clarification ? (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Action Required
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Thread Complete
                  </span>
                )}
              </div>

              {/* Response Feedback Alert */}
              {responseFeedback && (
                <div className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                  responseFeedback.type === 'success'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                  {responseFeedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertOctagon className="w-4 h-4 shrink-0" />}
                  <span>{responseFeedback.message}</span>
                </div>
              )}

              {/* Active Pending Request */}
              {issue.has_pending_clarification && (
                (() => {
                  const pendingReq = (issue.clarifications || []).find(c => c.status === 'PENDING');
                  if (!pendingReq) return null;
                  const isOwner = user?.id === issue.reporter_id;

                  return (
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                            PENDING REQUEST #{pendingReq.id}
                          </span>
                          <span className="text-xs text-slate-300 font-medium">
                            From: {pendingReq.requested_by_name || 'Municipal Reviewer'}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-400">
                          {new Date(pendingReq.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="bg-civic-bg/90 rounded-lg p-3 border border-amber-500/20 text-xs text-amber-100 font-medium leading-relaxed">
                        "{pendingReq.request_text}"
                      </div>

                      {isOwner ? (
                        <div className="space-y-3 pt-2">
                          <label className="text-[10px] font-mono text-slate-400 uppercase block">
                            Your Clarification / Supplementary Information (Report Owner)
                          </label>
                          <textarea
                            rows={3}
                            value={responseText}
                            onChange={(e) => setResponseText(e.target.value)}
                            placeholder="Provide additional location markers, details on the defect, or answers to the reviewer's inquiry..."
                            className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all resize-none"
                          />

                          <div>
                            <label className="text-[10px] font-mono text-slate-400 uppercase mb-1 block">
                              Supplementary Photo URL / File Path (Optional)
                            </label>
                            <input
                              type="text"
                              value={responsePhoto}
                              onChange={(e) => setResponsePhoto(e.target.value)}
                              placeholder="e.g. /uploads/evidence_detail.jpg or image URL"
                              className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all"
                            />
                          </div>

                          <div className="flex items-center justify-between pt-1">
                            <span className="text-[10px] text-slate-500">
                              ℹ Remains in Under Review; does not verify or resolve report.
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCitizenResponse(pendingReq.id)}
                              disabled={submittingResponse || !responseText.trim()}
                              className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5"
                            >
                              {submittingResponse ? (
                                <>
                                  <div className="w-3 h-3 border border-slate-950 border-t-transparent rounded-full animate-spin" />
                                  <span>Submitting...</span>
                                </>
                              ) : (
                                <>
                                  <Send className="w-3.5 h-3.5" />
                                  <span>Submit Response</span>
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400 italic">
                          Awaiting citizen response from the report owner.
                        </div>
                      )}
                    </div>
                  );
                })()
              )}

              {/* Ordered Clarification History */}
              <div className="space-y-3 pt-2">
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  Clarification History ({issue.clarifications?.length || 0})
                </div>
                {issue.clarifications && issue.clarifications.length > 0 ? (
                  issue.clarifications.map((item) => (
                    <div key={item.id} className="p-3.5 bg-civic-bg border border-civic-border rounded-xl space-y-2.5">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            item.status === 'RESPONDED'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}>
                            {item.status}
                          </span>
                          <span className="text-slate-300 font-medium text-xs">
                            Inquiry from {item.requested_by_name || 'Municipal Reviewer'}
                          </span>
                        </div>
                        <span className="text-slate-500 font-mono text-[10px]">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="text-xs text-slate-300 bg-civic-card/60 p-2.5 rounded-lg border border-civic-border/50">
                        "{item.request_text}"
                      </div>

                      {item.status === 'RESPONDED' ? (
                        <div className="pl-3 border-l-2 border-emerald-500/40 mt-2 space-y-1">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-emerald-400 font-medium">Citizen Response</span>
                            {item.responded_at && (
                              <span className="text-slate-500 font-mono text-[10px]">
                                {new Date(item.responded_at).toLocaleString()}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-200">{item.response_text}</p>
                          {item.response_image_path && (
                            <div className="pt-1 flex items-center gap-1.5 text-xs text-cyan-400 font-mono">
                              <ImageIcon className="w-3.5 h-3.5 shrink-0" />
                              <a href={item.response_image_path} target="_blank" rel="noreferrer" className="hover:underline truncate">
                                Attached Photo: {item.response_image_path}
                              </a>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-[11px] text-amber-400/80 italic">
                          Awaiting citizen response
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500">No clarification requests recorded.</p>
                )}
              </div>
            </div>
          )}

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

              {actionFeedback && (
                <div className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
                  actionFeedback.type === 'success' 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                  {actionFeedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertOctagon className="w-4 h-4 shrink-0" />}
                  <span>{actionFeedback.message}</span>
                </div>
              )}

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

              {/* Phase 4 Human Triage & Safe Verification */}
              <div className="pt-4 border-t border-civic-border space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider font-semibold">
                    Human Triage & Verification
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">
                    {issue.verification_status || 'UNVERIFIED'}
                  </span>
                </div>

                {/* Triage Action Selector */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setTriageAction('CONFIRM')}
                    className={`px-2 py-1.5 rounded-lg text-xs font-medium border text-left transition-colors ${
                      triageAction === 'CONFIRM'
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : 'bg-civic-bg border-civic-border text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    ✓ Confirm AI
                  </button>
                  <button
                    type="button"
                    onClick={() => setTriageAction('CORRECT')}
                    className={`px-2 py-1.5 rounded-lg text-xs font-medium border text-left transition-colors ${
                      triageAction === 'CORRECT'
                        ? 'bg-purple-500/20 border-purple-500/40 text-purple-300'
                        : 'bg-civic-bg border-civic-border text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    ✎ Reclassify
                  </button>
                  <button
                    type="button"
                    onClick={() => setTriageAction('REJECT_SUGGESTION')}
                    className={`px-2 py-1.5 rounded-lg text-xs font-medium border text-left transition-colors ${
                      triageAction === 'REJECT_SUGGESTION'
                        ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                        : 'bg-civic-bg border-civic-border text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    ✕ Reject AI
                  </button>
                  <button
                    type="button"
                    onClick={() => setTriageAction('REQUEST_INFO')}
                    className={`px-2 py-1.5 rounded-lg text-xs font-medium border text-left transition-colors ${
                      triageAction === 'REQUEST_INFO'
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                        : 'bg-civic-bg border-civic-border text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    ? Request Info
                  </button>
                </div>

                {/* Dynamic Category Selector for CORRECT */}
                {triageAction === 'CORRECT' && (
                  <div>
                    <label className="text-[10px] font-mono text-slate-400 uppercase mb-1 block">
                      Select Correct Category
                    </label>
                    <select
                      value={verifiedCategory}
                      onChange={(e) => setVerifiedCategory(e.target.value)}
                      className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-all"
                    >
                      <optgroup label="Road Infrastructure Defects (5)">
                        <option value="Pothole">Potholes [Object Detection Supported]</option>
                        <option value="Longitudinal Crack">Longitudinal Cracks [Object Detection Supported]</option>
                        <option value="Transverse Crack">Transverse Cracks [Object Detection Supported]</option>
                        <option value="Alligator Crack">Alligator Cracks [Object Detection Supported]</option>
                        <option value="Damaged Road Surface">Damaged Road Surfaces [Classification Intended — Model Unavailable]</option>
                      </optgroup>
                      <optgroup label="Sanitation & Waste Defects (3)">
                        <option value="Garbage Accumulation">Garbage Accumulation [Manual Reporting Only — Pending Training]</option>
                        <option value="Illegal Dumping">Illegal Dumping [Manual Reporting Only — Pending Training]</option>
                        <option value="Overflowing Garbage Bins">Overflowing Garbage Bins [Manual Reporting Only — Pending Training]</option>
                      </optgroup>
                      <optgroup label="Drainage & Flood Defects (4)">
                        <option value="Blocked Drains">Blocked Drains [Manual Reporting Only — Insufficient Field Data]</option>
                        <option value="Overflowing Drains">Overflowing Drains [Manual Reporting Only — Insufficient Field Data]</option>
                        <option value="Waterlogging">Waterlogging [Classification Intended — Model Unavailable]</option>
                        <option value="Damaged Drainage Covers">Damaged Drainage Covers [Manual Reporting Only — Insufficient Field Data]</option>
                      </optgroup>
                    </select>
                  </div>
                )}

                {/* Explanatory notes */}
                {triageAction === 'CONFIRM' && (
                  <p className="text-[11px] text-emerald-400/90 leading-tight">
                    Confirming AI suggestion: '{verifiedCategory || issue.issue_type}'. Defect will be marked verified.
                  </p>
                )}
                {triageAction === 'REJECT_SUGGESTION' && (
                  <p className="text-[11px] text-rose-400/90 leading-tight">
                    Flags AI suggestion as false positive. Citizen report and photos are preserved in UNDER REVIEW for manual handling.
                  </p>
                )}
                {triageAction === 'REQUEST_INFO' && (
                  <p className="text-[11px] text-amber-400/90 leading-tight">
                    Requests citizen clarification or clearer photo while keeping ticket active.
                  </p>
                )}

                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">
                    Reviewer Notes {triageAction === 'REJECT_SUGGESTION' || triageAction === 'REQUEST_INFO' ? '(Required)' : '(Optional)'}
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder={
                      triageAction === 'REJECT_SUGGESTION'
                        ? 'Reason for rejecting AI prediction (e.g. shadow artifact, normal texture)...'
                        : triageAction === 'REQUEST_INFO'
                        ? 'Specify information needed from citizen...'
                        : 'Review rationale or field inspection notes...'
                    }
                    className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 transition-all resize-none"
                  />
                </div>

                <button
                  type="button"
                  onClick={handleTriageDecision}
                  disabled={updating || ((triageAction === 'REJECT_SUGGESTION' || triageAction === 'REQUEST_INFO') && notes.trim().length < 3)}
                  className={`w-full py-2 rounded-lg text-white text-xs font-medium transition-colors disabled:opacity-50 ${
                    triageAction === 'CONFIRM'
                      ? 'bg-emerald-600 hover:bg-emerald-500'
                      : triageAction === 'CORRECT'
                      ? 'bg-purple-600 hover:bg-purple-500'
                      : triageAction === 'REJECT_SUGGESTION'
                      ? 'bg-rose-600 hover:bg-rose-500'
                      : 'bg-amber-600 hover:bg-amber-500'
                  }`}
                >
                  {updating ? 'Recording Decision...' : `Submit Triage: ${triageAction.replace('_', ' ')}`}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
