import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analysisApi } from './analysisApi';
import { historyApi } from './historyApi';
import { queryKeys } from './queryKeys';
import { PaperUploadPayload } from '../types/paper';
import { QuestionPatchPayload } from '../types/question';

export function useDashboardQueries() {
  const overview = useQuery({
    queryKey: queryKeys.overview,
    queryFn: () => analysisApi.getOverviewAnalytics(),
  });

  const bloom = useQuery({
    queryKey: queryKeys.bloomAnalytics(),
    queryFn: () => analysisApi.getBloomAnalytics(),
  });

  const history = useQuery({
    queryKey: queryKeys.history(1, 5),
    queryFn: () => historyApi.getHistory(1, 5),
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
    },
  });
}
