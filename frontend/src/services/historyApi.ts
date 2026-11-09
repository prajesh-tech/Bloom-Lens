import { apiClient } from './api';
import { isMock } from './mockMode';
import { QuestionPaper } from '../types/paper';
import { simulateMockLatency } from '../utils/latency';
import { readMockState } from './mockStore';

export interface HistoryListResponse {
  items: QuestionPaper[];
  total: number;
  page: number;
  limit: number;
}

export const historyApi = {
  async getHistory(page = 1, limit = 10, subjectId?: number): Promise<HistoryListResponse> {
    if (isMock()) {
      await simulateMockLatency();
      const papers = readMockState().papers.filter((paper) => subjectId === undefined || paper.subject_id === subjectId);
      return {
        items: papers.slice((page - 1) * limit, page * limit),
        total: papers.length,
        page,
        limit,
      };
    }

    const { data } = await apiClient.get<HistoryListResponse>('/papers', {
      params: { page, limit, ...(subjectId === undefined ? {} : { subject_id: subjectId }) },
    });
    return data;
  },
};
