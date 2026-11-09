import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { Analyze } from '../src/pages/Analyze';
import { analysisApi } from '../src/services/analysisApi';
import { toast } from '../src/components/common/Toast';
import { QuestionPaper } from '../src/types/paper';

vi.mock('../src/components/common/Toast', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));
const clients: QueryClient[] = [];
afterEach(() => {
  clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks();
});

async function startUpload() {
  vi.spyOn(analysisApi, 'getExamTypes').mockResolvedValue(['End-Semester']);
  vi.spyOn(analysisApi, 'uploadQuestionPaper').mockResolvedValue({ id: 55, processing_status: 'UPLOADED' } as QuestionPaper);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  clients.push(client);
  const view = render(<QueryClientProvider client={client}><MemoryRouter><Routes>
    <Route path="/" element={<Analyze />} /><Route path="/analysis/:id" element={<h1>Analysis results</h1>} />
  </Routes></MemoryRouter></QueryClientProvider>);
  fireEvent.change(view.container.querySelector('input[type="file"]')!, { target: { files: [new File(['PDF'], 'exam.pdf', { type: 'application/pdf' })] } });
  fireEvent.change(await screen.findByPlaceholderText('e.g. CS301'), { target: { value: 'CS301' } });
  fireEvent.change(screen.getByPlaceholderText('e.g. Database Management Systems'), { target: { value: 'Databases' } });
  await screen.findByRole('option', { name: 'End-Semester' });
  fireEvent.click(screen.getByRole('button', { name: 'Run BloomLens Analysis' }));
  return { client, ...view };
}

it('polls the accepted upload and opens results only after completion', async () => {
  const status = vi.spyOn(analysisApi, 'getPaperStatus')
    .mockResolvedValueOnce({ paper_id: 55, processing_status: 'PROCESSING', message: 'Extracting' })
    .mockResolvedValue({ paper_id: 55, processing_status: 'COMPLETED', message: 'Done' });
  const view = await startUpload();
  expect(await screen.findByText('Analyzing Question Paper')).toBeInTheDocument();
  expect(screen.queryByText('Analysis results')).not.toBeInTheDocument();
  expect(await screen.findByText('Analysis results', {}, { timeout: 4000 })).toBeInTheDocument();
  expect(status).toHaveBeenCalledTimes(2);
  view.unmount(); view.client.clear();
// This test includes form rendering and a real one-second polling interval.
// Allow for constrained CI scheduling without changing polling or assertions.
}, 15000);

it('returns to the upload form on terminal failure', async () => {
  vi.spyOn(analysisApi, 'getPaperStatus').mockResolvedValue({ paper_id: 55, processing_status: 'FAILED', message: 'Failed', error_message: 'Extraction failed safely' });
  const view = await startUpload();
  await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Extraction failed safely'));
  expect(await screen.findByRole('button', { name: 'Run BloomLens Analysis' })).toBeInTheDocument();
  expect(screen.queryByText('Analysis results')).not.toBeInTheDocument();
  view.unmount(); view.client.clear();
});

it('retries a failed status request without uploading again', async () => {
  const status = vi.spyOn(analysisApi, 'getPaperStatus').mockRejectedValueOnce(new Error('Offline'))
    .mockResolvedValue({ paper_id: 55, processing_status: 'COMPLETED', message: 'Done' });
  const view = await startUpload();
  fireEvent.click(await screen.findByRole('button', { name: 'Retry status check' }));
  expect(await screen.findByText('Analysis results')).toBeInTheDocument();
  expect(status).toHaveBeenCalledTimes(2);
  expect(analysisApi.uploadQuestionPaper).toHaveBeenCalledTimes(1);
  view.unmount(); view.client.clear();
});
