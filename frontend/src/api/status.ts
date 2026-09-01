import { apiClient as api } from './client';
import type { SystemStatusResponse } from '../types/api';

export const getSystemStatus = async (): Promise<SystemStatusResponse> => {
  const response = await api.get<SystemStatusResponse>('/api/system/status');
  return response.data;
};
