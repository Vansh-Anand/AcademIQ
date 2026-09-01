import React from 'react';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';
import { StatusBadge } from '../common/StatusBadge';
import type { LayerState } from '../../types/pipeline';
import { ExecutionMode } from '../../types/api';
import { Loader2, ShieldCheck, ShieldAlert, AlertTriangle, HelpCircle, Lock } from 'lucide-react';

interface PipelineLayerCardProps {
  id: string;
  name: string;
  state: LayerState;
  executionMode?: ExecutionMode;
  details?: React.ReactNode;
}

export const PipelineLayerCard: React.FC<PipelineLayerCardProps> = ({
  id,
  name,
  state,
  executionMode,
  details
}) => {
  const isPending = state === 'PENDING';
  const isProcessing = state === 'PROCESSING';
  const isBlocked = state === 'BLOCK' || state === 'FREEZE';
  const isWarn = state === 'WARN' || state === 'THROTTLE';
  const isAllow = state === 'ALLOW';
  const isUnavailable = state === 'UNAVAILABLE';

  let borderColor = 'border-gray-200';
  let bgColor = 'bg-white';
  if (isProcessing) {
    borderColor = 'border-blue-400';
    bgColor = 'bg-blue-50';
  } else if (isBlocked) {
    borderColor = 'border-red-400';
    bgColor = 'bg-red-50';
  } else if (isWarn) {
    borderColor = 'border-amber-400';
    bgColor = 'bg-amber-50';
  } else if (isUnavailable) {
    borderColor = 'border-dashed border-gray-300';
    bgColor = 'bg-gray-50';
  } else if (isAllow) {
    borderColor = 'border-emerald-300';
  }

  const renderIcon = () => {
    if (isPending) return <div className="w-5 h-5 rounded-full border-2 border-gray-200" />;
    if (isProcessing) return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    if (isBlocked) return <ShieldAlert className="w-5 h-5 text-red-500" />;
    if (isWarn) return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    if (isAllow) return <ShieldCheck className="w-5 h-5 text-emerald-500" />;
    if (isUnavailable) return <HelpCircle className="w-5 h-5 text-gray-400" />;
    return <Lock className="w-5 h-5 text-gray-400" />;
  };

  return (
    <div className={`relative p-4 rounded-lg border transition-all duration-300 ${borderColor} ${bgColor} ${isPending ? 'opacity-50' : 'opacity-100'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-3">
          {renderIcon()}
          <div>
            <h4 className="text-sm font-bold text-gray-900">{id} — {name}</h4>
          </div>
        </div>
        {executionMode && !isPending && !isProcessing && (
          <ExecutionModeBadge mode={executionMode} />
        )}
      </div>
      
      {!isPending && (
        <div className="mt-3 pl-8">
          <div className="flex items-center mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider mr-2">Result:</span>
            {isProcessing ? (
              <span className="text-xs text-blue-600 animate-pulse font-medium uppercase">Processing...</span>
            ) : (
              <StatusBadge status={state} />
            )}
          </div>
          {details && !isProcessing && (
            <div className="mt-2 text-sm text-gray-600 bg-white bg-opacity-50 p-2 rounded border border-gray-100">
              {details}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
