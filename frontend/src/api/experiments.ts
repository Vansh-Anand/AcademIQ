import { apiClient as api } from './client';
import type { 
  ExperimentListResponse, 
  ExperimentNormalized 
} from '../types/api';

export const getExperiments = async (): Promise<ExperimentListResponse> => {
  const response = await api.get<ExperimentListResponse>('/api/experiments');
  return response.data;
};

export const getExperimentDetail = async (experimentId: string): Promise<ExperimentNormalized> => {
  const response = await api.get<ExperimentNormalized>(`/api/experiments/${experimentId}`);
  return response.data;
};
