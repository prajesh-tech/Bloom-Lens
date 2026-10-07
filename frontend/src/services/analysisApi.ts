import { apiClient } from './api';
import { PaperUploadPayload, QuestionPaper, PerformanceEstimate } from '../types/paper';
import { QuestionAnalysis, QuestionPatchPayload } from '../types/question';
import { BloomAnalyticsData, TrendsAnalyticsData, OverviewAnalytics } from '../types/analytics';
import { simulateMockLatency } from '../utils/latency';
import {
  MOCK_PAPERS,
  MOCK_QUESTIONS_MAP,
  MOCK_BLOOM_ANALYTICS,
  MOCK_TRENDS_ANALYTICS,
  MOCK_OVERVIEW_ANALYTICS,
  MOCK_PERFORMANCE_ESTIMATES,
} from './mockData';

const isMock = () => import.meta.env.VITE_USE_MOCK_API === 'true';

export const analysisApi = {
  async uploadQuestionPaper(payload: PaperUploadPayload): Promise<QuestionPaper> {
    if (isMock()) {
      await simulateMockLatency();
      const newId = 100 + MOCK_PAPERS.length + 1;
      const newPaper: QuestionPaper = {
        id: newId,
        subject_code: payload.subject_code,
        subject_name: payload.subject_name,
        examination_type: payload.examination_type,
        maximum_marks: payload.maximum_marks,
        original_filename: payload.file.name,
        upload_timestamp: new Date().toISOString(),
        year_date: payload.year_date || '2024',
        processing_status: 'COMPLETED',
        extraction_status: 'SUCCESS',
        validation_status: 'VALID',
        optional_question_flag: false,
        total_questions: MOCK_QUESTIONS_MAP[101].length,
      };
      MOCK_PAPERS.unshift(newPaper);
      MOCK_QUESTIONS_MAP[newId] = MOCK_QUESTIONS_MAP[101].map((q, idx) => ({
        ...q,
        id: newId * 10 + idx,
        question_paper_id: newId,
      }));
      return newPaper;
    }

    const formData = new FormData();
    formData.append('subject_code', payload.subject_code);
    formData.append('subject_name', payload.subject_name);
    formData.append('examination_type', payload.examination_type);
    formData.append('maximum_marks', String(payload.maximum_marks));
    if (payload.year_date) formData.append('year_date', payload.year_date);
    formData.append('file', payload.file);

    const { data } = await apiClient.post<QuestionPaper>('/papers/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async getQuestionPaper(paperId: number): Promise<QuestionPaper> {
    if (isMock()) {
      await simulateMockLatency();
      const paper = MOCK_PAPERS.find((p) => p.id === paperId) || MOCK_PAPERS[0];
      return paper;
    }

    const { data } = await apiClient.get<QuestionPaper>(`/papers/${paperId}`);
    return data;
  },

  async deleteQuestionPaper(paperId: number): Promise<void> {
    if (isMock()) {
      await simulateMockLatency();
      const idx = MOCK_PAPERS.findIndex((p) => p.id === paperId);
      if (idx !== -1) MOCK_PAPERS.splice(idx, 1);
      delete MOCK_QUESTIONS_MAP[paperId];
      return;
    }

    await apiClient.delete(`/papers/${paperId}`);
  },

  async getPaperQuestions(paperId: number): Promise<QuestionAnalysis[]> {
    if (isMock()) {
      await simulateMockLatency();
      return MOCK_QUESTIONS_MAP[paperId] || MOCK_QUESTIONS_MAP[101];
    }

    let page = 1;
    const limit = 100;
    const allQuestions: QuestionAnalysis[] = [];
    let hasMore = true;

    while (hasMore) {
      const { data } = await apiClient.get<{ items: QuestionAnalysis[]; total: number; page: number; limit: number }>(
        `/questions`,
        {
          params: { paper: paperId, page, limit },
        }
      );
      const items = data.items || [];
      allQuestions.push(...items);

      if (items.length === 0 || allQuestions.length >= data.total || items.length < limit) {
        hasMore = false;
      } else {
        page++;
      }
    }

    return allQuestions;
  },

  async patchQuestion(questionId: number, payload: QuestionPatchPayload): Promise<QuestionAnalysis> {
    if (isMock()) {
      await simulateMockLatency();
      // Search across mock questions
      for (const qList of Object.values(MOCK_QUESTIONS_MAP)) {
        const q = qList.find((item) => item.id === questionId);
        if (q) {
          if (payload.question_text !== undefined) q.original_text = payload.question_text;
          if (payload.marks !== undefined) q.marks = payload.marks;
          if (payload.unit !== undefined) q.unit = payload.unit;
          if (payload.topic_name !== undefined) q.topic = payload.topic_name;
          if (payload.question_type !== undefined) {
            q.human_question_type = payload.question_type;
            q.question_type = payload.question_type;
          }
          if (payload.bloom_level !== undefined) {
            q.human_bloom_level = payload.bloom_level;
            q.effective_bloom_level = payload.bloom_level;
          }
          q.review_status = 'CORRECTED';
          return { ...q };
        }
      }
      throw new Error('Question not found in mock store');
    }

    const { data } = await apiClient.patch<QuestionAnalysis>(`/questions/${questionId}`, payload);
    return data;
  },

  async getBloomAnalytics(subjectId?: number): Promise<BloomAnalyticsData> {
    if (isMock()) {
      await simulateMockLatency();
      return MOCK_BLOOM_ANALYTICS;
    }

    const { data } = await apiClient.get<BloomAnalyticsData>('/analytics/bloom', {
      params: { subject_id: subjectId },
    });
    return data;
  },

  async getTrendsAnalytics(metricType = 'marks_weighted'): Promise<TrendsAnalyticsData> {
    if (isMock()) {
      await simulateMockLatency();
      return { ...MOCK_TRENDS_ANALYTICS, metric_type: metricType as any };
    }

    const { data } = await apiClient.get<TrendsAnalyticsData>('/analytics/trends', {
      params: { metric_type: metricType },
    });
    return data;
  },

  async getOverviewAnalytics(): Promise<OverviewAnalytics> {
    if (isMock()) {
      await simulateMockLatency();
      return MOCK_OVERVIEW_ANALYTICS;
    }

    const { data } = await apiClient.get<OverviewAnalytics>('/analytics/overview');
    return data;
  },

  async getPerformanceEstimate(paperId: number): Promise<PerformanceEstimate> {
    if (isMock()) {
      await simulateMockLatency();
      return (
        MOCK_PERFORMANCE_ESTIMATES[paperId] || {
          estimated_pass_percentage: 72.0,
          estimated_average_marks: 58.0,
          reason: null,
        }
      );
    }

    const { data } = await apiClient.get<PerformanceEstimate>(`/papers/${paperId}/performance-estimate`);
    return data;
  },
};

