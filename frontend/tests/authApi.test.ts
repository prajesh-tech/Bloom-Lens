import { afterEach, expect, it, vi } from 'vitest';
import { apiClient, setCsrfToken } from '../src/services/api';
import { authApi } from '../src/services/authApi';

afterEach(() => { vi.restoreAllMocks(); setCsrfToken(null); });

it('uses cookie sessions and never sends a browser API key', async () => {
  const post = vi.spyOn(apiClient, 'post').mockResolvedValue({ data: { user_id: 'reviewer:1:alice', role: 'instructor', csrf_token: 'csrf-test' } });
  expect((await authApi.login('alice', 'test-password')).user_id).toBe('reviewer:1:alice');
  expect(post).toHaveBeenCalledWith('/auth/login', { username: 'alice', password: 'test-password' });
  expect(apiClient.defaults.withCredentials).toBe(true);
  expect(apiClient.defaults.headers.common['X-API-Key']).toBeUndefined();
});

it('attaches the session CSRF token to writes through the shared client', async () => {
  setCsrfToken('session-csrf');
  await apiClient.post('/questions/1', {}, { adapter: async (config) => {
    expect(config.headers.get('X-CSRF-Token')).toBe('session-csrf');
    expect(config.headers.get('X-API-Key')).toBeUndefined();
    return { data: {}, status: 200, statusText: 'OK', headers: {}, config };
  } });
});
