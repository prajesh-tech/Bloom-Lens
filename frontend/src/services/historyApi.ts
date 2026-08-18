import { apiClient } from './api';
import { QuestionPaper } from '../types/paper';
import { simulateMockLatency } from '../utils/latency';
import { MOCK_PAPERS } from './mockData';

const isMock = () => import.meta.env.VITE_USE_MOCK_API !== 'false';

export interface HistoryListResponse {
  items: QuestionPaper[];
  total: number;
  page: number;
  limit: number;
}

export const historyApi = {
  async getHistory(page = 1, limit = 10): Promise<HistoryListResponse> {
    if (isMock()) {
      await simulateMockLatency();
      return {
        items: MOCK_PAPERS,
        total: MOCK_PAPERS.length,
        page,
        limit,
      };
    }

    const { data } = await apiClient.get<HistoryListResponse>('/papers', {
      params: { page, limit },
    });
    return data;
  },
};
