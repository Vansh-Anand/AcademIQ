import React from 'react';
import { AlertCircle } from 'lucide-react';
import { cn } from './ExecutionModeBadge';

interface ErrorStateProps {
  title?: string;
  message: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ title = 'Error', message, className }) => {
  return (
    <div className={cn("p-4 border border-red-200 bg-red-50 rounded-lg text-red-900", className)}>
      <div className="flex items-start">
        <AlertCircle className="w-5 h-5 mr-2 text-red-600 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-red-800">{title}</h3>
          <p className="text-sm mt-1 text-red-700">{message}</p>
        </div>
      </div>
    </div>
  );
};
