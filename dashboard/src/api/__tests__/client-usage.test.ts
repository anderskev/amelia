import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../client';
import type { UsageResponse } from '@/types';

const mockUsageResponse: UsageResponse = {
  summary: {
    total_cost_usd: 127.43,
    total_workflows: 24,
    total_tokens: 1_200_000,
    total_duration_ms: 2_820_000,
  },
  trend: [
    { date: '2026-01-15', cost_usd: 12.34, workflows: 3 },
  ],
  by_model: [
    { model: 'claude-sonnet-4', workflows: 18, tokens: 892_000, cost_usd: 42.17 },
  ],
};

describe('api.getUsage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('should fetch usage with preset', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    const result = await api.getUsage({ preset: '30d' });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?preset=30d'),
      expect.any(Object)
    );
    expect(result.summary.total_cost_usd).toBe(127.43);
  });

  it('should fetch usage with date range', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    const result = await api.getUsage({ start: '2026-01-01', end: '2026-01-15' });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?start=2026-01-01&end=2026-01-15'),
      expect.any(Object)
    );
    expect(result).toEqual(mockUsageResponse);
  });

  it('should default to preset=30d when no params', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUsageResponse,
    } as Response);

    await api.getUsage({});

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/usage?preset=30d'),
      expect.any(Object)
    );
  });
});
