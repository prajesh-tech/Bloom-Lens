import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { Home } from '../src/pages/Home';
import { analysisApi } from '../src/services/analysisApi';
import { historyApi } from '../src/services/historyApi';

vi.mock('../src/components/charts/BloomBarChart', () => ({ BloomBarChart: () => <p>Bar chart</p> }));
vi.mock('../src/components/charts/BloomDonutChart', () => ({ BloomDonutChart: () => <p>Donut chart</p> }));
afterEach(() => { vi.restoreAllMocks(); });

it('scopes dashboard overview, Bloom and recent papers to the selected subject', async () => {
  vi.spyOn(analysisApi, 'getSubjects').mockResolvedValue([{ id: 7, code: 'CS7', name: 'Networks' }]);
  const overview = vi.spyOn(analysisApi, 'getOverviewAnalytics').mockResolvedValue({ papers_analyzed: 2, questions_analyzed: 3, subjects_count: 1, topics_count: 1, total_relevant_marks: 20 });
  const bloom = vi.spyOn(analysisApi, 'getBloomAnalytics').mockResolvedValue({ distributions: [], total_questions: 0, total_marks: 0 });
  const history = vi.spyOn(historyApi, 'getHistory').mockResolvedValue({ items: [], page: 1, limit: 5, total: 0 });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(<QueryClientProvider client={client}><MemoryRouter><Home /></MemoryRouter></QueryClientProvider>);
  await screen.findByRole('option', { name: 'CS7 — Networks' });
  fireEvent.change(screen.getByRole('combobox', { name: 'Subject' }), { target: { value: '7' } });
  await waitFor(() => {
    expect(overview).toHaveBeenCalledWith(7);
    expect(bloom).toHaveBeenCalledWith(7);
    expect(history).toHaveBeenCalledWith(1, 5, 7);
  });
  view.unmount(); client.clear();
});
