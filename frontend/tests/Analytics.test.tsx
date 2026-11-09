import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { Analytics } from '../src/pages/Analytics';
import { analysisApi } from '../src/services/analysisApi';

vi.mock('../src/components/charts/BloomBarChart', () => ({ BloomBarChart: () => <p>Bloom chart</p> }));
afterEach(() => { vi.restoreAllMocks(); });

it('renders topic/repetition analytics and changes the server subject filter', async () => {
  vi.spyOn(analysisApi, 'getSubjects').mockResolvedValue([{ id: 1, code: 'DB', name: 'Databases' }, { id: 2, code: 'NET', name: 'Networks' }]);
  const topics = vi.spyOn(analysisApi, 'getTopicAnalytics').mockImplementation(async (subjectId) => ({ topics: [{ topic_id: subjectId ?? 1, topic: subjectId === 2 ? 'Routing' : 'Normalization', frequency: 1, total_marks: 5, bloom_breakdown: { L2: 1 } }] }));
  vi.spyOn(analysisApi, 'getQuestionAnalytics').mockResolvedValue({ repeated_questions_count: 3, similar_questions_count: 2, highest_mark_questions: [], question_type_distribution: {} });
  vi.spyOn(analysisApi, 'getBloomAnalytics').mockResolvedValue({ distributions: [], total_marks: 0, total_questions: 0 });
  vi.spyOn(analysisApi, 'getTrendsAnalytics').mockResolvedValue({ metric_type: 'marks_weighted', trends: [] });
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><Analytics /></QueryClientProvider>);
  expect(await screen.findByText('Normalization')).toBeInTheDocument();
  expect(screen.getByText('Repeated questions')).toBeInTheDocument();
  await screen.findByRole('option', { name: 'NET — Networks' });
  fireEvent.change(screen.getByRole('combobox', { name: 'Subject' }), { target: { value: '2' } });
  expect(await screen.findByText('Routing')).toBeInTheDocument();
  await waitFor(() => expect(topics).toHaveBeenCalledWith(2));
  expect(screen.queryByText('Normalization')).not.toBeInTheDocument();
});
