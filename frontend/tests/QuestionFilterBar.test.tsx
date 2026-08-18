import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QuestionFilterBar } from '../src/components/analysis/QuestionFilterBar';

describe('QuestionFilterBar Component', () => {
  it('renders search input and triggers change handler', () => {
    const handleSearchChange = vi.fn();
    render(
      <QuestionFilterBar
        searchQuery=""
        onSearchChange={handleSearchChange}
        selectedBloom="ALL"
        onBloomChange={() => {}}
        onReset={() => {}}
        filteredCount={10}
        totalCount={10}
      />
    );

    const input = screen.getByPlaceholderText(/Search questions/i);
    fireEvent.change(input, { target: { value: 'normalization' } });
    expect(handleSearchChange).toHaveBeenCalledWith('normalization');
  });

  it('renders Bloom level pill filter buttons', () => {
    const handleBloomChange = vi.fn();
    render(
      <QuestionFilterBar
        searchQuery=""
        onSearchChange={() => {}}
        selectedBloom="ALL"
        onBloomChange={handleBloomChange}
        onReset={() => {}}
        filteredCount={10}
        totalCount={10}
      />
    );

    const rememberBtn = screen.getByText('Remember');
    fireEvent.click(rememberBtn);
    expect(handleBloomChange).toHaveBeenCalledWith('Remember');
  });
});
