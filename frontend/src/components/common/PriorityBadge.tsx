import React from 'react';
import { SeverityLevel } from '../../types';

interface PriorityBadgeProps {
  score: number;
  severity: SeverityLevel | string;
  showScore?: boolean;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ score, severity, showScore = true }) => {
  const getBadgeStyle = () => {
    switch (severity) {
      case SeverityLevel.CRITICAL:
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case SeverityLevel.HIGH:
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case SeverityLevel.MEDIUM:
      case 'MEDIUM':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
      case SeverityLevel.LOW:
      case 'LOW':
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getBadgeStyle()}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      <span>{severity}</span>
      {showScore && <span className="opacity-80">({score.toFixed(0)}/100)</span>}
    </div>
  );
};
