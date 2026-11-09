import { apiClient } from './api';
import { isMock } from './mockMode';
import { readMockState, writeMockState } from './mockStore';
import { paperBloomDistributions } from '../utils/paperDistribution';
import { PaperUploadPayload, QuestionPaper, PerformanceEstimate, PaperStatus } from '../types/paper';
import { QuestionAnalysis, QuestionPatchPayload, SimilarQuestion, QuestionRevision } from '../types/question';
import { BloomAnalyticsData, TrendsAnalyticsData, OverviewAnalytics, Subject, TopicAnalyticsData, QuestionAnalyticsData } from '../types/analytics';
import { simulateMockLatency } from '../utils/latency';
import {
  MOCK_QUESTIONS_MAP,
  MOCK_PERFORMANCE_ESTIMATES,
} from './mockData';

export const analysisApi = {
  async getSubjects(): Promise<Subject[]> {
    if (isMock()) return [...new Map(readMockState().papers.map((paper) => [paper.subject_id, { id: paper.subject_id ?? paper.id, code: paper.subject_code, name: paper.subject_name }])).values()];
    const { data } = await apiClient.get<Subject[]>('/subjects');
    return data;
  },
  async getTopicAnalytics(subjectId?: number): Promise<TopicAnalyticsData> {
    if (isMock()) {
      const state = readMockState();
      const topics = new Map<string, TopicAnalyticsData['topics'][number]>();
      for (const paper of state.papers.filter((paper) => subjectId === undefined || paper.subject_id === subjectId)) {
        for (const question of state.questions[paper.id] ?? []) {
          if (!question.topic) continue;
          const item = topics.get(question.topic) ?? { topic: question.topic, frequency: 0, total_marks: 0 };
          item.frequency += 1;
          item.total_marks += question.marks ?? 0;
          topics.set(question.topic, item);
        }
      }
      return { topics: [...topics.values()] };
    }
    const { data } = await apiClient.get<TopicAnalyticsData>('/analytics/topics', { params: { subject_id: subjectId } });
    return data;
  },
  async getQuestionAnalytics(subjectId?: number): Promise<QuestionAnalyticsData> {
    if (isMock()) return { repeated_questions_count: 0, similar_questions_count: 0, highest_mark_questions: [], question_type_distribution: {} };
    const { data } = await apiClient.get<QuestionAnalyticsData>('/analytics/questions', { params: { subject_id: subjectId } });
    return data;
  },
  async getQuestionRevisions(questionId: number): Promise<QuestionRevision[]> {
    if (isMock()) return readMockState().revisions[questionId] ?? [];
    const { data } = await apiClient.get<QuestionRevision[]>(`/questions/${questionId}/revisions`);
    return data;
  },
  async getSimilarQuestions(questionId: number): Promise<SimilarQuestion[]> {
    if (isMock()) return [];
    const { data } = await apiClient.get<SimilarQuestion[]>(`/questions/${questionId}/similar`);
    return data;
  },
  async getPaperStatus(paperId: number): Promise<PaperStatus> {
    if (isMock()) return { paper_id: paperId, processing_status: 'COMPLETED', message: 'Done' };
    const { data } = await apiClient.get<PaperStatus>(`/papers/${paperId}/status`);
    return data;
  },
  async getExamTypes(): Promise<string[]> {
    if (isMock()) return [...new Set(readMockState().papers.map((paper) => paper.examination_type))];
    const { data } = await apiClient.get<string[]>('/papers/exam-types');
    return data;
  },

  async uploadQuestionPaper(payload: PaperUploadPayload): Promise<QuestionPaper> {
    if (isMock()) {
      await simulateMockLatency();
      const state = readMockState();
      const newId = Math.max(100, ...state.papers.map((paper) => paper.id)) + 1;
      const newPaper: QuestionPaper = {
        id: newId,
        subject_id: state.papers.find((paper) => paper.subject_code === payload.subject_code)?.subject_id ?? Math.max(0, ...state.papers.map((paper) => paper.subject_id ?? 0)) + 1,
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
      state.papers = [newPaper, ...state.papers];
      state.questions[newId] = MOCK_QUESTIONS_MAP[101].map((q, idx) => ({
        ...q,
        id: newId * 10 + idx,
        question_paper_id: newId,
      }));
      writeMockState(state);
      return structuredClone(newPaper);
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
      const paper = readMockState().papers.find((p) => p.id === paperId);
      if (!paper) throw new Error("Question paper not found");
      return paper;
    }

    const { data } = await apiClient.get<QuestionPaper>(`/papers/${paperId}`);
    return data;
  },

  async deleteQuestionPaper(paperId: number): Promise<void> {
    if (isMock()) {
      await simulateMockLatency();
      const state = readMockState();
      state.papers = state.papers.filter((paper) => paper.id !== paperId);
      delete state.questions[paperId];
      writeMockState(state);
      return;
    }

    await apiClient.delete(`/papers/${paperId}`);
  },

  async getPaperQuestions(paperId: number): Promise<QuestionAnalysis[]> {
    if (isMock()) {
      await simulateMockLatency();
      return readMockState().questions[paperId] || [];
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
      const state = readMockState();
      for (const qList of Object.values(state.questions)) {
        const q = qList.find((item) => item.id === questionId);
        if (q) {
          const oldValue = structuredClone(q);
          if (payload.question_text !== undefined) {
            q.original_text = payload.question_text;
            q.normalized_text = payload.question_text.toLowerCase().replace(/\s+/g, ' ').trim();
            q.ai_analysis_metadata = { ...q.ai_analysis_metadata, needs_reanalysis: true };
          }
          if (payload.co_mapping !== undefined) q.co_mapping = payload.co_mapping;
          if (payload.choice_group !== undefined) q.choice_group = payload.choice_group;
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
          const revisions = state.revisions[q.id] ?? [];
          state.revisions[q.id] = [{ id: revisions.length + 1, question_id: q.id, acting_user: 'demo_reviewer', created_at: new Date().toISOString(), old_value: { ...oldValue }, new_value: { ...q } }, ...revisions];
          writeMockState(state);
          return structuredClone(q);
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
      const state = readMockState();
      const ids = new Set(state.papers.filter((paper) => subjectId === undefined || paper.subject_id === subjectId).map((paper) => paper.id));
      const distributions = paperBloomDistributions(Object.entries(state.questions).filter(([id]) => ids.has(Number(id))).flatMap(([, questions]) => questions));
      return { distributions, total_questions: distributions.reduce((sum, item) => sum + item.question_count, 0), total_marks: distributions.reduce((sum, item) => sum + item.total_marks, 0) };
    }

    const { data } = await apiClient.get<BloomAnalyticsData>('/analytics/bloom', {
      params: { subject_id: subjectId },
    });
    return data;
  },

  async getTrendsAnalytics(metricType: 'count' | 'marks_weighted' = 'marks_weighted', subjectId?: number): Promise<TrendsAnalyticsData> {
    if (isMock()) {
      await simulateMockLatency();
      const state = readMockState();
      return { metric_type: metricType, trends: state.papers
        .filter((paper) => subjectId === undefined || paper.subject_id === subjectId)
        .sort((a, b) => (a.year_date ?? '').localeCompare(b.year_date ?? ''))
        .map((paper) => {
          const distributions = paperBloomDistributions(state.questions[paper.id] ?? []);
          const value = (code: string) => {
            const item = distributions.find((distribution) => distribution.bloom_level === code);
            return (metricType === 'count' ? item?.question_count_percentage : item?.marks_percentage) ?? 0;
          };
          return { paper_id: paper.id, paper: paper.original_filename, year: paper.year_date,
            L1: value('L1'), L2: value('L2'), L3: value('L3'), L4: value('L4'), L5: value('L5'), L6: value('L6') };
        }) };
    }

    const { data } = await apiClient.get<TrendsAnalyticsData>('/analytics/trends', {
      params: { metric_type: metricType, subject_id: subjectId },
    });
    return data;
  },

  async getOverviewAnalytics(subjectId?: number): Promise<OverviewAnalytics> {
    if (isMock()) {
      await simulateMockLatency();
      const state = readMockState();
      const papers = state.papers.filter((paper) => subjectId === undefined || paper.subject_id === subjectId);
      const bloom = await analysisApi.getBloomAnalytics(subjectId);
      return { papers_analyzed: papers.length, questions_analyzed: bloom.total_questions,
        subjects_count: new Set(papers.map((paper) => paper.subject_id)).size,
        topics_count: new Set(papers.flatMap((paper) => (state.questions[paper.id] ?? []).map((question) => question.topic))).size,
        total_relevant_marks: bloom.total_marks };
    }

    const { data } = await apiClient.get<OverviewAnalytics>('/analytics/overview', { params: { subject_id: subjectId } });
    return data;
  },

  async getPerformanceEstimate(paperId: number): Promise<PerformanceEstimate> {
    if (isMock()) {
      await simulateMockLatency();
      return structuredClone(
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
