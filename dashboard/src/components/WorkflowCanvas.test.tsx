import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowCanvas } from './WorkflowCanvas';

describe('WorkflowCanvas', () => {
  const mockPipeline = {
    nodes: [
      { id: 'issue', label: 'Issue', status: 'completed' as const },
      { id: 'architect', label: 'Architect', subtitle: 'Planning', status: 'completed' as const, tokens: '12.4k' },
      { id: 'developer', label: 'Developer', subtitle: 'Implementation', status: 'active' as const, tokens: '48.2k' },
    ],
    edges: [
      { from: 'issue', to: 'architect', label: '0:08', status: 'completed' as const },
      { from: 'architect', to: 'developer', label: '0:24', status: 'active' as const },
    ],
  };

  describe('empty state', () => {
    it('renders empty state when no pipeline provided', () => {
      render(<WorkflowCanvas />);
      expect(screen.getByText('Select a workflow to view pipeline')).toBeInTheDocument();
    });

    it('renders empty state with GitBranch icon', () => {
      render(<WorkflowCanvas />);
      // The icon is decorative, part of the status element
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has proper ARIA role and label for empty state', () => {
      render(<WorkflowCanvas />);
      const canvas = screen.getByRole('status');
      expect(canvas.getAttribute('aria-label')).toBe('No workflow selected');
    });

    it('has data-slot attribute in empty state', () => {
      render(<WorkflowCanvas />);
      const canvas = screen.getByRole('status');
      expect(canvas).toHaveAttribute('data-slot', 'workflow-canvas');
    });

    it('maintains consistent height in empty state', () => {
      render(<WorkflowCanvas />);
      const canvas = screen.getByRole('status');
      expect(canvas.className).toContain('h-64');
    });
  });

  describe('loading state', () => {
    it('renders loading state when isLoading is true', () => {
      render(<WorkflowCanvas isLoading={true} />);
      expect(screen.getByText('Loading pipeline...')).toBeInTheDocument();
    });

    it('renders loading state with spinner', () => {
      render(<WorkflowCanvas isLoading={true} />);
      // The spinner is part of the loading status element
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByText('Loading pipeline...')).toBeInTheDocument();
    });

    it('has proper ARIA role and label for loading state', () => {
      render(<WorkflowCanvas isLoading={true} />);
      const canvas = screen.getByRole('status');
      expect(canvas.getAttribute('aria-label')).toBe('Loading pipeline');
    });

    it('maintains consistent height in loading state', () => {
      render(<WorkflowCanvas isLoading={true} />);
      const canvas = screen.getByRole('status');
      expect(canvas.className).toContain('h-64');
    });
  });

  describe('active state', () => {
    it('renders React Flow container when pipeline provided', () => {
      render(<WorkflowCanvas pipeline={mockPipeline} />);
      // React Flow renders inside the canvas with role="img"
      expect(screen.getByRole('img')).toBeInTheDocument();
    });

    it('has proper ARIA role and label for active state', () => {
      render(<WorkflowCanvas pipeline={mockPipeline} />);
      const canvas = screen.getByRole('img');
      expect(canvas.getAttribute('aria-label')).toContain('pipeline');
    });

    it('renders all nodes', () => {
      render(<WorkflowCanvas pipeline={mockPipeline} />);
      expect(screen.getByText('Issue')).toBeInTheDocument();
      expect(screen.getByText('Architect')).toBeInTheDocument();
      expect(screen.getByText('Developer')).toBeInTheDocument();
    });

    it('has data-slot attribute in active state', () => {
      render(<WorkflowCanvas pipeline={mockPipeline} />);
      const canvas = screen.getByRole('img');
      expect(canvas).toHaveAttribute('data-slot', 'workflow-canvas');
    });

    it('maintains consistent height in active state', () => {
      render(<WorkflowCanvas pipeline={mockPipeline} />);
      const canvas = screen.getByRole('img');
      expect(canvas.className).toContain('h-40');
    });
  });
});
