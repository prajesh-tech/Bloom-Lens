export const queryKeys = {
  overview: ['analytics', 'overview'] as const,
  bloomAnalytics: (subjectId?: number) => ['analytics', 'bloom', subjectId ?? 'all'] as const,
  trends: (metricType: string) => ['analytics', 'trends', metricType] as const,
  history: (page: number, limit: number) => ['papers', 'history', page, limit] as const,
  paper: (paperId: number) => ['papers', paperId] as const,
  paperQuestions: (paperId: number) => ['papers', paperId, 'questions'] as const,
};
