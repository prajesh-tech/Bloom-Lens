import { afterEach, expect, it, vi } from 'vitest';
import { simulateMockLatency } from '../src/utils/latency';
afterEach(() => { vi.unstubAllEnvs(); vi.useRealTimers(); });
it('does not schedule mock latency unless mode is literally true', () => {
  vi.useFakeTimers();
  vi.stubEnv('VITE_USE_MOCK_API', '');
  void simulateMockLatency();
  expect(vi.getTimerCount()).toBe(0);
});
