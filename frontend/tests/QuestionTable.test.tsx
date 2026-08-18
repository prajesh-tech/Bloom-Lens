import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QuestionTable } from '../src/components/analysis/QuestionTable';
import { QuestionAnalysis } from '../src/types/question';

const mockQuestions: QuestionAnalysis[] = [
  {
    id: 1,
    question_paper_id: 101,
    question_number: 'Q1',
    original_text: 'Define normalization.',
    marks: 5,
    effective_bloom_level: 'Remember',
    bloom_confidence: 0.95,
    review_status: 'AUTO_CLASSIFIED',
  },
  {
    id: 2,
    question_paper_id: 101,
    question_number: 'Q2',
    original_text: 'Explain ACID properties.',
    marks: null,
    effective_bloom_level: 'Understand',
    bloom_confidence: 0.55, // Low confidence!
    review_status: 'FLAGGED',
  },
];

describe('QuestionTable Component', () => {
  it('renders question rows with monospace formatted IDs and marks', () => {
    render(
      <QuestionTable
        questions={mockQuestions}
        selectedQuestionId={null}
        onSelectQuestion={() => {}}
      />
    );

    expect(screen.getByText('Q01')).toBeInTheDocument();
    expect(screen.getByText('Define normalization.')).toBeInTheDocument();
    expect(screen.getByText('05 marks')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument(); // Missing marks
  });

  it('triggers onSelectQuestion callback when a row is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <QuestionTable
        questions={mockQuestions}
        selectedQuestionId={null}
        onSelectQuestion={handleSelect}
      />
    );

    const firstRowText = screen.getByText('Define normalization.');
    fireEvent.click(firstRowText);
    expect(handleSelect).toHaveBeenCalledWith(mockQuestions[0]);
  });
});
