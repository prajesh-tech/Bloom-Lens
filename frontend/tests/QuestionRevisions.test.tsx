import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { QuestionRevisions } from '../src/components/analysis/QuestionRevisions';
import { analysisApi } from '../src/services/analysisApi';

afterEach(() => { vi.restoreAllMocks(); });
it('shows the acting reviewer and before/after values', async () => {
  vi.spyOn(analysisApi, 'getQuestionRevisions').mockResolvedValue([{ id: 1, question_id: 12,
    acting_user: 'reviewer:1:alice', created_at: '2026-11-09T10:00:00Z', old_value: { marks: 5 }, new_value: { marks: 7 } }]);
  render(<QueryClientProvider client={new QueryClient()}><QuestionRevisions questionId={12} /></QueryClientProvider>);
  expect(await screen.findByText(/reviewer:1:alice/)).toBeInTheDocument();
  expect(screen.getByText('5 → 7')).toBeInTheDocument();
});
