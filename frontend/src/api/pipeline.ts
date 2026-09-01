import { apiClient } from './client';
import type { PipelineRunResponse } from '../types/api';

export const runPipelineScenario = async (scenarioId: string): Promise<PipelineRunResponse> => {
  const response = await apiClient.post<PipelineRunResponse>('/api/pipeline/run', { scenario_id: scenarioId });
  return response.data;
};
