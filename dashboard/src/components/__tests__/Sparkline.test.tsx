import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Sparkline } from '../Sparkline';

describe('Sparkline', () => {
  it('should render SVG element', () => {
    render(<Sparkline data={[1, 2, 3]} color="var(--chart-model-1)" />);

    const svg = screen.getByRole('img', { hidden: true });
    expect(svg).toBeInTheDocument();
    expect(svg.tagName).toBe('svg');
  });

  it('should render polyline with data points', () => {
    const { container } = render(
      <Sparkline data={[0, 12, 6]} color="var(--chart-model-1)" />
    );

    const polyline = container.querySelector('polyline');
    expect(polyline).toBeInTheDocument();
    expect(polyline).toHaveAttribute('stroke', 'var(--chart-model-1)');
  });

  it('should handle empty data gracefully', () => {
    const { container } = render(
      <Sparkline data={[]} color="var(--chart-model-1)" />
    );

    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('should handle single data point', () => {
    const { container } = render(
      <Sparkline data={[5]} color="var(--chart-model-1)" />
    );

    const polyline = container.querySelector('polyline');
    expect(polyline).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <Sparkline data={[1, 2, 3]} color="var(--chart-model-1)" className="custom-class" />
    );

    expect(container.querySelector('svg')).toHaveClass('custom-class');
  });
});
