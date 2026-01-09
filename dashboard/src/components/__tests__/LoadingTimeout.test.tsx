import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { LoadingTimeout } from '../LoadingTimeout';

describe('LoadingTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('should show loading spinner initially', () => {
    render(<LoadingTimeout />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByText(/taking longer/i)).not.toBeInTheDocument();
  });

  it('should show timeout message after 10 seconds', () => {
    render(<LoadingTimeout />);

    // Advance 11 intervals (11 seconds) to exceed 10s threshold
    act(() => {
      vi.advanceTimersByTime(11000);
    });

    expect(screen.getByText(/taking longer than expected/i)).toBeInTheDocument();
  });

  it('should show connection hint after 30 seconds', () => {
    render(<LoadingTimeout />);

    // Advance 31 intervals (31 seconds) to exceed 30s threshold
    act(() => {
      vi.advanceTimersByTime(31000);
    });

    expect(screen.getByText(/check your connection/i)).toBeInTheDocument();
  });
});
