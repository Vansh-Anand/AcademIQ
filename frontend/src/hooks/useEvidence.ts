import { useState, useCallback, useEffect } from 'react';
import { getEvidenceSessions, getSessionChain, verifySession } from '../api/evidence';
import type { SessionListItem, SessionDetailResponse, VerifyResponse } from '../types/api';

export const useEvidence = () => {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    setSessionsLoading(true);
    setSessionsError(null);
    try {
      const data = await getEvidenceSessions();
      setSessions(data.sessions);
    } catch (err: any) {
      setSessionsError(err.response?.data?.detail || err.message || 'Failed to fetch sessions');
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const selectSession = useCallback(async (sessionId: string) => {
    setActiveSessionId(sessionId);
    setSessionDetail(null);
    setDetailLoading(true);
    setDetailError(null);
    setVerifyResult(null);
    setVerifyError(null);

    try {
      const data = await getSessionChain(sessionId);
      setSessionDetail(data);
    } catch (err: any) {
      setDetailError(err.response?.data?.detail || err.message || 'Failed to fetch session detail');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const triggerVerify = useCallback(async () => {
    if (!activeSessionId) return;
    
    setVerifyLoading(true);
    setVerifyError(null);
    setVerifyResult(null);

    try {
      const result = await verifySession(activeSessionId);
      setVerifyResult(result);
    } catch (err: any) {
      setVerifyError(err.response?.data?.detail || err.message || 'Failed to verify chain');
    } finally {
      setVerifyLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    sessionsLoading,
    sessionsError,
    activeSessionId,
    sessionDetail,
    detailLoading,
    detailError,
    verifyResult,
    verifyLoading,
    verifyError,
    selectSession,
    triggerVerify,
    refreshSessions: fetchSessions
  };
};
