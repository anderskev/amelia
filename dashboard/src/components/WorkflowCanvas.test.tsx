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

  it('renders React Flow container', () => {
    const { container } = render(<WorkflowCanvas pipeline={mockPipeline} />);
    expect(container.querySelector('.react-flow')).toBeInTheDocument();
  });

  it('has proper ARIA role and label', () => {
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

  it('renders stage progress info', () => {
    render(<WorkflowCanvas pipeline={mockPipeline} />);
    expect(screen.getByText(/2.*\/.*3/)).toBeInTheDocument(); // "2/3 stages" or similar
  });

  it('has data-slot attribute', () => {
    const { container } = render(<WorkflowCanvas pipeline={mockPipeline} />);
    expect(container.querySelector('[data-slot="workflow-canvas"]')).toBeInTheDocument();
  });
});
