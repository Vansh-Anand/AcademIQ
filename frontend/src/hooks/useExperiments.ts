import { useState, useEffect, useCallback } from 'react';
import { getExperiments } from '../api/experiments';
import type { ExperimentSummary } from '../types/api';

export const useExperiments = () => {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExperiments();
      setExperiments(data.experiments);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch experiments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  return { experiments, loading, error, refresh: fetchExperiments };
};
