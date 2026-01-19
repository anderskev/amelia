import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostsTrendChart } from './CostsTrendChart';
import type { UsageTrendPoint } from '@/types';

const mockTrend: UsageTrendPoint[] = [
  { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
  { date: '2026-01-16', cost_usd: 15.67, workflows: 4 },
  { date: '2026-01-17', cost_usd: 8.90, workflows: 2 },
];

describe('CostsTrendChart', () => {
  it('should render chart container', () => {
    render(<CostsTrendChart data={mockTrend} />);

    // Chart container should exist
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });

  it('should show empty state when no data', () => {
    render(<CostsTrendChart data={[]} />);

    expect(screen.getByText(/no data/i)).toBeInTheDocument();
  });

  it('should display chart with data-slot attribute', () => {
    const { container } = render(<CostsTrendChart data={mockTrend} />);

    expect(container.querySelector('[data-slot="costs-trend-chart"]')).toBeInTheDocument();
  });
});
