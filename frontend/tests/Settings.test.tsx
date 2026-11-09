import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { Settings } from '../src/pages/Settings';

afterEach(() => { vi.unstubAllEnvs(); });
it('describes unset mock mode as real API configuration without claiming connectivity', () => {
  vi.stubEnv('VITE_USE_MOCK_API', '');
  vi.stubEnv('VITE_API_BASE_URL', '');
  render(<Settings />);
  expect(screen.getByText('Real API mode')).toBeInTheDocument();
  expect(screen.getByText('Same origin (/api/v1)')).toBeInTheDocument();
  expect(screen.queryByText(/Backend Connected/)).not.toBeInTheDocument();
});
