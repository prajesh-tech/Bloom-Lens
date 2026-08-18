import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BloomBadge } from '../src/components/common/BloomBadge';

describe('BloomBadge Component', () => {
  it('renders Remember level badge correctly', () => {
    render(<BloomBadge level="Remember" />);
    expect(screen.getByText('Remember')).toBeInTheDocument();
    expect(screen.getByText('[L1]')).toBeInTheDocument();
  });

  it('renders Analyze level from code L4 correctly', () => {
    render(<BloomBadge level="L4" />);
    expect(screen.getByText('Analyze')).toBeInTheDocument();
    expect(screen.getByText('[L4]')).toBeInTheDocument();
  });

  it('renders fallback for unclassified questions', () => {
    render(<BloomBadge level={null} />);
    expect(screen.getByText('Not Classified')).toBeInTheDocument();
  });
});
