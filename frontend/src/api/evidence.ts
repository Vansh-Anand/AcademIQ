import { apiClient as api } from './client';
import type { 
  SessionListResponse, 
  SessionDetailResponse, 
  VerifyResponse 
} from '../types/api';

export const getEvidenceSessions = async (): Promise<SessionListResponse> => {
  const response = await api.get('/evidence/sessions');
  return response.data;
};

export const getSessionChain = async (sessionId: string): Promise<SessionDetailResponse> => {
  const response = await api.get(`/evidence/session/${sessionId}`);
  return response.data;
};

export const verifySession = async (sessionId: string): Promise<VerifyResponse> => {
  const response = await api.post(`/evidence/session/${sessionId}/verify`);
  return response.data;
};
