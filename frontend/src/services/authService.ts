import apiClient, { clearTokens, setTokens } from './apiClient';
import { LoginPayload, RegisterPayload, TokenPair, User } from '@/types';

export const authService = {
  async login(payload: LoginPayload): Promise<TokenPair> {
    const { data } = await apiClient.post<TokenPair>('/auth/login', payload);
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await apiClient.post<User>('/auth/register', payload);
    return data;
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  logout(): void {
    clearTokens();
  },
};
