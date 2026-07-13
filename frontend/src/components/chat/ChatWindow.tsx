import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import { Artifacts, DataSource, Message } from '@/types';
import { NodeEvent } from '@/hooks/useChatStream';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import AgentTimeline from './AgentTimeline';
import EmptyState from '@/components/common/EmptyState';

interface ChatWindowProps {
  messages: Message[];
  streaming: boolean;
  streamContent: string;
  streamArtifacts: Artifacts;
  nodeEvents: NodeEvent[];
  error: string | null;
  datasources?: DataSource[];
  selectedDatasourceId?: string;
  onSelectDatasource?: (id: string | undefined) => void;
  onSend: (question: string) => void;
  onUpload?: (file: File) => void;
  onStop?: () => void;
  disabled?: boolean;
}

export default function ChatWindow({
  messages,
  streaming,
  streamContent,
  streamArtifacts,
  nodeEvents,
  error,
  datasources,
  selectedDatasourceId,
  onSelectDatasource,
  onSend,
  onUpload,
  onStop,
  disabled,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamContent, nodeEvents.length]);

  const showStreamBubble = streaming || streamContent || nodeEvents.length > 0;

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && !showStreamBubble ? (
            <div className="flex h-full items-center py-16">
              <EmptyState
                icon={Bot}
                title="Ask anything about your data"
                description="Connect a data source and ask a question. The agent will generate SQL, run analysis, build charts, and summarize insights."
              />
            </div>
          ) : (
            <>
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}

              {showStreamBubble && (
                <div className="py-2">
                  {nodeEvents.length > 0 && (
                    <div className="surface mb-2 ml-11 max-w-md rounded-xl p-3 shadow-card">
                      <p className="mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                        Agent pipeline
                      </p>
                      <AgentTimeline events={nodeEvents} active={streaming} />
                    </div>
                  )}
                  <MessageBubble
                    message={{
                      id: 'streaming',
                      role: 'assistant',
                      content: streamContent,
                      artifacts: streamArtifacts,
                    }}
                    streaming={streaming}
                  />
                </div>
              )}

              {error && (
                <div className="ml-11 mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                  {error}
                </div>
              )}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="mx-auto w-full max-w-3xl px-4 pb-2">
        <ChatInput
          onSend={onSend}
          onUpload={onUpload}
          onStop={onStop}
          streaming={streaming}
          disabled={disabled}
          datasources={datasources}
          selectedDatasourceId={selectedDatasourceId}
          onSelectDatasource={onSelectDatasource}
        />
      </div>
    </div>
  );
}
