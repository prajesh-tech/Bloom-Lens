import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BloomDonutChart } from '../src/components/charts/BloomDonutChart';
import { CustomTooltip } from '../src/components/charts/CustomTooltip';
import { HistoryTable } from '../src/components/history/HistoryTable';
import { SummaryCards } from '../src/components/analysis/SummaryCards';
import { ThemeProvider } from '../src/context/ThemeContext';
import { getBloomCode } from '../src/config/bloomConfig';
import { BloomDistributionItem } from '../src/types/analytics';
import { QuestionPaper } from '../src/types/paper';
import { formatMarks } from '../src/utils/formatters';

vi.mock('recharts', async (importOriginal) => {
  const recharts = await importOriginal<typeof import('recharts')>();
  return {
    ...recharts,
    ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  };
});

const paper: QuestionPaper = {
  id: 1,
  subject_code: 'CS101',
  subject_name: 'Computer Science',
  examination_type: 'Final',
  maximum_marks: 100,
  original_filename: 'paper.pdf',
  upload_timestamp: '2026-01-01T00:00:00Z',
  processing_status: 'FAILED',
  extraction_status: 'FAILED',
  validation_status: 'uncertain',
  optional_question_flag: false,
};

const distributions: BloomDistributionItem[] = [
  {
    bloom_level: 'L1',
    name: 'Remember',
    question_count: 2,
    question_count_percentage: 40,
    total_marks: 10,
    marks_percentage: 25,
  },
  {
    bloom_level: 'L2',
    name: 'Understand',
    question_count: 3,
    question_count_percentage: 60,
    total_marks: 30,
    marks_percentage: 75,
  },
];

describe('analysis bug fixes', () => {
  it('matches Bloom codes exactly rather than treating L10 as L1', () => {
    expect(getBloomCode('L1')).toBe('L1');
    expect(getBloomCode('L10')).toBeUndefined();
    expect(getBloomCode('remember')).toBe('L1');
  });

  it('does not zero-pad fractional marks', () => {
    expect(formatMarks(2.5)).toBe('2.5 marks');
    expect(formatMarks(5)).toBe('05 marks');
  });

  it('shows marks instead of question count in the marks-weighted tooltip', () => {
    render(
      <CustomTooltip
        active
        payload={[{ payload: { name: 'Remember', value: 25, question_count: 8, total_marks: 10 } }]}
      />
    );

    expect(screen.getByText('Total Marks:')).toBeInTheDocument();
    expect(screen.getByText('10 marks')).toBeInTheDocument();
    expect(screen.queryByText('8 Questions')).not.toBeInTheDocument();
  });

  it('uses the chart distribution total as the donut center count', () => {
    render(
      <ThemeProvider>
        <BloomDonutChart data={distributions} />
      </ThemeProvider>
    );

    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('uses warning styling for lowercase uncertain validation status', () => {
    render(<SummaryCards paper={paper} questionCount={4} />);

    expect(screen.getByText('uncertain').className).toContain('amber');
  });

  it('uses danger styling for failed processing status', () => {
    render(
      <MemoryRouter>
        <HistoryTable papers={[paper]} />
      </MemoryRouter>
    );

    expect(screen.getByText('FAILED').className).toContain('rose');
  });
});
