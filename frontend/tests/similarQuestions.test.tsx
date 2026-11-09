import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { SimilarQuestions } from '../src/components/analysis/SimilarQuestions';
import { analysisApi } from '../src/services/analysisApi';

afterEach(() => { vi.restoreAllMocks(); });

it('shows the returned repeated question and its classification', async () => {
  vi.spyOn(analysisApi, 'getSimilarQuestions').mockResolvedValue([{ id: 1, source_question_id: 12,
    target_question_id: 20, target_question_text: 'Describe ACID properties.', target_question_number: 'Q2',
    similarity_score: 0.97, similarity_type: 'semantic_repeat', classification: 'near_duplicate' }]);
  render(<QueryClientProvider client={new QueryClient()}><SimilarQuestions questionId={12} /></QueryClientProvider>);
  expect(await screen.findByText('Describe ACID properties.')).toBeInTheDocument();
  expect(screen.getByText(/near duplicate/)).toBeInTheDocument();
});
