import { useState, useEffect, useCallback } from 'react';
import { getSystemStatus } from '../api/status';
import type { SystemStatusResponse } from '../types/api';

export const useSystemStatus = () => {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSystemStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch system status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { status, loading, error, refresh: fetchStatus };
};
