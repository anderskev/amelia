---
description: perform comprehensive frontend code review using framework-specific skills and parallel agents
---

# Frontend Code Review

You are performing a comprehensive frontend code review for this branch/PR.

## Skills to Load

Before starting, load the relevant skills for the technologies in use:

- `.claude/skills/amelia/react-flow/SKILL.md` - for @xyflow/react components
- `.claude/skills/amelia/react-router-v7/SKILL.md` - for routing
- `.claude/skills/amelia/shadcn-ui/SKILL.md` - for UI components
- `.claude/skills/amelia/vitest-testing/SKILL.md` - for test quality
- `.claude/skills/amelia/tailwind-v4/SKILL.md` - for styling

## Review Scope

Identify frontend files changed on this branch:

```bash
git diff --name-only $(git merge-base HEAD main)..HEAD | grep -E '\.(tsx?|css)$'
```

## Parallel Review Agents

Launch specialized review agents in parallel using the Task tool with `subagent_type="superpowers:code-reviewer"`:

### 1. React Flow Components Agent

Review files matching: `**/flow/*.tsx`, `**/Workflow*.tsx`, `**/Canvas*.tsx`

Check for:

- NodeProps<T> and EdgeProps<T> typing
- Handle components with correct Position enum
- "nodrag" class on interactive elements
- nodeTypes/edgeTypes memoization
- useUpdateNodeInternals for dynamic handles
- BaseEdge and path utilities usage
- EdgeLabelRenderer for interactive labels

Reference: `/Users/ka/github/xyflow` for canonical patterns

### 2. shadcn/ui Components Agent

Review files matching: `**/ui/*.tsx`, `**/*Badge*.tsx`, `**/*Button*.tsx`

Check for:

- React.ComponentProps typing
- cn() utility usage (className always last)
- data-slot attributes
- CVA patterns with VariantProps
- asChild pattern with Radix Slot
- "use client" directive for Radix wrappers
- Accessibility states (focus-visible, aria-invalid, disabled)

### 3. New Components Agent

Review newly added component files.

Check for:

- Compound component patterns where appropriate
- Proper skeleton/loading state design
- Empty state messaging
- Consistent with existing design system
- Performance (memoization, render optimization)

### 4. Test Quality Agent

Review files matching: `**/*.test.tsx`, `**/*.test.ts`

Check for:

- Testing behavior, not implementation
- Proper async handling (await expect().resolves)
- @testing-library/react query best practices
- vi.clearAllMocks() in beforeEach
- No snapshot overuse
- DRY test code (use .each for parametrized tests)
- Actually testing logic, not mocks

### 5. Routing Agent (if applicable)

Review files with routing: `**/routes/**`, `**/*Router*`, `**/*Layout*`

Check for:

- Loader vs useEffect decisions
- Form vs useFetcher decisions
- Proper error boundaries
- Nested routes with Outlet
- Type-safe params

## Uncertainty Resolution

If uncertain about library patterns, consult:

- `/Users/ka/github/xyflow` - React Flow source and examples
- `/Users/ka/github/react-router` - React Router source and examples

## Output Format

Output MUST be structured as numbered items for use with `/amelia/eval-feedback`.

```
## Review Summary

[1-2 sentence overview]

## Issues

### Critical (Blocking)

1. [FILE:LINE] ISSUE_TITLE
   - Issue: Description of what's wrong
   - Why: Why this matters (bug, a11y, perf, security)
   - Fix: Specific recommended fix

2. [FILE:LINE] ISSUE_TITLE
   - Issue: ...
   - Why: ...
   - Fix: ...

### Major (Should Fix)

3. [FILE:LINE] ISSUE_TITLE
   - Issue: ...
   - Why: ...
   - Fix: ...

### Minor (Nice to Have)

N. [FILE:LINE] ISSUE_TITLE
   - Issue: ...
   - Why: ...
   - Fix: ...

## Good Patterns

- [FILE:LINE] Pattern description (preserve this)

## Verdict

Ready: Yes | No | With fixes 1-N
Rationale: [1-2 sentences]
```

## Example Output

```
## Review Summary

Found 3 critical a11y issues and 2 major React Flow pattern violations.

## Issues

### Critical (Blocking)

1. [ui/tooltip.tsx:1] Missing "use client" directive
   - Issue: Radix wrapper component lacks client directive
   - Why: Will cause RSC errors when imported in server components
   - Fix: Add "use client" as first line

2. [flow/WorkflowEdge.tsx:71] Edge label missing nodrag nopan
   - Issue: Interactive label has pointerEvents but no drag prevention
   - Why: Users dragging label will pan canvas unexpectedly
   - Fix: Add className="nodrag nopan" to the label div

### Major (Should Fix)

3. [ui/badge.tsx:14-20] Status variants in base component
   - Issue: Domain-specific variants pollute reusable primitive
   - Why: Violates separation of concerns, less reusable
   - Fix: Move status variants to StatusBadge, keep base generic

## Good Patterns

- [flow/WorkflowNode.tsx:17-42] Clean statusStyles object separation
- [WorkflowCanvas.tsx:40-46] nodeTypes defined outside component

## Verdict

Ready: With fixes 1-2
Rationale: Critical a11y issues must be fixed. Major issues can follow.
```

## Critical Rules

**DO:**

- Number every issue sequentially (1, 2, 3...)
- Include FILE:LINE for each issue
- Separate Issue/Why/Fix clearly
- Categorize by actual severity
- Give clear verdict with issue numbers

**DON'T:**

- Use tables (harder to parse)
- Skip numbering
- Give vague file references
- Mark style issues as Critical
- Approve without thorough review
