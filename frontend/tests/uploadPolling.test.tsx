import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { analysisApi } from '../src/services/analysisApi';
import { usePaperStatusQuery } from '../src/services/queries';

afterEach(() => { vi.restoreAllMocks(); });

it('polls processing and stops at the completed status', async () => {
  const get = vi.spyOn(analysisApi, 'getPaperStatus')
    .mockResolvedValueOnce({ paper_id: 1, processing_status: 'PROCESSING', message: 'Processing' })
    .mockResolvedValue({ paper_id: 1, processing_status: 'COMPLETED', message: 'Done' });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const { result, unmount } = renderHook(() => usePaperStatusQuery(1), { wrapper });
  await waitFor(() => expect(result.current.data?.processing_status).toBe('COMPLETED'), { timeout: 4000 });
  await new Promise((resolve) => setTimeout(resolve, 1200));
  expect(get).toHaveBeenCalledTimes(2);
  const query = client.getQueryCache().getAll()[0];
  expect(query.state.data).toMatchObject({ processing_status: 'COMPLETED' });
  unmount();
  client.clear();
});

it('exposes the persisted processing failure', async () => {
  vi.spyOn(analysisApi, 'getPaperStatus').mockResolvedValue({ paper_id: 2, processing_status: 'FAILED', message: 'Extraction failed', error_message: 'Extraction failed' });
  const client = new QueryClient();
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const { result, unmount } = renderHook(() => usePaperStatusQuery(2), { wrapper });
  await waitFor(() => expect(result.current.data?.error_message).toBe('Extraction failed'));
  unmount();
  client.clear();
});
