/**
 * Simulates network latency for mock API calls (1500ms - 2500ms).
 */
export async function simulateMockLatency(): Promise<void> {
  const isMock = import.meta.env.VITE_USE_MOCK_API !== 'false';
  if (!isMock) return;

  const delayMs = Math.floor(Math.random() * 1000) + 1500;
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}
