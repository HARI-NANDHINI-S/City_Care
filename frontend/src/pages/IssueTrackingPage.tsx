import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { citizenService } from '../services/api';
import { Issue, IssueStatus } from '../types';
import { ArrowLeft, CheckCircle2, Circle, Clock, MapPin } from 'lucide-react';
import { motion } from 'framer-motion';
import { StatusBadge } from '../components/common/StatusBadge';

const flow = [
  IssueStatus.REPORTED, IssueStatus.AI_ANALYZED, IssueStatus.UNDER_REVIEW,
  IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED, IssueStatus.CLOSED
];

const stepDescriptions: Partial<Record<IssueStatus, string>> = {
  [IssueStatus.REPORTED]: 'Your issue has been submitted to CivicVision AI.',
  [IssueStatus.AI_ANALYZED]: 'Our computer vision pipeline has analyzed your image.',
  [IssueStatus.UNDER_REVIEW]: 'Municipal administrators are reviewing the report.',
  [IssueStatus.ASSIGNED]: 'The issue has been assigned to a municipal department.',
  [IssueStatus.IN_PROGRESS]: 'A repair crew has been dispatched to address the issue.',
  [IssueStatus.RESOLVED]: 'The issue has been resolved by the department.',
  [IssueStatus.CLOSED]: 'The maintenance ticket has been formally closed.',
};

export const IssueTrackingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [issue, setIssue] = useState<Issue | undefined>();
  const [timeline, setTimeline] = useState<any[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!id) return;
    Promise.all([citizenService.details(+id), citizenService.timeline(+id)])
      .then(([i, t]) => { setIssue(i); setTimeline(t); })
      .catch(() => setErr('Unable to load this issue timeline.'));
  }, [id]);

  if (err) return (
    <div className="p-8 flex items-center justify-center min-h-[40vh]">
      <div className="text-center space-y-2">
        <p className="text-red-400">{err}</p>
        <Link to={`/issue/${id}`} className="text-cyan-400 text-sm hover:underline">← Back to details</Link>
      </div>
    </div>
  );

  if (!issue) return (
    <div className="p-8 space-y-4">
      <div className="h-6 w-48 bg-slate-800 rounded animate-pulse" />
      <div className="space-y-4">
        {[...Array(7)].map((_, i) => <div key={i} className="h-20 bg-civic-card border border-civic-border rounded-xl animate-pulse" />)}
      </div>
    </div>
  );

  const done = new Set(timeline.map(t => t.new_status));
  const current = issue.status;
  const currentStepIdx = flow.indexOf(current);

  return (
    <div className="p-6 lg:p-8 max-w-2xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Link to={`/issue/${id}`} className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:underline mb-6">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Issue Details
        </Link>

        <div className="flex items-start justify-between gap-4 mb-8">
          <div>
            <div className="text-[11px] font-mono text-slate-500 mb-1">Issue #{issue.id}</div>
            <h1 className="text-xl font-bold text-white">{issue.title}</h1>
            {issue.address && (
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                <MapPin className="w-3 h-3" /> {issue.address}
              </div>
            )}
          </div>
          <StatusBadge status={issue.status} />
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-xs text-slate-500 mb-2">
            <span>Overall Progress</span>
            <span className="font-mono">{issue.progress_percentage || 0}%</span>
          </div>
          <div className="h-2 bg-civic-card border border-civic-border rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${issue.progress_percentage || 0}%` }}
              transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full"
            />
          </div>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-[14px] top-0 bottom-0 w-0.5 bg-civic-border" />

          <div className="space-y-1">
            {flow.map((step, idx) => {
              const ev = [...timeline].reverse().find(t => t.new_status === step);
              const isCompleted = done.has(step) || idx < currentStepIdx;
              const isCurrent = step === current;
              const isPending = !isCompleted && !isCurrent;

              return (
                <motion.div key={step}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.07 }}
                  className="relative flex gap-4 pb-6"
                >
                  {/* Icon */}
                  <div className="relative z-10 shrink-0">
                    {isCompleted ? (
                      <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center">
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      </div>
                    ) : isCurrent ? (
                      <div className="w-7 h-7 rounded-full bg-cyan-500 flex items-center justify-center ring-4 ring-cyan-500/20">
                        <Clock className="w-3.5 h-3.5 text-white" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-civic-card border border-civic-border flex items-center justify-center">
                        <Circle className="w-3.5 h-3.5 text-slate-600" />
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className={`flex-1 pt-0.5 pb-2 rounded-xl px-4 py-3 ${isCurrent ? 'bg-cyan-500/5 border border-cyan-500/15' : isCompleted ? 'bg-emerald-500/5 border border-emerald-500/10' : 'bg-civic-card/40 border border-transparent'}`}>
                    <div className={`text-sm font-semibold ${isCurrent ? 'text-cyan-300' : isCompleted ? 'text-emerald-300' : 'text-slate-500'}`}>
                      {step.replace(/_/g, ' ')}
                    </div>

                    {ev ? (
                      <>
                        <div className="text-xs text-slate-500 mt-0.5 font-mono">{new Date(ev.created_at).toLocaleString()}</div>
                        <div className="text-xs text-slate-400 mt-1">{ev.notes || stepDescriptions[step]}</div>
                        {ev.progress_percentage != null && (
                          <div className="text-xs text-cyan-400 font-mono mt-1">Progress: {ev.progress_percentage}%</div>
                        )}
                      </>
                    ) : isCurrent ? (
                      <>
                        <div className="text-xs text-slate-500 mt-0.5">Currently at this stage</div>
                        <div className="text-xs text-slate-400 mt-1">{issue.latest_update || stepDescriptions[step]}</div>
                      </>
                    ) : isPending ? (
                      <div className="text-xs text-slate-600 mt-0.5">{stepDescriptions[step]}</div>
                    ) : null}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>
    </div>
  );
};
