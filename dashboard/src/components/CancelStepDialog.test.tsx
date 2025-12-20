import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CancelStepDialog } from './CancelStepDialog';

describe('CancelStepDialog', () => {
  const defaultProps = {
    stepDescription: 'Running unit tests',
    isOpen: true,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('shows warning message with step description', () => {
    render(<CancelStepDialog {...defaultProps} />);

    expect(screen.getByText('Cancel Step?')).toBeInTheDocument();
    expect(screen.getByText(/are you sure you want to cancel this step/i)).toBeInTheDocument();
    expect(screen.getByText(/Running unit tests/)).toBeInTheDocument();
    expect(screen.getByText(/stopped mid-execution/i)).toBeInTheDocument();
  });

  it('displays warning icon', () => {
    render(<CancelStepDialog {...defaultProps} />);

    // The AlertTriangle icon should be in the document
    const alertIcon = document.querySelector('svg');
    expect(alertIcon).toBeInTheDocument();
  });

  it('shows Continue Running and Cancel Step buttons', () => {
    render(<CancelStepDialog {...defaultProps} />);

    expect(screen.getByRole('button', { name: /continue running/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel step/i })).toBeInTheDocument();
  });

  it('calls onConfirm when Cancel Step button is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(<CancelStepDialog {...defaultProps} onConfirm={onConfirm} />);

    const cancelButton = screen.getByRole('button', { name: /cancel step/i });
    await user.click(cancelButton);

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when Continue Running button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(<CancelStepDialog {...defaultProps} onCancel={onCancel} />);

    const continueButton = screen.getByRole('button', { name: /continue running/i });
    await user.click(continueButton);

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('does not render dialog when isOpen is false', () => {
    render(<CancelStepDialog {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Cancel Step?')).not.toBeInTheDocument();
  });

  it('Cancel Step button has destructive variant', () => {
    render(<CancelStepDialog {...defaultProps} />);

    const cancelButton = screen.getByRole('button', { name: /cancel step/i });
    expect(cancelButton).toHaveClass('bg-destructive');
  });

  it('Continue Running button has outline variant', () => {
    render(<CancelStepDialog {...defaultProps} />);

    const continueButton = screen.getByRole('button', { name: /continue running/i });
    // The AlertDialogCancel component applies the outline variant by default
    expect(continueButton.className).toMatch(/outline/);
  });
});
