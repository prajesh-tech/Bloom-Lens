export const queryKeys = {
  overview: (subjectId?: number) => ['analytics', 'overview', subjectId ?? 'all'] as const,
  bloomAnalytics: (subjectId?: number) => ['analytics', 'bloom', subjectId ?? 'all'] as const,
  trends: (metricType: string, subjectId?: number) => ['analytics', 'trends', metricType, subjectId ?? 'all'] as const,
  history: (page: number, limit: number, subjectId?: number) => ['papers', 'history', page, limit, subjectId ?? 'all'] as const,
  paper: (paperId: number) => ['papers', paperId] as const,
  paperQuestions: (paperId: number) => ['papers', paperId, 'questions'] as const,
  performanceEstimate: (paperId: number) => ['papers', paperId, 'performance-estimate'] as const,
};
