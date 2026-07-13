import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { chatService, ChatInput } from '@/services/chatService';

export function useChats(projectId: string | undefined) {
  return useQuery({
    queryKey: ['chats', projectId],
    queryFn: () => chatService.list(projectId as string),
    enabled: Boolean(projectId),
  });
}

export function useChat(id: string | undefined) {
  return useQuery({
    queryKey: ['chat', id],
    queryFn: () => chatService.get(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateChat() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ChatInput) => chatService.create(input),
    onSuccess: (_data, variables) =>
      qc.invalidateQueries({ queryKey: ['chats', variables.project_id] }),
  });
}
