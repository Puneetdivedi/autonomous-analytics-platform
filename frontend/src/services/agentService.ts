import apiClient from './apiClient';
import { AgentExecution } from '@/types';

export const agentService = {
  async executions(messageId: string): Promise<AgentExecution[]> {
    const { data } = await apiClient.get<AgentExecution[]>(
      '/agents/executions',
      { params: { message_id: messageId } }
    );
    return data;
  },
};
