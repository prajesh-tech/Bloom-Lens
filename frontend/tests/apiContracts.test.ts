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

it('passes subject filters, revision and similarity paths to Axios', async () => {
  vi.stubEnv('VITE_USE_MOCK_API', 'false');
  const get = vi.spyOn(apiClient, 'get').mockResolvedValue({ data: [] });
  await analysisApi.getTopicAnalytics(9);
  expect(get).toHaveBeenLastCalledWith('/analytics/topics', { params: { subject_id: 9 } });
  await analysisApi.getTrendsAnalytics('count', 9);
  expect(get).toHaveBeenLastCalledWith('/analytics/trends', { params: { metric_type: 'count', subject_id: 9 } });
  await historyApi.getHistory(2, 5, 9);
  expect(get).toHaveBeenLastCalledWith('/papers', { params: { page: 2, limit: 5, subject_id: 9 } });
  await analysisApi.getQuestionRevisions(3);
  expect(get).toHaveBeenLastCalledWith('/questions/3/revisions');
  await analysisApi.getSimilarQuestions(3);
  expect(get).toHaveBeenLastCalledWith('/questions/3/similar');
});
