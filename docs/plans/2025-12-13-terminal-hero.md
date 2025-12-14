# Plan: Terminal Narrative Hero Component

**Goal**: Replace the standard VitePress features grid with an animated terminal that demonstrates Amelia's workflow authentically, building trust through real CLI behavior.

**Design Decision**: Terminal uses inverted theme (dark on light site, light on dark site) to create visual contrast and draw attention.

---

## Component Architecture

### New File: `docs/site/.vitepress/theme/components/TerminalHero.vue`

A self-contained Vue component that renders an animated terminal session showing Amelia's complete workflow.

#### Props
- None (self-contained animation)

#### State
- `visibleLines: number` - Controls progressive line reveal
- `currentPhase: 'command' | 'fetch' | 'plan' | 'approval' | 'execute' | 'review' | 'done'` - Animation phase
- `isTyping: boolean` - Whether command is being typed

#### Animation Sequence

| Phase | Duration | Content |
|-------|----------|---------|
| 1. Command typing | 1.5s | `$ amelia start 127 --profile work` character by character |
| 2. Fetch | 0.8s | Spinner → checkmark, issue title appears |
| 3. Plan | 1.2s | Architect spinner → TaskDAG box draws in |
| 4. Approval gate | 2.0s | "Awaiting approval..." with pulsing cursor (key pause) |
| 5. Approved | 0.5s | Checkmark, "Approved via dashboard" |
| 6. Execute | 1.5s | Developer steps 1/3, 2/3, 3/3 |
| 7. Review | 1.0s | Reviewer validates → approved |
| 8. Complete | 1.5s | Final message, hold |
| 9. Reset | 0.5s | Fade out, restart from phase 1 |

**Total cycle**: ~10.5 seconds

#### Visual Elements

```
┌─────────────────────────────────────────────────────────────────┐
│ ● ● ●  amelia                                                   │  ← Window chrome
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  $ amelia start 127 --profile work                              │
│                                                                 │
│  ◐ Fetching issue from GitHub...                                │
│  ✓ Issue #127: Add rate limiting to API                         │
│                                                                 │
│  ◐ Architect analyzing scope...                                 │
│  ✓ Plan ready (3 tasks)                                         │
│                                                                 │
│    ┌─ TaskDAG ─────────────────────────┐                        │
│    │ 1. Add rate limiter middleware    │                        │
│    │ 2. Apply to /api/* routes         │                        │
│    │ 3. Add configuration to env       │                        │
│    └───────────────────────────────────┘                        │
│                                                                 │
│  ◐ Awaiting human approval...                                   │
│  ✓ Approved via dashboard                                       │
│                                                                 │
│  ◐ Developer executing 1/3...                                   │
│  ◐ Developer executing 2/3...                                   │
│  ◐ Developer executing 3/3...                                   │
│  ✓ All tasks complete                                           │
│                                                                 │
│  ◐ Reviewer validating changes...                               │
│  ✓ Changes approved                                             │
│                                                                 │
│    Ready to commit? Open dashboard at localhost:8420            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Theme Inversion Strategy

### CSS Custom Properties

```css
/* Light site → Dark terminal */
:root {
  --terminal-bg: #1a1a1a;
  --terminal-text: #e0e0e0;
  --terminal-text-dim: #888888;
  --terminal-accent: #d4a017;        /* Amelia gold */
  --terminal-success: #4ade80;       /* Green checkmarks */
  --terminal-border: #333333;
  --terminal-chrome: #2d2d2d;
}

/* Dark site → Light terminal */
.dark {
  --terminal-bg: #fafafa;
  --terminal-text: #1a1a1a;
  --terminal-text-dim: #666666;
  --terminal-accent: #b8860b;        /* Darker gold for contrast */
  --terminal-success: #16a34a;       /* Darker green */
  --terminal-border: #e0e0e0;
  --terminal-chrome: #f0f0f0;
}
```

---

## Landing Page Modifications

### File: `docs/site/index.md`

**Remove**: Entire `features:` frontmatter block (lines 19-37)

**Add**: Custom slot usage below the hero

```md
---
layout: home

hero:
  name: "Amelia"
  text: "Agentic Coding Orchestrator"
  tagline: A local AI orchestrator that coordinates specialized agents through a LangGraph state machine.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/usage
    - theme: alt
      text: Architecture
      link: /architecture/overview
---

<TerminalHero />

## Quick Start
...
```

### File: `docs/site/.vitepress/theme/index.ts`

Register TerminalHero as a global component (similar to existing AnimatedWorkflowHero registration).

---

## Accessibility

1. **Reduced motion**: Detect `prefers-reduced-motion` and show static final state instead of animation
2. **Screen reader**: Add `aria-label` describing the workflow, `aria-live="polite"` for phase changes
3. **Contrast**: Ensure all text meets WCAG AA (4.5:1 for normal text, 3:1 for large)

---

## Implementation Order

1. Create `TerminalHero.vue` with static layout (no animation)
2. Add theme inversion CSS variables to `style.css`
3. Implement typing animation for command line
4. Add progressive line reveal with spinners
5. Implement phase transitions with timing
6. Add TaskDAG box drawing animation
7. Implement loop reset with fade
8. Add reduced motion support
9. Register component in theme
10. Update `index.md` to remove features and add component
11. Test both light and dark themes
12. Test reduced motion preference

---

## Open Questions Resolved

| Question | Decision |
|----------|----------|
| Terminal theme | Inverted from site theme |
| Interactivity | None - pure watch animation |
| Features grid | Removed entirely |
| Loop behavior | Infinite with fade reset |
| Approval pause | 2 seconds (longest pause, emphasizes human-in-loop) |

---

## Files Changed

| File | Action |
|------|--------|
| `docs/site/.vitepress/theme/components/TerminalHero.vue` | Create |
| `docs/site/.vitepress/theme/style.css` | Add terminal CSS variables |
| `docs/site/.vitepress/theme/index.ts` | Register component |
| `docs/site/index.md` | Remove features, add TerminalHero |
