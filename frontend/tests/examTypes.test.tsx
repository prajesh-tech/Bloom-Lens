import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, expect, it, vi } from 'vitest';
import { FilePreview } from '../src/components/upload/FilePreview';
import { apiClient } from '../src/services/api';

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); });

it('renders exactly the examination types returned by the backend', async () => {
  vi.stubEnv('VITE_USE_MOCK_API', 'false');
  vi.spyOn(apiClient, 'get').mockResolvedValue({ data: ['Internal', 'Mid-Term'] });
  const noop = () => {};
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <FilePreview file={new File(['paper'], 'paper.pdf')} subjectCode="CS" setSubjectCode={noop}
      subjectName="CS" setSubjectName={noop} examType="Internal" setExamType={noop}
      maxMarks={10} setMaxMarks={noop} yearDate="" setYearDate={noop} onRemove={noop} />
  </QueryClientProvider>);
  await screen.findByRole('option', { name: 'Internal' });
  expect(screen.getAllByRole('option').map((option) => option.textContent)).toEqual(['Internal', 'Mid-Term']);
});
