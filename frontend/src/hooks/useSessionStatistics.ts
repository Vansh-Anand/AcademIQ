import { useState, useEffect, useRef } from 'react';
import type { PipelineRunResponse } from '../types/api';
import { getEvidenceSessions } from '../api/evidence';

export const useSessionStatistics = (result: PipelineRunResponse | null) => {
  const [attacksRun, setAttacksRun] = useState(0);
  const [blocked, setBlocked] = useState(0);
  const [frozen, setFrozen] = useState(0);
  const [allowed, setAllowed] = useState(0);
  const [cumulativeLatency, setCumulativeLatency] = useState(0);
  const [ecesCount, setEcesCount] = useState(0);
  
  const processedSessions = useRef<Set<string>>(new Set());
  const isInitialized = useRef(false);

  const fetchEvidenceCount = async () => {
    try {
      const response = await getEvidenceSessions();
      const newCount = response.sessions?.length || 0;
      
      setEcesCount(prev => {
        // Dispatch event if count increased AND we have already done the initial fetch
        if (isInitialized.current && newCount > prev) {
          const latestSessionId = response.sessions?.[0]?.session_id || 'unknown';
          window.dispatchEvent(new CustomEvent('eces-new-session', { detail: latestSessionId }));
        }
        return newCount;
      });
    } catch (err: any) {
      if (err.response?.status === 404) {
        setEcesCount(0);
      } else {
        setEcesCount(0); // Safely default to 0 for other errors
      }
    }
  };

  // Initial load of ECES count
  useEffect(() => {
    fetchEvidenceCount().then(() => {
      isInitialized.current = true;
    });
  }, []);

  useEffect(() => {
    if (!result) return;
    
    // Prevent double counting if the same session_id is processed again
    if (processedSessions.current.has(result.session_id)) return;
    processedSessions.current.add(result.session_id);

    setAttacksRun(prev => prev + 1);
    
    // Blocked: only if stopping_layer is L1 or L2
    if (result.overall_decision === 'BLOCK' && (result.stopping_layer === 'L1' || result.stopping_layer === 'L2')) {
      setBlocked(prev => prev + 1);
    } else if (result.overall_decision === 'FREEZE') {
      setFrozen(prev => prev + 1);
    } else if (result.overall_decision === 'ALLOW') {
      setAllowed(prev => prev + 1);
    }
    
    // Add latency: Use total_latency_ns if available, otherwise sum layer latencies
    let addedLatency = 0;
    if (result.total_latency_ns) {
      addedLatency = result.total_latency_ns / 1_000_000;
    } else {
      const layers = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'];
      let sumNs = 0;
      for (const l of layers) {
        const out = (result as any)[l];
        if (out && out.latency_ns) sumNs += out.latency_ns;
      }
      addedLatency = sumNs / 1_000_000;
    }
    
    setCumulativeLatency(prev => prev + addedLatency);
    
    // Refresh ECES count after execution completes
    fetchEvidenceCount();
    
  }, [result]);

  return {
    attacksRun,
    blocked,
    frozen,
    allowed,
    cumulativeLatency,
    ecesCount
  };
};
