import { useQuery } from '@tanstack/react-query';
import { traceService } from '@/services/traceService';

export function useTraceByMessage(messageId: string | undefined) {
  return useQuery({
    queryKey: ['trace', 'message', messageId],
    queryFn: () => traceService.byMessage(messageId as string),
    enabled: Boolean(messageId),
  });
}

export function useTrace(traceId: string | undefined) {
  return useQuery({
    queryKey: ['trace', traceId],
    queryFn: () => traceService.get(traceId as string),
    enabled: Boolean(traceId),
  });
}
