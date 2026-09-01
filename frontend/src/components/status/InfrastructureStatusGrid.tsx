import React from 'react';
import type { InfrastructureStatus } from '../../types/api';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';
import { CheckCircle2, XCircle } from 'lucide-react';

interface Props {
  infrastructure: InfrastructureStatus[];
}

export const InfrastructureStatusGrid: React.FC<Props> = ({ infrastructure }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {infrastructure.map((infra, idx) => (
        <div key={idx} className="bg-slate-900 border border-slate-700 rounded-lg p-4 flex items-center justify-between">
          <div className="flex-1 min-w-0 pr-4">
            <h4 className="text-sm font-medium text-slate-100 truncate">{infra.name}</h4>
            <p className="text-xs text-slate-400 mt-0.5 truncate">{infra.description}</p>
          </div>
          <div className="flex flex-col items-end shrink-0 space-y-1.5">
            <div className="flex items-center">
              {infra.status === 'OPERATIONAL' ? (
                <span className="flex items-center text-emerald-400 text-xs font-bold font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  {infra.status}
                </span>
              ) : (
                <span className="flex items-center text-red-400 text-xs font-bold font-mono">
                  <XCircle className="w-3.5 h-3.5 mr-1" />
                  {infra.status}
                </span>
              )}
            </div>
            <ExecutionModeBadge mode={infra.execution_mode} />
          </div>
        </div>
      ))}
    </div>
  );
};
