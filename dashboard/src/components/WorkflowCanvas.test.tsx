import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowCanvas } from './WorkflowCanvas';
import type { EventDrivenPipeline } from '../utils/pipeline';

// Create mock functions we can spy on - use vi.hoisted for proper hoisting
const { mockFitView, mockNodesInitialized } = vi.hoisted(() => ({
  mockFitView: vi.fn(),
  mockNodesInitialized: { value: false },
}));

// Mock ai-elements Canvas - it wraps ReactFlow
vi.mock('./ai-elements/canvas', () => ({
  Canvas: ({ children, nodes }: { children: React.ReactNode; nodes: unknown[] }) => (
    <div data-testid="react-flow" data-node-count={nodes.length}>
      {children}
    </div>
  ),
}));

// Mock React Flow hooks for FitViewOnChange component
vi.mock('@xyflow/react', () => ({
  useReactFlow: () => ({
    fitView: mockFitView,
  }),
  useNodesInitialized: () => mockNodesInitialized.value,
}));

describe('WorkflowCanvas', () => {
  const emptyPipeline: EventDrivenPipeline = { nodes: [], edges: [] };

  beforeEach(() => {
    mockFitView.mockClear();
    mockNodesInitialized.value = false;
  });

  it('renders empty state when pipeline has no nodes', () => {
    render(<WorkflowCanvas pipeline={emptyPipeline} />);
    expect(screen.getByText(/no pipeline data/i)).toBeInTheDocument();
  });

  it('renders pipeline nodes', () => {
    const pipeline: EventDrivenPipeline = {
      nodes: [
        {
          id: 'architect',
          type: 'agent',
          position: { x: 0, y: 0 },
          data: { agentType: 'architect', status: 'completed', iterations: [], isExpanded: false },
        },
        {
          id: 'developer',
          type: 'agent',
          position: { x: 200, y: 0 },
          data: { agentType: 'developer', status: 'active', iterations: [], isExpanded: false },
        },
      ],
      edges: [{ id: 'e1', source: 'architect', target: 'developer', data: { status: 'completed' } }],
    };

    render(<WorkflowCanvas pipeline={pipeline} />);

    const flow = screen.getByTestId('react-flow');
    expect(flow).toHaveAttribute('data-node-count', '2');
  });

  it('applies layout to nodes', () => {
    const pipeline: EventDrivenPipeline = {
      nodes: [
        {
          id: 'architect',
          type: 'agent',
          position: { x: 0, y: 0 },
          data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
        },
      ],
      edges: [],
    };

    render(<WorkflowCanvas pipeline={pipeline} />);
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<WorkflowCanvas pipeline={emptyPipeline} />);
    expect(screen.getByRole('region', { name: /workflow pipeline/i })).toBeInTheDocument();
  });

  it('re-renders with new node count when pipeline changes', () => {
    const initialPipeline: EventDrivenPipeline = {
      nodes: [
        {
          id: 'architect',
          type: 'agent',
          position: { x: 0, y: 0 },
          data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
        },
      ],
      edges: [],
    };

    const { rerender } = render(<WorkflowCanvas pipeline={initialPipeline} />);
    expect(screen.getByTestId('react-flow')).toHaveAttribute('data-node-count', '1');

    // Update pipeline with additional node
    const updatedPipeline: EventDrivenPipeline = {
      nodes: [
        {
          id: 'architect',
          type: 'agent',
          position: { x: 0, y: 0 },
          data: { agentType: 'architect', status: 'completed', iterations: [], isExpanded: false },
        },
        {
          id: 'developer',
          type: 'agent',
          position: { x: 200, y: 0 },
          data: { agentType: 'developer', status: 'active', iterations: [], isExpanded: false },
        },
      ],
      edges: [{ id: 'e1', source: 'architect', target: 'developer', data: { status: 'completed' } }],
    };

    rerender(<WorkflowCanvas pipeline={updatedPipeline} />);

    // Controlled state: component should immediately reflect the new props
    expect(screen.getByTestId('react-flow')).toHaveAttribute('data-node-count', '2');
  });

  describe('FitViewOnNodeCountChange', () => {
    it('does not call fitView on initial render (handled by Canvas fitView prop)', () => {
      const pipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
          },
        ],
        edges: [],
      };

      // Nodes are initialized
      mockNodesInitialized.value = true;
      render(<WorkflowCanvas pipeline={pipeline} />);

      // Our component should NOT call fitView on initial render
      // (the Canvas's built-in fitView prop handles that)
      expect(mockFitView).not.toHaveBeenCalled();
    });

    it('calls fitView when new nodes are added', () => {
      const initialPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
          },
        ],
        edges: [],
      };

      // Start with nodes initialized
      mockNodesInitialized.value = true;
      const { rerender } = render(<WorkflowCanvas pipeline={initialPipeline} />);

      // Initial render - no fitView call from our component
      expect(mockFitView).not.toHaveBeenCalled();

      // Add new nodes
      const updatedPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'completed', iterations: [], isExpanded: false },
          },
          {
            id: 'developer',
            type: 'agent',
            position: { x: 200, y: 0 },
            data: { agentType: 'developer', status: 'active', iterations: [], isExpanded: false },
          },
        ],
        edges: [{ id: 'e1', source: 'architect', target: 'developer', data: { status: 'completed' } }],
      };
      rerender(<WorkflowCanvas pipeline={updatedPipeline} />);

      // fitView should be called when node count increases
      expect(mockFitView).toHaveBeenCalledWith({ padding: 0.2 });
    });

    it('does not call fitView when only node status changes (same count)', () => {
      const initialPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
          },
        ],
        edges: [],
      };

      // Start with nodes initialized
      mockNodesInitialized.value = true;
      const { rerender } = render(<WorkflowCanvas pipeline={initialPipeline} />);

      // Update status only - same node count
      const updatedPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'completed', iterations: [], isExpanded: false },
          },
        ],
        edges: [],
      };
      rerender(<WorkflowCanvas pipeline={updatedPipeline} />);

      // fitView should NOT be called - node count didn't change
      expect(mockFitView).not.toHaveBeenCalled();
    });

    it('waits for nodes to be initialized before calling fitView', () => {
      const initialPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'pending', iterations: [], isExpanded: false },
          },
        ],
        edges: [],
      };

      // Nodes initialized
      mockNodesInitialized.value = true;
      const { rerender } = render(<WorkflowCanvas pipeline={initialPipeline} />);

      // Add nodes but they're not measured yet
      mockNodesInitialized.value = false;
      const updatedPipeline: EventDrivenPipeline = {
        nodes: [
          {
            id: 'architect',
            type: 'agent',
            position: { x: 0, y: 0 },
            data: { agentType: 'architect', status: 'completed', iterations: [], isExpanded: false },
          },
          {
            id: 'developer',
            type: 'agent',
            position: { x: 200, y: 0 },
            data: { agentType: 'developer', status: 'active', iterations: [], isExpanded: false },
          },
        ],
        edges: [{ id: 'e1', source: 'architect', target: 'developer', data: { status: 'completed' } }],
      };
      rerender(<WorkflowCanvas pipeline={updatedPipeline} />);

      // fitView should NOT be called - nodes not initialized
      expect(mockFitView).not.toHaveBeenCalled();

      // Now nodes are measured
      mockNodesInitialized.value = true;
      rerender(<WorkflowCanvas pipeline={updatedPipeline} />);

      // fitView should be called now
      expect(mockFitView).toHaveBeenCalledWith({ padding: 0.2 });
    });
  });
});
