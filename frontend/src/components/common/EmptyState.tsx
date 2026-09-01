import React from 'react';
import { ServerOff } from 'lucide-react';
import { cn } from './ExecutionModeBadge';

interface EmptyStateProps {
  title?: string;
  message: string;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title = 'Unavailable', 
  message, 
  icon = <ServerOff className="w-10 h-10 text-gray-400" />,
  className 
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-12 border border-gray-200 border-dashed rounded-lg bg-gray-50 text-center", className)}>
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-500 max-w-sm mx-auto">{message}</p>
    </div>
  );
};
