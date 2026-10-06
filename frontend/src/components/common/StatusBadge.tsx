import React from 'react';
import { IssueStatus } from '../../types';

interface StatusBadgeProps {
  status: IssueStatus | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStyle = () => {
    switch (status) {
      case IssueStatus.RESOLVED:
      case 'RESOLVED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case IssueStatus.IN_PROGRESS:
      case 'IN_PROGRESS':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case IssueStatus.ASSIGNED:
      case 'ASSIGNED':
        return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40';
      case IssueStatus.UNDER_REVIEW:
      case 'UNDER_REVIEW':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case IssueStatus.AI_ANALYZED:
      case 'AI_ANALYZED':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case IssueStatus.REPORTED:
      case 'REPORTED':
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${getStyle()}`}>
      {status.replace('_', ' ')}
    </span>
  );
};
