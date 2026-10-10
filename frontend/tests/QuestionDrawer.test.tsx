import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { QuestionDrawer } from '../src/components/analysis/QuestionDrawer';
import { QuestionAnalysis } from '../src/types/question';

const question: QuestionAnalysis = {
  id: 12,
  question_paper_id: 3,
  question_number: 'Q1',
  original_text: 'Assess the approach.',
  marks: 5,
  ai_bloom_level: 'L4',
  effective_bloom_level: 'L4',
  review_status: 'AUTO_CLASSIFIED',
};

describe('QuestionDrawer human override', () => {
  it('sends the selected Bloom level as the API code expected by the server', async () => {
    const onSaveOverride = vi.fn().mockResolvedValue(undefined);
    render(
      <QuestionDrawer
        question={question}
        isOpen
        onClose={vi.fn()}
        onSaveOverride={onSaveOverride}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Override' }));
    fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'Evaluate' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Correction' }));

    await waitFor(() => expect(onSaveOverride).toHaveBeenCalled());
    expect(onSaveOverride).toHaveBeenCalledWith(
      12,
      expect.objectContaining({ bloom_level: 'L5' })
    );
  });
});
