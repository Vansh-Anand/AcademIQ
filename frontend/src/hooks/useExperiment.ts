import { useState, useEffect, useCallback } from 'react';
import { getExperimentDetail } from '../api/experiments';
import type { ExperimentNormalized } from '../types/api';

export const useExperiment = (experimentId: string | null) => {
  const [experiment, setExperiment] = useState<ExperimentNormalized | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiment = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExperimentDetail(id);
      setExperiment(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Result Unavailable');
      setExperiment(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (experimentId) {
      fetchExperiment(experimentId);
    } else {
      setExperiment(null);
      setError(null);
    }
  }, [experimentId, fetchExperiment]);

  return { experiment, loading, error, refresh: () => experimentId && fetchExperiment(experimentId) };
};
