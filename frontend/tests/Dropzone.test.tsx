import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Dropzone } from '../src/components/upload/Dropzone';

describe('Dropzone Component', () => {
  it('renders file upload dropzone UI correctly', () => {
    render(<Dropzone onFileSelect={() => {}} />);
    expect(screen.getByText('Upload Question Paper')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop your examination question paper/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOCX/i)).toBeInTheDocument();
  });
});
