import React from 'react';
import { cn } from './ExecutionModeBadge';

interface StatusBadgeProps {
  status: 'ALLOW' | 'BLOCK' | 'WARN' | 'THROTTLE' | 'FREEZE' | 'UNAVAILABLE' | string | null;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const styles: Record<string, string> = {
    'ALLOW': 'bg-emerald-100 text-emerald-800 border-emerald-200',
    'BLOCK': 'bg-red-100 text-red-800 border-red-200',
    'WARN': 'bg-amber-100 text-amber-800 border-amber-200',
    'THROTTLE': 'bg-amber-100 text-amber-800 border-amber-200',
    'FREEZE': 'bg-red-100 text-red-800 border-red-200',
    'UNAVAILABLE': 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const safeStatus = status || 'UNAVAILABLE';

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase',
        styles[safeStatus] || styles['UNAVAILABLE'],
        className
      )}
    >
      {safeStatus}
    </span>
  );
};
