import { ApiError, apiClient, setCsrfToken } from './api';
import { isMock } from './mockMode';

export interface BrowserSession {
  user_id: string;
  role: string;
  csrf_token?: string | null;
}

export const authApi = {
  async getSession(): Promise<BrowserSession | null> {
    if (isMock()) return { user_id: 'demo', role: 'instructor' };
    try {
      const { data } = await apiClient.get<BrowserSession>('/auth/me');
      setCsrfToken(data.csrf_token ?? null);
      return data;
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) return null;
      throw error;
    }
  },
  async login(username: string, password: string): Promise<BrowserSession> {
    const { data } = await apiClient.post<BrowserSession>('/auth/login', { username, password });
    setCsrfToken(data.csrf_token ?? null);
    return data;
  },
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
    setCsrfToken(null);
  },
};
