import { useQuery } from '@tanstack/react-query';
import { agentService } from '@/services/agentService';

export function useAgentExecutions(messageId: string | undefined) {
  return useQuery({
    queryKey: ['agent-executions', messageId],
    queryFn: () => agentService.executions(messageId as string),
    enabled: Boolean(messageId),
  });
}
