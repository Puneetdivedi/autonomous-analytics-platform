import apiClient, { API_BASE_URL, getAccessToken } from './apiClient';
import { Chat, Message, SendMessagePayload, StreamEvent } from '@/types';

export interface ChatInput {
  project_id: string;
  title: string;
}

export const chatService = {
  async list(projectId: string): Promise<Chat[]> {
    const { data } = await apiClient.get<Chat[]>('/chats', {
      params: { project_id: projectId },
    });
    return data;
  },

  async get(id: string): Promise<Chat> {
    const { data } = await apiClient.get<Chat>(`/chats/${id}`);
    return data;
  },

  async create(input: ChatInput): Promise<Chat> {
    const { data } = await apiClient.post<Chat>('/chats', input);
    return data;
  },

  async sendMessage(
    chatId: string,
    body: SendMessagePayload
  ): Promise<Message> {
    const { data } = await apiClient.post<Message>(
      `/chats/${chatId}/messages`,
      { ...body, stream: false }
    );
    return data;
  },
};

/**
 * Stream an assistant response from the backend via SSE-over-fetch.
 * Parses `data:` lines, each carrying a JSON StreamEvent, and forwards
 * every event to `onEvent`. Resolves when the stream ends.
 */
export async function streamMessage(
  chatId: string,
  body: SendMessagePayload,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(
    `${API_BASE_URL}/chats/${chatId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ ...body, stream: true }),
      signal,
    }
  );

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '');
    throw new Error(
      `Stream request failed (${response.status}): ${text || response.statusText}`
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const dispatch = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed || trimmed === '[DONE]') return;
    try {
      const event = JSON.parse(trimmed) as StreamEvent;
      onEvent(event);
    } catch {
      // Ignore malformed chunks (e.g. keep-alive comments).
    }
  };

  // SSE frames are separated by a blank line. Each frame may contain
  // one or more `data:` fields.
  const processFrame = (frame: string) => {
    const dataLines = frame
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart());
    if (dataLines.length > 0) {
      dispatch(dataLines.join('\n'));
    }
  };

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex: number;
    // Frames separated by double newline.
    while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);
      processFrame(frame);
    }
  }

  // Flush any trailing frame.
  if (buffer.trim()) {
    processFrame(buffer);
  }
}
