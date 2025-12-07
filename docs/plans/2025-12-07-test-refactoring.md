# Test File Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor three dashboard test files to remove library behavior testing, add parametrization, and focus on meaningful component logic.

**Architecture:** Delete tests that verify shadcn/Radix UI library internals. Replace repetitive test cases with `test.each()` parametrization. Add edge case coverage for actual component logic. Keep only tests that would catch real bugs in component behavior.

**Tech Stack:** Vitest, React Testing Library, TypeScript

---

## Summary of Changes

| File | Before | After | Reduction |
|------|--------|-------|-----------|
| DashboardSidebar.test.tsx | 6 tests, 54 lines | 2 tests, ~25 lines | 54% |
| WorkflowEmptyState.test.tsx | 8 tests, 60 lines | 3 tests, ~45 lines | 25% |
| WorkflowProgress.test.tsx | 6 tests, 39 lines | 3 tests, ~40 lines | ~0% (but higher value) |

---

## Task 1: Refactor DashboardSidebar.test.tsx

**Files:**
- Modify: `dashboard/src/components/DashboardSidebar.test.tsx`

**Context:** This component is purely presentational with no state or props. Current tests verify library behavior (data-slot attributes, Radix Collapsible state). We need only verify the navigation structure renders.

### Step 1: Replace entire test file with parametrized version

Replace the contents of `dashboard/src/components/DashboardSidebar.test.tsx` with:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardSidebar } from './DashboardSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';

const renderSidebar = () => {
  return render(
    <SidebarProvider>
      <DashboardSidebar />
    </SidebarProvider>
  );
};

describe('DashboardSidebar', () => {
  it.each([
    'Workflows',
    'Active',
    'Completed',
    'Failed',
    'Activity',
    'Settings',
  ])('renders %s menu item', (menuItem) => {
    renderSidebar();
    expect(screen.getByText(menuItem)).toBeInTheDocument();
  });

  it('renders branding and version info', () => {
    renderSidebar();
    expect(screen.getByText('AMELIA')).toBeInTheDocument();
    expect(screen.getByText(/Amelia/)).toBeInTheDocument();
  });
});
```

### Step 2: Run tests to verify refactored tests pass

Run: `cd /Users/ka/github/amelia-langgraph-bridge/dashboard && pnpm test DashboardSidebar`

Expected: All tests PASS

### Step 3: Commit

```bash
git add dashboard/src/components/DashboardSidebar.test.tsx
git commit -m "refactor(tests): simplify DashboardSidebar tests with parametrization

- Remove tests for library behavior (data-slot, Radix state)
- Parametrize menu item assertions with test.each
- Reduce from 6 tests to 2 (6 menu items + branding)"
```

---

## Task 2: Refactor WorkflowEmptyState.test.tsx

**Files:**
- Modify: `dashboard/src/components/WorkflowEmptyState.test.tsx`

**Context:** Current tests verify "an SVG renders" and individual variants separately. We need to parametrize variant testing and add a negative test for the action button.

### Step 1: Replace entire test file with parametrized version

Replace the contents of `dashboard/src/components/WorkflowEmptyState.test.tsx` with:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkflowEmptyState } from './WorkflowEmptyState';

describe('WorkflowEmptyState', () => {
  describe('variant configurations', () => {
    it.each([
      {
        variant: 'no-workflows' as const,
        expectedTitle: 'No Active Workflows',
        expectedDescription: /Start a new workflow/,
      },
      {
        variant: 'no-activity' as const,
        expectedTitle: 'No Activity Yet',
        expectedDescription: /Activity will appear here/,
      },
      {
        variant: 'no-results' as const,
        expectedTitle: 'No Results Found',
        expectedDescription: /Try adjusting your search/,
      },
      {
        variant: 'error' as const,
        expectedTitle: 'Something Went Wrong',
        expectedDescription: /An error occurred/,
      },
    ])(
      '$variant renders correct title and description',
      ({ variant, expectedTitle, expectedDescription }) => {
        render(<WorkflowEmptyState variant={variant} />);

        expect(screen.getByText(expectedTitle)).toBeInTheDocument();
        expect(screen.getByText(expectedDescription)).toBeInTheDocument();
      }
    );
  });

  describe('custom overrides', () => {
    it('allows custom title and description to override variant defaults', () => {
      render(
        <WorkflowEmptyState
          variant="no-workflows"
          title="Custom Title"
          description="Custom description text"
        />
      );

      expect(screen.getByText('Custom Title')).toBeInTheDocument();
      expect(screen.getByText('Custom description text')).toBeInTheDocument();
      expect(screen.queryByText('No Active Workflows')).not.toBeInTheDocument();
    });
  });

  describe('action button', () => {
    it('renders and triggers action when provided', async () => {
      const user = userEvent.setup();
      const onAction = vi.fn();

      render(
        <WorkflowEmptyState
          variant="no-workflows"
          action={{ label: 'New Workflow', onClick: onAction }}
        />
      );

      const button = screen.getByRole('button', { name: 'New Workflow' });
      await user.click(button);
      expect(onAction).toHaveBeenCalledTimes(1);
    });

    it('does not render button when action is not provided', () => {
      render(<WorkflowEmptyState variant="no-workflows" />);

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });
  });
});
```

### Step 2: Run tests to verify refactored tests pass

Run: `cd /Users/ka/github/amelia-langgraph-bridge/dashboard && pnpm test WorkflowEmptyState`

Expected: All tests PASS

### Step 3: Commit

```bash
git add dashboard/src/components/WorkflowEmptyState.test.tsx
git commit -m "refactor(tests): parametrize WorkflowEmptyState variant tests

- Remove tests for library behavior (data-slot, SVG rendering)
- Parametrize variant assertions with test.each
- Add negative test: button not rendered when action missing
- Use userEvent instead of fireEvent for click"
```

---

## Task 3: Refactor WorkflowProgress.test.tsx

**Files:**
- Modify: `dashboard/src/components/WorkflowProgress.test.tsx`

**Context:** Current tests verify Radix translateX calculations and ARIA prop passthrough. We need to test the component's actual logic: percentage calculation, rounding, division-by-zero protection, and completion state.

### Step 1: Replace entire test file with comprehensive version

Replace the contents of `dashboard/src/components/WorkflowProgress.test.tsx` with:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkflowProgress } from './WorkflowProgress';

describe('WorkflowProgress', () => {
  describe('percentage calculation', () => {
    it.each([
      { completed: 0, total: 5, expectedPct: '0%', expectedStages: '0 of 5 stages' },
      { completed: 1, total: 5, expectedPct: '20%', expectedStages: '1 of 5 stages' },
      { completed: 2, total: 5, expectedPct: '40%', expectedStages: '2 of 5 stages' },
      { completed: 3, total: 4, expectedPct: '75%', expectedStages: '3 of 4 stages' },
      { completed: 5, total: 5, expectedPct: '100%', expectedStages: '5 of 5 stages' },
      { completed: 1, total: 3, expectedPct: '33%', expectedStages: '1 of 3 stages' },
      { completed: 2, total: 3, expectedPct: '67%', expectedStages: '2 of 3 stages' },
    ])(
      '$completed/$total = $expectedPct',
      ({ completed, total, expectedPct, expectedStages }) => {
        render(<WorkflowProgress completed={completed} total={total} />);

        expect(screen.getByText(expectedPct)).toBeInTheDocument();
        expect(screen.getByText(expectedStages)).toBeInTheDocument();
      }
    );

    it('handles division by zero gracefully', () => {
      render(<WorkflowProgress completed={0} total={0} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('0 of 0 stages')).toBeInTheDocument();
    });
  });

  describe('completion state', () => {
    it('marks as incomplete when stages remain', () => {
      const { container } = render(<WorkflowProgress completed={4} total={5} />);

      expect(container.querySelector('[data-complete="true"]')).not.toBeInTheDocument();
    });

    it('marks as complete when all stages done', () => {
      const { container } = render(<WorkflowProgress completed={5} total={5} />);

      expect(container.querySelector('[data-complete="true"]')).toBeInTheDocument();
    });

    it('does not mark 0/0 as complete', () => {
      const { container } = render(<WorkflowProgress completed={0} total={0} />);

      expect(container.querySelector('[data-complete="true"]')).not.toBeInTheDocument();
    });
  });
});
```

### Step 2: Run tests to verify refactored tests pass

Run: `cd /Users/ka/github/amelia-langgraph-bridge/dashboard && pnpm test WorkflowProgress`

Expected: All tests PASS

### Step 3: Commit

```bash
git add dashboard/src/components/WorkflowProgress.test.tsx
git commit -m "refactor(tests): focus WorkflowProgress tests on calculation logic

- Remove tests for library behavior (translateX, ARIA passthrough)
- Parametrize percentage calculation with test.each (7 cases)
- Add edge case: division by zero (total=0)
- Add boundary tests for completion state"
```

---

## Task 4: Run full test suite and verify

### Step 1: Run all dashboard tests

Run: `cd /Users/ka/github/amelia-langgraph-bridge/dashboard && pnpm test`

Expected: All tests PASS

### Step 2: Final commit (if any fixes needed)

Only if tests reveal issues, fix and commit with:

```bash
git commit -m "fix(tests): address issues found in full test run"
```

---

## Deleted Tests Summary

### DashboardSidebar.test.tsx (4 tests removed)
- `renders sidebar with data-slot` - Tests shadcn implementation detail
- `renders collapsible section for workflows` - Tests Radix implementation detail
- `expands collapsible on click` - Tests Radix Collapsible state management
- `renders AMELIA branding in header` - Redundant with menu items test

### WorkflowEmptyState.test.tsx (4 tests removed)
- `renders icon` - Tests that React renders SVG (framework behavior)
- `renders title` - Redundant with parametrized variant test
- `renders description` - Redundant with parametrized variant test
- `uses data-slot for styling hooks` - Tests Empty component implementation detail

### WorkflowProgress.test.tsx (3 tests removed)
- `renders progress bar` - Tests shadcn implementation detail
- `applies correct progress value` - Tests Radix translateX calculation (library)
- `has proper ARIA attributes` - Tests prop passthrough (framework behavior)
