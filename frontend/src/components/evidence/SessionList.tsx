import React from 'react';
import type { SessionListItem } from '../../types/api';
import { ExecutionModeBadge } from '../common/ExecutionModeBadge';
import { Database, Loader2 } from 'lucide-react';

interface SessionListProps {
  sessions: SessionListItem[];
  isLoading: boolean;
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
}

export const SessionList: React.FC<SessionListProps> = ({ sessions, isLoading, activeSessionId, onSelect }) => {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center text-center">
        <Database className="w-8 h-8 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">No ECES evidence sessions available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sessions.map((session) => (
        <button
          key={session.session_id}
          onClick={() => onSelect(session.session_id)}
          className={`w-full text-left p-4 rounded-lg border transition-all duration-200 ${
            activeSessionId === session.session_id
              ? 'bg-blue-50 border-blue-400 shadow-sm'
              : 'bg-white border-gray-200 hover:border-blue-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex justify-between items-start mb-2">
            <span className="font-mono text-xs font-semibold text-gray-900 truncate mr-2" title={session.session_id}>
              {session.session_id}
            </span>
            <ExecutionModeBadge mode={session.execution_mode} />
          </div>
          <div className="flex justify-between items-end mt-3">
            <span className="text-xs text-gray-500">{session.event_count} records</span>
            <span className="text-xs text-gray-400" title={new Date(session.start_time_ns / 1_000_000).toLocaleString()}>
              {new Date(session.start_time_ns / 1_000_000).toLocaleTimeString()}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
};
