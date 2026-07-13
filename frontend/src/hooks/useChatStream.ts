import { useCallback, useRef, useState } from 'react';
import { streamMessage } from '@/services/chatService';
import {
  Artifacts,
  Message,
  SendMessagePayload,
  StreamEvent,
} from '@/types';

export interface NodeEvent {
  node: string;
  status: 'running' | 'done' | 'error';
  timestamp: number;
}

interface StreamState {
  content: string;
  artifacts: Artifacts;
  nodeEvents: NodeEvent[];
  isStreaming: boolean;
  error: string | null;
  finalMessage: Message | null;
}

const initialState: StreamState = {
  content: '',
  artifacts: {},
  nodeEvents: [],
  isStreaming: false,
  error: null,
  finalMessage: null,
};

/**
 * Manages streaming a single question to the backend and accumulating
 * the emitted stream events into a live assistant message.
 */
export function useChatStream() {
  const [state, setState] = useState<StreamState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState(initialState);
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const applyEvent = useCallback((event: StreamEvent) => {
    setState((prev) => {
      switch (event.type) {
        case 'node_start':
          return {
            ...prev,
            nodeEvents: [
              ...prev.nodeEvents,
              {
                node: event.node ?? 'unknown',
                status: 'running',
                timestamp: Date.now(),
              },
            ],
          };
        case 'node_end': {
          const nodeEvents = prev.nodeEvents.map((n) =>
            n.node === (event.node ?? 'unknown') && n.status === 'running'
              ? { ...n, status: 'done' as const }
              : n
          );
          return { ...prev, nodeEvents };
        }
        case 'token': {
          const token =
            typeof event.data === 'string'
              ? event.data
              : ((event.data as { text?: string } | undefined)?.text ?? '');
          return { ...prev, content: prev.content + token };
        }
        case 'artifact': {
          const incoming = (event.data ?? {}) as Artifacts;
          return {
            ...prev,
            artifacts: { ...prev.artifacts, ...incoming },
          };
        }
        case 'error':
          return {
            ...prev,
            error:
              typeof event.data === 'string'
                ? event.data
                : ((event.data as { message?: string } | undefined)?.message ??
                  'An error occurred during analysis.'),
            isStreaming: false,
          };
        case 'done': {
          const finalMessage = (event.data ?? null) as Message | null;
          return { ...prev, isStreaming: false, finalMessage };
        }
        default:
          return prev;
      }
    });
  }, []);

  const send = useCallback(
    async (chatId: string, payload: SendMessagePayload) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState({ ...initialState, isStreaming: true });

      try {
        await streamMessage(chatId, payload, applyEvent, controller.signal);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: (err as Error).message ?? 'Streaming failed.',
        }));
      } finally {
        setState((prev) => ({ ...prev, isStreaming: false }));
      }
    },
    [applyEvent]
  );

  return { ...state, send, stop, reset };
}
