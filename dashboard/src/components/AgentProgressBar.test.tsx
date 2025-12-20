import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentProgressBar } from './AgentProgressBar';

describe('AgentProgressBar', () => {
  describe('stage rendering', () => {
    it('renders all agent stages', () => {
      render(
        <AgentProgressBar
          currentStage="architect"
          completedStages={['pm']}
        />
      );

      expect(screen.getByText('PM')).toBeInTheDocument();
      expect(screen.getByText('Architect')).toBeInTheDocument();
      expect(screen.getByText('Developer')).toBeInTheDocument();
      expect(screen.getByText('Reviewer')).toBeInTheDocument();
    });

    it('renders stages in correct order', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      const stages = screen.getAllByRole('listitem');
      expect(stages).toHaveLength(4);
      expect(stages[0]).toHaveTextContent('PM');
      expect(stages[1]).toHaveTextContent('Architect');
      expect(stages[2]).toHaveTextContent('Developer');
      expect(stages[3]).toHaveTextContent('Reviewer');
    });
  });

  describe('current stage highlighting', () => {
    it('highlights current stage with primary styling', () => {
      render(
        <AgentProgressBar
          currentStage="architect"
          completedStages={['pm']}
        />
      );

      const architectStage = screen.getByText('Architect').closest('[data-slot="stage-item"]');
      expect(architectStage).toHaveAttribute('data-current', 'true');
    });

    it('does not highlight other stages as current', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      const pmStage = screen.getByText('PM').closest('[data-slot="stage-item"]');
      const architectStage = screen.getByText('Architect').closest('[data-slot="stage-item"]');
      const reviewerStage = screen.getByText('Reviewer').closest('[data-slot="stage-item"]');

      expect(pmStage).not.toHaveAttribute('data-current', 'true');
      expect(architectStage).not.toHaveAttribute('data-current', 'true');
      expect(reviewerStage).not.toHaveAttribute('data-current', 'true');
    });

    it('handles null currentStage gracefully', () => {
      render(
        <AgentProgressBar
          currentStage={null}
          completedStages={['pm', 'architect']}
        />
      );

      const stages = screen.getAllByRole('listitem');
      stages.forEach((stage) => {
        expect(stage.querySelector('[data-slot="stage-item"]')).not.toHaveAttribute('data-current', 'true');
      });
    });
  });

  describe('completed stages', () => {
    it('shows checkmark icon for completed stages', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      const pmStage = screen.getByText('PM').closest('[data-slot="stage-item"]');
      const architectStage = screen.getByText('Architect').closest('[data-slot="stage-item"]');

      expect(pmStage).toHaveAttribute('data-completed', 'true');
      expect(architectStage).toHaveAttribute('data-completed', 'true');
    });

    it('does not show checkmark for incomplete stages', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      const developerStage = screen.getByText('Developer').closest('[data-slot="stage-item"]');
      const reviewerStage = screen.getByText('Reviewer').closest('[data-slot="stage-item"]');

      expect(developerStage).not.toHaveAttribute('data-completed', 'true');
      expect(reviewerStage).not.toHaveAttribute('data-completed', 'true');
    });

    it('marks all stages as completed when all are done', () => {
      render(
        <AgentProgressBar
          currentStage={null}
          completedStages={['pm', 'architect', 'developer', 'reviewer']}
        />
      );

      const stages = screen.getAllByRole('listitem');
      stages.forEach((stage) => {
        expect(stage.querySelector('[data-slot="stage-item"]')).toHaveAttribute('data-completed', 'true');
      });
    });

    it('handles empty completedStages array', () => {
      render(
        <AgentProgressBar
          currentStage="pm"
          completedStages={[]}
        />
      );

      const stages = screen.getAllByRole('listitem');
      stages.forEach((stage) => {
        expect(stage.querySelector('[data-slot="stage-item"]')).not.toHaveAttribute('data-completed', 'true');
      });
    });
  });

  describe('stage states', () => {
    it('prioritizes current over completed when both apply', () => {
      // Edge case: caller passes currentStage that is also in completedStages
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect', 'developer']}
        />
      );

      const developerStage = screen.getByText('Developer').closest('[data-slot="stage-item"]');

      // Should be current, NOT completed (mutual exclusivity)
      expect(developerStage).toHaveAttribute('data-current', 'true');
      expect(developerStage).not.toHaveAttribute('data-completed', 'true');
      expect(developerStage).not.toHaveAttribute('data-pending', 'true');
    });

    it('marks pending stages correctly', () => {
      render(
        <AgentProgressBar
          currentStage="architect"
          completedStages={['pm']}
        />
      );

      const developerStage = screen.getByText('Developer').closest('[data-slot="stage-item"]');
      const reviewerStage = screen.getByText('Reviewer').closest('[data-slot="stage-item"]');

      expect(developerStage).toHaveAttribute('data-pending', 'true');
      expect(reviewerStage).toHaveAttribute('data-pending', 'true');
    });

    it('correctly differentiates completed, current, and pending stages', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      const pmStage = screen.getByText('PM').closest('[data-slot="stage-item"]');
      const architectStage = screen.getByText('Architect').closest('[data-slot="stage-item"]');
      const developerStage = screen.getByText('Developer').closest('[data-slot="stage-item"]');
      const reviewerStage = screen.getByText('Reviewer').closest('[data-slot="stage-item"]');

      // Completed stages
      expect(pmStage).toHaveAttribute('data-completed', 'true');
      expect(architectStage).toHaveAttribute('data-completed', 'true');

      // Current stage
      expect(developerStage).toHaveAttribute('data-current', 'true');

      // Pending stage
      expect(reviewerStage).toHaveAttribute('data-pending', 'true');
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA role and label', () => {
      render(
        <AgentProgressBar
          currentStage="architect"
          completedStages={['pm']}
        />
      );

      const progressBar = screen.getByRole('navigation');
      expect(progressBar).toHaveAttribute('aria-label', 'Agent workflow progress');
    });

    it('uses semantic list structure', () => {
      render(
        <AgentProgressBar
          currentStage="developer"
          completedStages={['pm', 'architect']}
        />
      );

      expect(screen.getByRole('list')).toBeInTheDocument();
      expect(screen.getAllByRole('listitem')).toHaveLength(4);
    });
  });

  describe('custom className', () => {
    it('applies custom className to wrapper', () => {
      const { container } = render(
        <AgentProgressBar
          currentStage="architect"
          completedStages={['pm']}
          className="custom-class"
        />
      );

      const wrapper = container.querySelector('[data-slot="agent-progress-bar"]');
      expect(wrapper).toHaveClass('custom-class');
    });
  });
});
