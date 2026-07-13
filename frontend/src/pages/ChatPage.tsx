import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { MessageSquare } from 'lucide-react';
import { useChats, useChat, useCreateChat } from '@/hooks/useChats';
import { useChatStream } from '@/hooks/useChatStream';
import { useSelectedProject } from '@/hooks/useSelectedProject';
import { datasourceService } from '@/services/datasourceService';
import { Message } from '@/types';
import ChatList from '@/components/chat/ChatList';
import ChatWindow from '@/components/chat/ChatWindow';
import EmptyState from '@/components/common/EmptyState';
import Spinner from '@/components/common/Spinner';

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { projectId } = useSelectedProject();

  const { data: chats, isLoading: chatsLoading } = useChats(
    projectId ?? undefined
  );
  const { data: chat, isLoading: chatLoading } = useChat(chatId);
  const createChat = useCreateChat();
  const stream = useChatStream();

  const { data: datasources } = useQuery({
    queryKey: ['datasources', projectId],
    queryFn: () => datasourceService.list(projectId as string),
    enabled: Boolean(projectId),
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedDs, setSelectedDs] = useState<string | undefined>(undefined);
  const pendingQuestion = useRef<string | null>(null);
  const committedRef = useRef(false);

  // Sync fetched chat messages into local state.
  useEffect(() => {
    setMessages(chat?.messages ?? []);
  }, [chat?.id, chat?.messages]);

  // Send a pending question once a chat becomes active (after creation).
  useEffect(() => {
    if (chatId && pendingQuestion.current) {
      const q = pendingQuestion.current;
      pendingQuestion.current = null;
      void doSend(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId]);

  // Commit the streamed assistant message when streaming completes.
  useEffect(() => {
    if (stream.isStreaming) {
      committedRef.current = false;
      return;
    }
    if (committedRef.current) return;
    const hasResult =
      stream.finalMessage || stream.content || stream.error;
    if (!hasResult) return;

    committedRef.current = true;

    const assistant: Message =
      stream.finalMessage ??
      ({
        id: `local-${Date.now()}`,
        chat_id: chatId ?? '',
        role: 'assistant',
        content: stream.content || (stream.error ? '' : ''),
        artifacts: stream.artifacts,
        created_at: new Date().toISOString(),
      } as Message);

    if (stream.content || stream.finalMessage) {
      setMessages((prev) => [...prev, assistant]);
    }
    if (chatId) {
      void qc.invalidateQueries({ queryKey: ['chat', chatId] });
    }
    stream.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.isStreaming, stream.finalMessage, stream.content, stream.error]);

  const doSend = useCallback(
    async (question: string) => {
      if (!chatId) return;
      const userMessage: Message = {
        id: `local-user-${Date.now()}`,
        chat_id: chatId,
        role: 'user',
        content: question,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      committedRef.current = false;
      await stream.send(chatId, {
        question,
        datasource_id: selectedDs,
        stream: true,
      });
    },
    [chatId, selectedDs, stream]
  );

  const handleSend = useCallback(
    async (question: string) => {
      if (chatId) {
        void doSend(question);
        return;
      }
      if (!projectId) return;
      // Create a chat, then send once routed to it.
      pendingQuestion.current = question;
      const created = await createChat.mutateAsync({
        project_id: projectId,
        title: question.slice(0, 60),
      });
      navigate(`/chat/${created.id}`);
    },
    [chatId, projectId, createChat, doSend, navigate]
  );

  const handleNewChat = useCallback(() => {
    stream.reset();
    setMessages([]);
    navigate('/chat');
  }, [navigate, stream]);

  const handleUpload = useCallback(
    async (file: File) => {
      if (!projectId) return;
      await datasourceService.upload(projectId, file);
      void qc.invalidateQueries({ queryKey: ['datasources', projectId] });
    },
    [projectId, qc]
  );

  if (!projectId) {
    return (
      <div className="py-16">
        <EmptyState
          icon={MessageSquare}
          title="Select a project first"
          description="Choose an active project from the top bar to start a conversation."
        />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4">
      <div className="hidden w-64 shrink-0 md:block">
        <div className="surface h-full rounded-xl shadow-card">
          <ChatList
            chats={chats}
            activeChatId={chatId}
            loading={chatsLoading}
            onSelect={(c) => navigate(`/chat/${c.id}`)}
            onNew={handleNewChat}
            disabled={createChat.isPending}
          />
        </div>
      </div>

      <div className="surface flex-1 overflow-hidden rounded-xl shadow-card">
        {chatId && chatLoading ? (
          <Spinner fullscreen label="Loading conversation..." />
        ) : (
          <ChatWindow
            messages={messages}
            streaming={stream.isStreaming}
            streamContent={stream.content}
            streamArtifacts={stream.artifacts}
            nodeEvents={stream.nodeEvents}
            error={stream.error}
            datasources={datasources}
            selectedDatasourceId={selectedDs}
            onSelectDatasource={setSelectedDs}
            onSend={handleSend}
            onUpload={handleUpload}
            onStop={stream.stop}
            disabled={createChat.isPending}
          />
        )}
      </div>
    </div>
  );
}
