import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BlockerResolutionDialog } from './BlockerResolutionDialog';
import type { BlockerReport } from '@/types';

const mockBlocker: BlockerReport = {
  step_id: 'step-1',
  step_description: 'Run unit tests',
  blocker_type: 'command_failed',
  error_message: 'Test suite failed with 3 errors',
  attempted_actions: [
    'Tried running tests with --verbose flag',
    'Attempted to fix import paths',
  ],
  suggested_resolutions: [
    'Review test failures and fix failing tests',
    'Check for missing test dependencies',
  ],
};

const defaultProps = {
  blocker: mockBlocker,
  isOpen: true,
  onClose: vi.fn(),
  onRetry: vi.fn(),
  onSkip: vi.fn(),
  onFixInstruction: vi.fn(),
  onAbort: vi.fn(),
};

describe('BlockerResolutionDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Blocker Details', () => {
    it('renders blocker details', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByText('step-1')).toBeInTheDocument();
      expect(screen.getByText('Run unit tests')).toBeInTheDocument();
      expect(screen.getByText('Test suite failed with 3 errors')).toBeInTheDocument();
    });

    it('renders blocker type badge', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByText('command_failed')).toBeInTheDocument();
    });

    it('renders attempted actions list', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByText('Tried running tests with --verbose flag')).toBeInTheDocument();
      expect(screen.getByText('Attempted to fix import paths')).toBeInTheDocument();
    });

    it('renders AI suggested resolutions with label', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByText(/AI suggestions/i)).toBeInTheDocument();
      expect(screen.getByText('Review test failures and fix failing tests')).toBeInTheDocument();
      expect(screen.getByText('Check for missing test dependencies')).toBeInTheDocument();
    });
  });

  describe('Resolution Options', () => {
    it('renders Retry button as primary action', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('calls onRetry when Retry button is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /retry/i }));

      expect(defaultProps.onRetry).toHaveBeenCalledOnce();
    });

    it('renders Skip Step button', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /skip step/i })).toBeInTheDocument();
    });

    it('calls onSkip when Skip Step button is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /skip step/i }));

      expect(defaultProps.onSkip).toHaveBeenCalledOnce();
    });

    it('shows cascade skip count badge when cascadeSkips provided', () => {
      render(
        <BlockerResolutionDialog
          {...defaultProps}
          cascadeSkips={['step-2', 'step-3', 'step-4']}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('renders fix instruction textarea', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByPlaceholderText(/describe the fix/i)).toBeInTheDocument();
    });

    it('renders Apply Fix button', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /apply fix/i })).toBeInTheDocument();
    });

    it('calls onFixInstruction with text when Apply Fix is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/describe the fix/i);
      await user.type(textarea, 'Update import paths to use absolute paths');
      await user.click(screen.getByRole('button', { name: /apply fix/i }));

      expect(defaultProps.onFixInstruction).toHaveBeenCalledWith('Update import paths to use absolute paths');
    });

    it('disables Apply Fix button when textarea is empty', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      const applyButton = screen.getByRole('button', { name: /apply fix/i });
      expect(applyButton).toBeDisabled();
    });

    it('enables Apply Fix button when textarea has content', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/describe the fix/i);
      await user.type(textarea, 'Fix the tests');

      const applyButton = screen.getByRole('button', { name: /apply fix/i });
      expect(applyButton).toBeEnabled();
    });
  });

  describe('Abort Options', () => {
    it('renders Abort button group', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /keep changes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /revert batch/i })).toBeInTheDocument();
    });

    it('shows AlertDialog when Keep Changes is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /keep changes/i }));

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it('calls onAbort with false when Keep Changes is confirmed', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /keep changes/i }));

      // Find and click the confirm button in the AlertDialog
      const confirmButton = await screen.findByRole('button', { name: /^keep/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(defaultProps.onAbort).toHaveBeenCalledWith(false);
      });
    });

    it('shows AlertDialog when Revert Batch is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /revert batch/i }));

      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it('calls onAbort with true when Revert Batch is confirmed', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /revert batch/i }));

      // Find and click the confirm button in the AlertDialog
      const confirmButton = await screen.findByRole('button', { name: /revert/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(defaultProps.onAbort).toHaveBeenCalledWith(true);
      });
    });
  });

  describe('Cascade Skip Preview', () => {
    it('shows cascade skip preview when cascadeSkips provided', () => {
      render(
        <BlockerResolutionDialog
          {...defaultProps}
          cascadeSkips={['step-2', 'step-3']}
        />
      );

      expect(screen.getByText(/will also skip/i)).toBeInTheDocument();
      expect(screen.getByText('step-2')).toBeInTheDocument();
      expect(screen.getByText('step-3')).toBeInTheDocument();
    });

    it('does not show cascade preview when no cascadeSkips', () => {
      render(<BlockerResolutionDialog {...defaultProps} />);

      expect(screen.queryByText(/will also skip/i)).not.toBeInTheDocument();
    });

    it('does not show cascade preview when cascadeSkips is empty', () => {
      render(
        <BlockerResolutionDialog
          {...defaultProps}
          cascadeSkips={[]}
        />
      );

      expect(screen.queryByText(/will also skip/i)).not.toBeInTheDocument();
    });
  });

  describe('Dialog Control', () => {
    it('does not render when isOpen is false', () => {
      render(<BlockerResolutionDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Run unit tests')).not.toBeInTheDocument();
    });

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<BlockerResolutionDialog {...defaultProps} />);

      // Find close button (X icon in dialog header)
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(defaultProps.onClose).toHaveBeenCalledOnce();
    });
  });

  describe('Different Blocker Types', () => {
    it.each([
      { blocker_type: 'validation_failed' as const },
      { blocker_type: 'needs_judgment' as const },
      { blocker_type: 'unexpected_state' as const },
      { blocker_type: 'dependency_skipped' as const },
    ])('renders $blocker_type blocker type', ({ blocker_type }) => {
      render(
        <BlockerResolutionDialog
          {...defaultProps}
          blocker={{ ...mockBlocker, blocker_type }}
        />
      );

      expect(screen.getByText(blocker_type)).toBeInTheDocument();
    });
  });
});
