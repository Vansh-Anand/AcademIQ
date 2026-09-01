import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from './ExecutionModeBadge';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading...', className }) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-gray-500", className)}>
      <Loader2 className="w-8 h-8 animate-spin mb-4" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};
