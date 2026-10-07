import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PerformanceEstimateCard } from '../src/components/analysis/PerformanceEstimateCard';
import { analysisApi } from '../src/services/analysisApi';
import { MOCK_PERFORMANCE_ESTIMATES } from '../src/services/mockData';

// Mock the queries module to avoid real network/queryClient dependency in direct unit tests
vi.mock('../src/services/queries', () => ({
  usePerformanceEstimateQuery: vi.fn().mockReturnValue({
    data: null,
    isLoading: false,
    isError: false,
  }),
}));

describe('PerformanceEstimateCard Component', () => {
  it('renders both values with Estimated labels and neutral note', () => {
    render(
      <PerformanceEstimateCard
        paperId={101}
        maxMarks={100}
        estimate={{
          estimated_pass_percentage: 72.0,
          estimated_average_marks: 58.0,
          reason: null,
        }}
        isLoading={false}
        isError={false}
      />
    );

    // Verify Title
    expect(screen.getByText('Estimated Student Performance')).toBeInTheDocument();

    // Verify Metric 1
    expect(screen.getByText('Estimated Pass Percentage')).toBeInTheDocument();
    expect(screen.getByTestId('estimated-pass-pct')).toHaveTextContent('72%');

    // Verify Metric 2
    expect(screen.getByText('Estimated Average Marks')).toBeInTheDocument();
    expect(screen.getByTestId('estimated-avg-marks')).toHaveTextContent('58 / 100');

    // Verify multiple 'Estimated' labels
    const estimatedLabels = screen.getAllByText('Estimated');
    expect(estimatedLabels.length).toBeGreaterThanOrEqual(2);

    // Verify neutral disclaimer note
    expect(
      screen.getByText(/Heuristic estimate based solely on this paper's Bloom's Taxonomy and marks distribution\. Not actual student performance\./i)
    ).toBeInTheDocument();
  });

  it('renders loading skeleton state', () => {
    render(
      <PerformanceEstimateCard
        paperId={101}
        isLoading={true}
        isError={false}
      />
    );

    expect(screen.getByTestId('performance-estimate-loading')).toBeInTheDocument();
  });

  it('renders error state safely without breaking', () => {
    render(
      <PerformanceEstimateCard
        paperId={101}
        isLoading={false}
        isError={true}
      />
    );

    expect(screen.getByTestId('performance-estimate-error')).toBeInTheDocument();
    expect(screen.getByText(/Unable to calculate performance estimate at this time/i)).toBeInTheDocument();
  });

  it('renders unavailable state with explanatory reason code', () => {
    render(
      <PerformanceEstimateCard
        paperId={101}
        estimate={{
          estimated_pass_percentage: null,
          estimated_average_marks: null,
          reason: 'no_valid_questions',
        }}
        isLoading={false}
        isError={false}
      />
    );

    expect(screen.getByTestId('performance-estimate-unavailable')).toBeInTheDocument();
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
    expect(screen.getByText(/No valid questions with confirmed marks and Bloom levels remain/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Heuristic estimate based solely on this paper's Bloom's Taxonomy and marks distribution\. Not actual student performance\./i)
    ).toBeInTheDocument();
  });

  it('returns valid deterministic mock estimate from analysisApi in mock mode', async () => {
    vi.stubEnv('VITE_USE_MOCK_API', 'true');

    try {
      const mockEstimate = MOCK_PERFORMANCE_ESTIMATES[101];
      expect(mockEstimate).toBeDefined();
      expect(mockEstimate.estimated_pass_percentage).toBe(72.0);
      expect(mockEstimate.estimated_average_marks).toBe(58.0);
      expect(mockEstimate.reason).toBeNull();

      const result = await analysisApi.getPerformanceEstimate(101);
      expect(result).toBeDefined();
      expect(result.estimated_pass_percentage).toBe(72.0);
      expect(result.estimated_average_marks).toBe(58.0);
    } finally {
      vi.unstubAllEnvs();
    }
  });
});
