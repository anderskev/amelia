import { describe, it, expect, vi, beforeEach } from 'vitest';
import { costsLoader } from '../costs';
import { api } from '@/api/client';
import type { UsageResponse } from '@/types';

vi.mock('@/api/client', () => ({
  api: {
    getUsage: vi.fn(),
  },
}));

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

describe('costsLoader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getUsage).mockResolvedValue(mockUsageResponse);
  });

  it('should use preset from URL params', async () => {
    const request = new Request('http://localhost/costs?preset=7d');

    const result = await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({ preset: '7d' });
    expect(result.usage).toEqual(mockUsageResponse);
  });

  it('should use date range from URL params', async () => {
    const request = new Request('http://localhost/costs?start=2026-01-01&end=2026-01-15');

    await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({
      start: '2026-01-01',
      end: '2026-01-15',
    });
  });

  it('should default to preset=30d when no params', async () => {
    const request = new Request('http://localhost/costs');

    await costsLoader({ request, params: {} } as any);

    expect(api.getUsage).toHaveBeenCalledWith({ preset: '30d' });
  });

  it('should return current params for UI state', async () => {
    const request = new Request('http://localhost/costs?preset=90d');

    const result = await costsLoader({ request, params: {} } as any);

    expect(result.currentPreset).toBe('90d');
  });
});
