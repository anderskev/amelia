import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorkflowsPage from './WorkflowsPage';

// Mock data matching actual WorkflowSummary type
const mockWorkflows = [
  {
    id: 'wf-001',
    issue_id: 'PROJ-123',
    worktree_name: 'proj-123-feature',
    status: 'in_progress' as const,
    started_at: '2025-12-07T09:00:00Z',
    current_stage: 'developer',
  },
];

// Mock hooks
vi.mock('@/hooks/useWorkflows', () => ({
  useWorkflows: vi.fn(),
}));

import { useWorkflows } from '@/hooks/useWorkflows';

describe('WorkflowsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render JobQueue when workflows exist', () => {
    vi.mocked(useWorkflows).mockReturnValue({
      workflows: mockWorkflows,
      isConnected: true,
      isRevalidating: false,
      revalidate: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkflowsPage />
      </MemoryRouter>
    );

    // JobQueue uses data-slot attribute
    expect(document.querySelector('[data-slot="job-queue"]')).toBeInTheDocument();
  });

  it('should render WorkflowEmptyState when no workflows', () => {
    vi.mocked(useWorkflows).mockReturnValue({
      workflows: [],
      isConnected: true,
      isRevalidating: false,
      revalidate: vi.fn(),
    });

    render(
      <MemoryRouter>
        <WorkflowsPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/no active workflows/i)).toBeInTheDocument();
  });
});
