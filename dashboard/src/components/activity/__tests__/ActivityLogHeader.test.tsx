import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ActivityLogHeader } from '../ActivityLogHeader';
import type { StageGroup } from '../types';

const makeGroup = (overrides: Partial<StageGroup> = {}): StageGroup => ({
  stage: 'architect',
  label: 'Planning (Architect)',
  events: [],
  isActive: false,
  isCompleted: false,
  startedAt: null,
  endedAt: null,
  ...overrides,
});

describe('ActivityLogHeader', () => {
  it('renders stage label', () => {
    render(
      <ActivityLogHeader
        group={makeGroup({ label: 'Planning (Architect)' })}
        isCollapsed={false}
        onToggle={() => {}}
      />
    );

    expect(screen.getByText('Planning (Architect)')).toBeInTheDocument();
  });

  it('shows event count', () => {
    render(
      <ActivityLogHeader
        group={makeGroup({ events: [{} as any, {} as any, {} as any] })}
        isCollapsed={false}
        onToggle={() => {}}
      />
    );

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(
      <ActivityLogHeader
        group={makeGroup()}
        isCollapsed={false}
        onToggle={onToggle}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('shows completed indicator when isCompleted', () => {
    render(
      <ActivityLogHeader
        group={makeGroup({ isCompleted: true })}
        isCollapsed={false}
        onToggle={() => {}}
      />
    );

    expect(screen.getByTestId('stage-completed')).toBeInTheDocument();
  });

  it('shows active indicator when isActive', () => {
    render(
      <ActivityLogHeader
        group={makeGroup({ isActive: true })}
        isCollapsed={false}
        onToggle={() => {}}
      />
    );

    expect(screen.getByTestId('stage-active')).toBeInTheDocument();
  });
});
