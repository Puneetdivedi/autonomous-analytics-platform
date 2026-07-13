import apiClient from './apiClient';
import { TraceSummary } from '@/types';

export const traceService = {
  async byMessage(messageId: string): Promise<TraceSummary> {
    const { data } = await apiClient.get<TraceSummary>('/traces', {
      params: { message_id: messageId },
    });
    return data;
  },

  async get(traceId: string): Promise<TraceSummary> {
    const { data } = await apiClient.get<TraceSummary>(`/traces/${traceId}`);
    return data;
  },
};
