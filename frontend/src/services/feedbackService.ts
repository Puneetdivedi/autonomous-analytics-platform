import apiClient from './apiClient';

export interface FeedbackInput {
  message_id: string;
  rating: number;
  comment?: string;
}

export const feedbackService = {
  async submit(input: FeedbackInput): Promise<void> {
    await apiClient.post('/feedback', input);
  },
};
