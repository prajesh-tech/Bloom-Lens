import { afterEach, describe, expect, it, vi } from 'vitest';
import { analysisApi } from '../src/services/analysisApi';
import { historyApi } from '../src/services/historyApi';
import { apiClient } from '../src/services/api';

afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

describe('real API defaults', () => {
  it('uses the real history API when mock mode is unset', async () => {
    vi.stubEnv('VITE_USE_MOCK_API', '');
    Reflect.deleteProperty(import.meta.env, 'VITE_USE_MOCK_API');
    const response = { items: [], total: 0, page: 1, limit: 10 };
    const get = vi.spyOn(apiClient, 'get').mockResolvedValue({ data: response });
    expect(await historyApi.getHistory()).toEqual(response);
    expect(get).toHaveBeenCalledWith('/papers', { params: { page: 1, limit: 10 } });
  });

  it('fetches examination types from the canonical backend endpoint', async () => {
    vi.stubEnv('VITE_USE_MOCK_API', 'false');
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: ['Internal', 'Mid-Term'] });
    expect(await analysisApi.getExamTypes()).toEqual(['Internal', 'Mid-Term']);
  });
});
