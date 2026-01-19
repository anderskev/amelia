import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CostsPage from './CostsPage';
import type { CostsLoaderData } from '@/loaders/costs';

const mockLoaderData: CostsLoaderData = {
  usage: {
    summary: {
      total_cost_usd: 127.43,
      total_workflows: 24,
      total_tokens: 1_200_000,
      total_duration_ms: 2_820_000,
    },
    trend: [
      { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
      { date: '2026-01-16', cost_usd: 15.67, workflows: 4 },
    ],
    by_model: [
      { model: 'claude-sonnet-4', workflows: 18, tokens: 892_000, cost_usd: 42.17 },
      { model: 'claude-opus-4', workflows: 6, tokens: 340_000, cost_usd: 85.26 },
    ],
  },
  currentPreset: '30d',
  currentStart: null,
  currentEnd: null,
};

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...mod,
    useLoaderData: vi.fn(),
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams('?preset=30d'), vi.fn()],
  };
});

import { useLoaderData } from 'react-router-dom';

describe('CostsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useLoaderData).mockReturnValue(mockLoaderData);
  });

  it('should render page header with title', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('COSTS')).toBeInTheDocument();
    expect(screen.getByText('Usage & Spending')).toBeInTheDocument();
  });

  it('should display total cost in header', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    // Cost appears in both header and summary row
    const costElements = screen.getAllByText('$127.43');
    expect(costElements.length).toBeGreaterThanOrEqual(1);
  });

  it('should display summary row with metrics', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('24')).toBeInTheDocument(); // workflows
    expect(screen.getByText(/1200K/i)).toBeInTheDocument(); // tokens
  });

  it('should render model breakdown table', () => {
    render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('claude-sonnet-4')).toBeInTheDocument();
    expect(screen.getByText('claude-opus-4')).toBeInTheDocument();
    expect(screen.getByText('$42.17')).toBeInTheDocument();
    expect(screen.getByText('$85.26')).toBeInTheDocument();
  });

  it('should render trend chart', () => {
    const { container } = render(
      <MemoryRouter>
        <CostsPage />
      </MemoryRouter>
    );

    expect(container.querySelector('[data-slot="costs-trend-chart"]')).toBeInTheDocument();
  });
});
