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
      const { container } = render(<WorkflowCanvas />);
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('has proper ARIA role and label for empty state', () => {
      render(<WorkflowCanvas />);
      const canvas = screen.getByRole('status');
      expect(canvas.getAttribute('aria-label')).toBe('No workflow selected');
    });

    it('has data-slot attribute in empty state', () => {
      const { container } = render(<WorkflowCanvas />);
      expect(container.querySelector('[data-slot="workflow-canvas"]')).toBeInTheDocument();
    });

    it('maintains consistent height in empty state', () => {
      const { container } = render(<WorkflowCanvas />);
      const canvas = container.querySelector('[data-slot="workflow-canvas"]');
      expect(canvas?.className).toContain('h-64');
    });
  });

  describe('loading state', () => {
    it('renders loading state when isLoading is true', () => {
      render(<WorkflowCanvas isLoading={true} />);
      expect(screen.getByText('Loading pipeline...')).toBeInTheDocument();
    });

    it('renders loading state with spinner', () => {
      const { container } = render(<WorkflowCanvas isLoading={true} />);
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('has proper ARIA role and label for loading state', () => {
      render(<WorkflowCanvas isLoading={true} />);
      const canvas = screen.getByRole('status');
      expect(canvas.getAttribute('aria-label')).toBe('Loading pipeline');
    });

    it('maintains consistent height in loading state', () => {
      const { container } = render(<WorkflowCanvas isLoading={true} />);
      const canvas = container.querySelector('[data-slot="workflow-canvas"]');
      expect(canvas?.className).toContain('h-64');
    });
  });

  describe('active state', () => {
    it('renders React Flow container when pipeline provided', () => {
      const { container } = render(<WorkflowCanvas pipeline={mockPipeline} />);
      expect(container.querySelector('.react-flow')).toBeInTheDocument();
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
      const { container } = render(<WorkflowCanvas pipeline={mockPipeline} />);
      expect(container.querySelector('[data-slot="workflow-canvas"]')).toBeInTheDocument();
    });

    it('maintains consistent height in active state', () => {
      const { container } = render(<WorkflowCanvas pipeline={mockPipeline} />);
      const canvas = container.querySelector('[data-slot="workflow-canvas"]');
      expect(canvas?.className).toContain('h-40');
    });
  });
});
