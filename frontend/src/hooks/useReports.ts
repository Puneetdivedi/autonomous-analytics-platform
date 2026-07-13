import { useQuery } from '@tanstack/react-query';
import { reportService } from '@/services/reportService';

export function useReports(projectId: string | undefined) {
  return useQuery({
    queryKey: ['reports', projectId],
    queryFn: () => reportService.list(projectId as string),
    enabled: Boolean(projectId),
  });
}
