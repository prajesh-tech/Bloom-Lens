import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analysisApi } from './analysisApi';
import { historyApi } from './historyApi';
import { queryKeys } from './queryKeys';
import { PaperUploadPayload } from '../types/paper';
import { QuestionPatchPayload } from '../types/question';

export function useExamTypesQuery() {
  return useQuery({ queryKey: ['papers', 'exam-types'], queryFn: () => analysisApi.getExamTypes() });
}

export function useSimilarQuestionsQuery(questionId: number) {
  return useQuery({ queryKey: ['questions', questionId, 'similar'], queryFn: () => analysisApi.getSimilarQuestions(questionId) });
}

export function usePaperStatusQuery(paperId?: number) {
  return useQuery({
    queryKey: ['papers', paperId, 'status'],
    queryFn: () => analysisApi.getPaperStatus(paperId!),
    enabled: paperId !== undefined,
    refetchInterval: (query) => ['COMPLETED', 'REVIEW_REQUIRED', 'FAILED'].includes(query.state.data?.processing_status ?? '') ? false : 1000,
  });
}

export function useSubjectsQuery() {
  return useQuery({ queryKey: ['subjects'], queryFn: () => analysisApi.getSubjects() });
}

export function useTopicAnalyticsQuery(subjectId?: number) {
  return useQuery({ queryKey: ['analytics', 'topics', subjectId ?? 'all'], queryFn: () => analysisApi.getTopicAnalytics(subjectId) });
}

export function useQuestionAnalyticsQuery(subjectId?: number) {
  return useQuery({ queryKey: ['analytics', 'questions', subjectId ?? 'all'], queryFn: () => analysisApi.getQuestionAnalytics(subjectId) });
}

export function useTrendsQuery(metricType: 'count' | 'marks_weighted', subjectId?: number) {
  return useQuery({ queryKey: queryKeys.trends(metricType, subjectId), queryFn: () => analysisApi.getTrendsAnalytics(metricType, subjectId) });
}

export function useQuestionRevisionsQuery(questionId: number) {
  return useQuery({ queryKey: ['questions', questionId, 'revisions'], queryFn: () => analysisApi.getQuestionRevisions(questionId) });
}

export function useBloomAnalyticsQuery(subjectId?: number) {
  return useQuery({ queryKey: queryKeys.bloomAnalytics(subjectId), queryFn: () => analysisApi.getBloomAnalytics(subjectId) });
}

export function useDashboardQueries(subjectId?: number) {
  const overview = useQuery({
    queryKey: queryKeys.overview(subjectId),
    queryFn: () => analysisApi.getOverviewAnalytics(subjectId),
  });

  const bloom = useBloomAnalyticsQuery(subjectId);

  const history = useQuery({
    queryKey: queryKeys.history(1, 5, subjectId),
    queryFn: () => historyApi.getHistory(1, 5, subjectId),
  });

  return { overview, bloom, history };
}

export function useHistoryQuery(page = 1, limit = 50) {
  return useQuery({
    queryKey: queryKeys.history(page, limit),
    queryFn: () => historyApi.getHistory(page, limit),
  });
}

export function useAnalysisResultQueries(paperId: number) {
  const paper = useQuery({
    queryKey: queryKeys.paper(paperId),
    queryFn: () => analysisApi.getQuestionPaper(paperId),
    enabled: Number.isFinite(paperId),
  });

  const questions = useQuery({
    queryKey: queryKeys.paperQuestions(paperId),
    queryFn: () => analysisApi.getPaperQuestions(paperId),
    enabled: Number.isFinite(paperId),
  });

  return { paper, questions };
}

export function usePerformanceEstimateQuery(paperId: number) {
  return useQuery({
    queryKey: queryKeys.performanceEstimate(paperId),
    queryFn: () => analysisApi.getPerformanceEstimate(paperId),
    enabled: Number.isFinite(paperId),
  });
}

export function useUploadPaperMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PaperUploadPayload) => analysisApi.uploadQuestionPaper(payload),
    onSuccess: (paper) => {
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.setQueryData(queryKeys.paper(paper.id), paper);
    },
  });
}

export function useDeletePaperMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (paperId: number) => analysisApi.deleteQuestionPaper(paperId),
    onSuccess: (_, paperId) => {
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.removeQueries({ queryKey: queryKeys.paper(paperId) });
      queryClient.removeQueries({ queryKey: queryKeys.paperQuestions(paperId) });
      queryClient.removeQueries({ queryKey: queryKeys.performanceEstimate(paperId) });
    },
  });
}

export function usePatchQuestionMutation(paperId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ questionId, payload }: { questionId: number; payload: QuestionPatchPayload }) =>
      analysisApi.patchQuestion(questionId, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.paperQuestions(paperId), (previous: unknown) => {
        if (!Array.isArray(previous)) return previous;
        return previous.map((question) =>
          question && typeof question === 'object' && 'id' in question && question.id === updated.id
            ? { ...question, ...updated }
            : question
        );
      });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.invalidateQueries({ queryKey: queryKeys.performanceEstimate(paperId) });
      queryClient.invalidateQueries({ queryKey: ['questions', updated.id] });
    },
  });
}
