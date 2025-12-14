# Animated Workflow Hero Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the generic VitePress hero section with a distinctive animated visualization showing Amelia's Architect → Developer → Reviewer agent workflow loop.

**Architecture:** Create a custom Vue component `AnimatedWorkflowHero.vue` that renders an SVG-based workflow diagram with CSS animations. Inject it into VitePress's `home-hero-image` slot to replace the default empty hero image area. The animation shows agents as nodes with connecting arrows, with a pulsing "active" state that cycles through the workflow.

**Tech Stack:** Vue 3 Composition API, SVG, CSS animations, VitePress layout slots

---

## Task 1: Create the AnimatedWorkflowHero Vue Component

**Files:**
- Create: `docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue`

**Step 1: Create the component file with basic structure**

Create the file with the following content:

```vue
<!--
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// Agent workflow states: architect -> developer -> reviewer -> (loop back to developer or done)
type AgentState = 'architect' | 'developer' | 'reviewer' | 'approved'

const currentAgent = ref<AgentState>('architect')
const cycleCount = ref(0)
let animationInterval: ReturnType<typeof setInterval> | null = null

const agents = [
  { id: 'architect', label: 'Architect', sublabel: 'plans' },
  { id: 'developer', label: 'Developer', sublabel: 'executes' },
  { id: 'reviewer', label: 'Reviewer', sublabel: 'validates' }
] as const

onMounted(() => {
  // Cycle through agents every 2 seconds
  animationInterval = setInterval(() => {
    switch (currentAgent.value) {
      case 'architect':
        currentAgent.value = 'developer'
        break
      case 'developer':
        currentAgent.value = 'reviewer'
        break
      case 'reviewer':
        // After 2 review cycles, show "approved" briefly then restart
        if (cycleCount.value >= 1) {
          currentAgent.value = 'approved'
          cycleCount.value = 0
          // Reset to architect after showing approved
          setTimeout(() => {
            currentAgent.value = 'architect'
          }, 1500)
        } else {
          // Loop back to developer (simulating revision)
          currentAgent.value = 'developer'
          cycleCount.value++
        }
        break
      case 'approved':
        currentAgent.value = 'architect'
        break
    }
  }, 2000)
})

onUnmounted(() => {
  if (animationInterval) {
    clearInterval(animationInterval)
  }
})

const isActive = (agentId: string) => currentAgent.value === agentId
const isApproved = () => currentAgent.value === 'approved'
</script>

<template>
  <div class="workflow-hero">
    <svg
      viewBox="0 0 400 320"
      class="workflow-diagram"
      aria-label="Amelia agent workflow: Architect plans, Developer executes, Reviewer validates"
    >
      <defs>
        <!-- Gradient for active state glow -->
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>

        <!-- Arrow marker -->
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill="var(--vp-c-text-3)"
          />
        </marker>

        <marker
          id="arrowhead-active"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill="var(--vp-c-brand-1)"
          />
        </marker>
      </defs>

      <!-- Architect Node -->
      <g class="agent-node" :class="{ active: isActive('architect') }">
        <rect
          x="140"
          y="20"
          width="120"
          height="70"
          rx="8"
          class="node-bg"
          :filter="isActive('architect') ? 'url(#glow)' : ''"
        />
        <text x="200" y="50" class="node-label">Architect</text>
        <text x="200" y="70" class="node-sublabel">plans</text>
      </g>

      <!-- Arrow: Architect -> Developer -->
      <path
        d="M 200 90 L 200 125"
        class="connector"
        :class="{ active: isActive('developer') }"
        marker-end="url(#arrowhead)"
      />

      <!-- Developer Node -->
      <g class="agent-node" :class="{ active: isActive('developer') }">
        <rect
          x="140"
          y="130"
          width="120"
          height="70"
          rx="8"
          class="node-bg"
          :filter="isActive('developer') ? 'url(#glow)' : ''"
        />
        <text x="200" y="160" class="node-label">Developer</text>
        <text x="200" y="180" class="node-sublabel">executes</text>
      </g>

      <!-- Arrow: Developer -> Reviewer -->
      <path
        d="M 200 200 L 200 235"
        class="connector"
        :class="{ active: isActive('reviewer') }"
        marker-end="url(#arrowhead)"
      />

      <!-- Reviewer Node -->
      <g class="agent-node" :class="{ active: isActive('reviewer') || isApproved() }">
        <rect
          x="140"
          y="240"
          width="120"
          height="70"
          rx="8"
          class="node-bg"
          :class="{ approved: isApproved() }"
          :filter="isActive('reviewer') || isApproved() ? 'url(#glow)' : ''"
        />
        <text x="200" y="270" class="node-label">Reviewer</text>
        <text x="200" y="290" class="node-sublabel">
          {{ isApproved() ? '✓ approved' : 'validates' }}
        </text>
      </g>

      <!-- Loop arrow: Reviewer -> Developer (revision loop) -->
      <path
        d="M 260 275 Q 320 275 320 165 Q 320 130 260 165"
        class="connector loop-connector"
        :class="{ active: cycleCount > 0 && isActive('developer') }"
        fill="none"
        marker-end="url(#arrowhead)"
      />
      <text x="340" y="200" class="loop-label">loop until</text>
      <text x="340" y="218" class="loop-label">approved</text>
    </svg>
  </div>
</template>

<style scoped>
.workflow-hero {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.workflow-diagram {
  width: 100%;
  height: auto;
}

/* Node styling */
.node-bg {
  fill: var(--vp-c-bg-alt);
  stroke: var(--vp-c-divider);
  stroke-width: 2;
  transition: all 0.3s ease;
}

.agent-node.active .node-bg {
  stroke: var(--vp-c-brand-1);
  stroke-width: 3;
}

.node-bg.approved {
  stroke: var(--vp-c-tip-1);
  fill: var(--vp-c-tip-soft);
}

.node-label {
  fill: var(--vp-c-text-1);
  font-family: var(--amelia-font-heading);
  font-size: 18px;
  font-weight: 600;
  text-anchor: middle;
}

.node-sublabel {
  fill: var(--vp-c-text-2);
  font-family: var(--vp-font-family-base);
  font-size: 14px;
  text-anchor: middle;
}

.agent-node.active .node-label {
  fill: var(--vp-c-brand-1);
}

/* Connector styling */
.connector {
  stroke: var(--vp-c-text-3);
  stroke-width: 2;
  fill: none;
  transition: all 0.3s ease;
}

.connector.active {
  stroke: var(--vp-c-brand-1);
  stroke-width: 3;
}

.loop-connector {
  stroke-dasharray: 5, 5;
}

.loop-label {
  fill: var(--vp-c-text-3);
  font-family: var(--vp-font-family-mono);
  font-size: 11px;
  text-anchor: start;
}

/* Pulse animation for active nodes */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.agent-node.active .node-bg {
  animation: pulse 1.5s ease-in-out infinite;
}
</style>
```

**Step 2: Verify the file was created**

Run: `ls -la docs/site/.vitepress/theme/components/`
Expected: See `AnimatedWorkflowHero.vue` in the list

**Step 3: Commit**

```bash
git add docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue
git commit -m "feat(docs): add AnimatedWorkflowHero component skeleton"
```

---

## Task 2: Register the Component in VitePress Theme

**Files:**
- Modify: `docs/site/.vitepress/theme/index.ts`

**Step 1: Import the new component**

Add the import statement after line 23 (after `ColorComparison` import):

```typescript
import AnimatedWorkflowHero from './components/AnimatedWorkflowHero.vue'
```

**Step 2: Register the component globally**

Add to the `enhanceApp` function after line 37:

```typescript
app.component('AnimatedWorkflowHero', AnimatedWorkflowHero)
```

**Step 3: Inject into the home-hero-image slot**

Replace the `Layout` function (lines 26-31) with:

```typescript
Layout: () => {
  return h(DefaultTheme.Layout, null, {
    // Inject animated workflow diagram into the hero image slot
    'home-hero-image': () => h(AnimatedWorkflowHero)
  })
},
```

**Step 4: Verify TypeScript compiles**

Run: `cd docs/site && pnpm type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add docs/site/.vitepress/theme/index.ts
git commit -m "feat(docs): register AnimatedWorkflowHero in VitePress theme"
```

---

## Task 3: Update Hero CSS for Better Layout

**Files:**
- Modify: `docs/site/.vitepress/theme/style.css`

**Step 1: Add hero layout adjustments**

Add the following CSS after line 200 (after the existing `--vp-home-hero-image-filter` definition):

```css
/**
 * Component: Home Hero Layout Adjustments
 * Make space for the animated workflow diagram
 * -------------------------------------------------------------------------- */

/* Adjust hero container for side-by-side layout on larger screens */
@media (min-width: 960px) {
  .VPHero .container {
    display: flex;
    align-items: center;
    gap: 2rem;
  }

  .VPHero .main {
    flex: 1;
    max-width: 600px;
  }

  .VPHero .image {
    flex: 0 0 400px;
  }
}

/* Ensure the animated diagram scales nicely */
.VPHero .image-container {
  max-width: 400px;
  margin: 0 auto;
}

/* Add subtle gradient background to hero area */
.VPHome .VPHero {
  background: radial-gradient(
    ellipse at 70% 30%,
    var(--vp-c-brand-soft) 0%,
    transparent 50%
  );
}

.dark .VPHome .VPHero {
  background: radial-gradient(
    ellipse at 70% 30%,
    rgba(255, 200, 87, 0.03) 0%,
    transparent 50%
  );
}
```

**Step 2: Verify CSS is valid**

Run: `cd docs/site && pnpm build`
Expected: Build succeeds without CSS errors

**Step 3: Commit**

```bash
git add docs/site/.vitepress/theme/style.css
git commit -m "style(docs): add hero layout adjustments for workflow diagram"
```

---

## Task 4: Test the Component Locally

**Files:**
- None (testing only)

**Step 1: Start the dev server**

Run: `cd docs/site && pnpm dev`
Expected: Server starts at localhost:5173

**Step 2: Open the home page in browser**

Navigate to: `http://localhost:5173/amelia/`

**Step 3: Verify the animation works**

Expected behavior:
1. See the workflow diagram in the hero section (right side on desktop, below on mobile)
2. The "Architect" node pulses gold/active first
3. After 2 seconds, "Developer" becomes active
4. After 2 seconds, "Reviewer" becomes active
5. The loop repeats, with occasional "✓ approved" state

**Step 4: Test dark/light mode toggle**

Click the theme toggle in the nav
Expected: Colors adapt to the theme (gold in dark mode, blue in light mode)

**Step 5: Test responsive behavior**

Resize browser to mobile width (~375px)
Expected: Diagram stacks below the hero text, scales appropriately

---

## Task 5: Add Animation Refinements

**Files:**
- Modify: `docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue`

**Step 1: Add entrance animation**

Add to the `<style scoped>` section:

```css
/* Entrance animation */
@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.workflow-hero {
  animation: fadeSlideIn 0.6s ease-out;
}

/* Stagger node entrance */
.agent-node:nth-child(1) { animation-delay: 0.1s; }
.agent-node:nth-child(2) { animation-delay: 0.2s; }
.agent-node:nth-child(3) { animation-delay: 0.3s; }
```

**Step 2: Add connection line animation**

Add to the `<style scoped>` section:

```css
/* Animated flow along connectors */
@keyframes flowPulse {
  0% {
    stroke-dashoffset: 20;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

.connector.active {
  stroke-dasharray: 10, 10;
  animation: flowPulse 0.5s linear infinite;
}
```

**Step 3: Verify animations in browser**

Refresh the page
Expected: Smooth entrance animation, flowing connector lines when active

**Step 4: Commit**

```bash
git add docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue
git commit -m "style(docs): add entrance and flow animations to workflow hero"
```

---

## Task 6: Add Accessibility Attributes

**Files:**
- Modify: `docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue`

**Step 1: Add reduced motion support**

Add to the `<style scoped>` section:

```css
/* Respect user's reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .workflow-hero,
  .agent-node,
  .connector,
  .node-bg {
    animation: none !important;
    transition: none !important;
  }
}
```

**Step 2: Add ARIA live region for state changes**

Add after the SVG element in the template:

```vue
<!-- Screen reader announcement -->
<span class="sr-only" role="status" aria-live="polite">
  {{ isApproved() ? 'Workflow complete: changes approved' : `Current step: ${currentAgent}` }}
</span>
```

**Step 3: Add sr-only utility class**

Add to the `<style scoped>` section:

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Step 4: Commit**

```bash
git add docs/site/.vitepress/theme/components/AnimatedWorkflowHero.vue
git commit -m "a11y(docs): add reduced motion and screen reader support to workflow hero"
```

---

## Task 7: Final Testing and Build Verification

**Files:**
- None (testing only)

**Step 1: Run the production build**

Run: `cd docs/site && pnpm build`
Expected: Build completes successfully

**Step 2: Preview the production build**

Run: `cd docs/site && pnpm preview`
Expected: Preview server starts

**Step 3: Test in production mode**

Navigate to: `http://localhost:4173/amelia/`
Expected: Animation works identically to dev mode

**Step 4: Verify no console errors**

Open browser DevTools console
Expected: No JavaScript errors or warnings

**Step 5: Final commit (if any cleanup needed)**

```bash
git add -A
git commit -m "chore(docs): finalize animated workflow hero implementation"
```

---

## Summary

After completing all tasks, the landing page will have:

1. **Distinctive visual hero** - An animated SVG workflow diagram that immediately communicates what Amelia does
2. **Smooth animations** - CSS-only animations for the workflow cycle with entrance effects
3. **Theme-aware styling** - Adapts to dark/light mode using existing design tokens
4. **Accessible design** - Respects reduced motion, includes screen reader announcements
5. **Responsive layout** - Stacks appropriately on mobile devices

The implementation uses:
- VitePress's `home-hero-image` slot (no custom layout override needed)
- CSS animations (no JavaScript animation libraries)
- Existing design system variables for consistency
