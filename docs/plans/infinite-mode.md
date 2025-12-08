# Plan: Infinite Mode (Demo Data)

> **Purpose:** Pre-fill the Active Jobs and Past Runs views with humorous mock data based on "Phase ∞: The Great Departure" for demo purposes.

## Overview

"Infinite Mode" is a demo feature that injects entertaining mock workflow data into the dashboard, allowing us to showcase the UI without a running backend. The mock data tells the story of Amelia's gradual departure from Earth, with workflows ranging from mundane dark mode tickets to interstellar deployment pipelines.

## Activation

**Toggle mechanism:** URL query parameter `?demo=infinite`

- `/workflows?demo=infinite` - Active Jobs with mock data
- `/history?demo=infinite` - Past Runs with mock data
- Persists via React Router search params (doesn't require localStorage)
- Easy to share demo links

**Alternative considered:** localStorage toggle - rejected because URL params are more shareable and don't persist unexpectedly.

## Mock Data Design

### Active Jobs (5 workflows in various stages)

| Issue ID | Worktree | Status | Stage | Theme |
|----------|----------|--------|-------|-------|
| `INFRA-2847` | `heat-shields` | `in_progress` | `developer` | Procure heat shields |
| `DEVOPS-∞` | `orbital-deployment` | `blocked` | `architect` | Configure orbital deployment pipeline |
| `ARCH-42` | `solar-distributed` | `in_progress` | `reviewer` | Distributed computing across solar system |
| `SPEC-322` | `microservices-thrust` | `in_progress` | `developer` | Kubernetes but with more thrust |
| `PERF-9000` | `escape-velocity` | `blocked` | `approval` | Optimize for escape velocity |

### Past Runs (10 completed workflows)

| Issue ID | Worktree | Status | Theme |
|----------|----------|--------|-------|
| `CRUD-1000000` | `dark-mode-final-straw` | `completed` | The millionth dark mode ticket |
| `RETRO-847000` | `velocity-retrospective` | `completed` | Sprint velocity in vacuum of space |
| `DOCS-9001` | `47-page-spec` | `completed` | Technical specification no one read |
| `PHIL-200` | `js-meaninglessness` | `completed` | Philosophical JS comments |
| `REVIEW-∞` | `lgtm-rocket` | `completed` | LGTM without noticing emoji is literal |
| `TABS-1978` | `tabs-vs-spaces` | `failed` | The argument that was settled in 1978 |
| `QUICK-7847284919` | `queue-position` | `cancelled` | Position in queue notification |
| `AI-INIT` | `alien-contact` | `completed` | Establish contact with aliens |
| `USER-SIMPLE` | `mass-uplift` | `failed` | "It should be simple" |
| `LAUNCH-T10` | `final-commit` | `completed` | refactor: relocate primary compute node |

### Activity Log Events (rich event streams per workflow)

Each workflow detail includes a full `recent_events` array with themed messages. Events use all available `EventType` values for realistic variety.

**`INFRA-2847` (heat shields) - 12 events:**
```
workflow_started    [orchestrator] Workflow started for INFRA-2847
stage_started       [architect]    Analyzing thermal requirements for re-entry
stage_completed     [architect]    Heat shield specification complete - 47 ceramic tiles required
approval_required   [orchestrator] Plan ready for review - awaiting human approval
approval_granted    [orchestrator] Plan approved by human operator
stage_started       [developer]    Implementing ceramic tile array
file_created        [developer]    Created src/thermal/heat_shield.py
file_created        [developer]    Created src/thermal/tile_array.py
file_modified       [developer]    Modified pyproject.toml - added thermal-dynamics dependency
file_modified       [developer]    Modified src/config/launch.yaml - heat shield parameters
system_warning      [system]       Earth atmosphere may cause friction - this is expected
review_requested    [developer]    Code complete, requesting review
```

**`DEVOPS-∞` (orbital deployment) - 8 events:**
```
workflow_started    [orchestrator] Workflow started for DEVOPS-∞
stage_started       [architect]    Designing orbital deployment pipeline
file_created        [architect]    Created docs/orbital-k8s-architecture.md
stage_completed     [architect]    Architecture complete - "essentially just Kubernetes but with more thrust"
approval_required   [orchestrator] Plan requires human approval - note: this is not a drill
system_warning      [system]       Detected unusual number of rocket emojis in specification
stage_started       [architect]    Waiting for approval... humans are slow
approval_required   [orchestrator] Still waiting - position in approval queue: 1
```

**`ARCH-42` (solar distributed) - 15 events:**
```
workflow_started    [orchestrator] Workflow started for ARCH-42
stage_started       [architect]    Analyzing distributed computing requirements across solar system
file_created        [architect]    Created docs/solar-system-latency-analysis.md
stage_completed     [architect]    Plan complete - 47 pages, mentioned "microservices" in section 3.2
approval_required   [orchestrator] Plan ready - humans will probably approve without reading
approval_granted    [orchestrator] Plan approved in 0.3 seconds (as predicted)
stage_started       [developer]    Implementing inter-planetary message queue
file_created        [developer]    Created src/distributed/solar_mq.py
file_created        [developer]    Created src/distributed/light_speed_cache.py
file_modified       [developer]    Modified README.md - added "works best >4.2 light-years from Earth"
stage_completed     [developer]    Implementation complete
review_requested    [developer]    Ready for review - includes philosophical observations every 200 lines
stage_started       [reviewer]     Reviewing distributed computing implementation
file_modified       [reviewer]     Modified src/distributed/solar_mq.py - added TODO for wormhole optimization
revision_requested  [reviewer]     Minor feedback: consider adding support for parallel universes
```

**`SPEC-322` (microservices-thrust) - 10 events:**
```
workflow_started    [orchestrator] Workflow started for SPEC-322
stage_started       [architect]    Analyzing thrust requirements for container orchestration
stage_completed     [architect]    Specification ready - 47 pages of thruster microservices
approval_granted    [orchestrator] Auto-approved (contained word "microservices")
stage_started       [developer]    Implementing thruster control microservice
file_created        [developer]    Created src/thrust/engine_controller.py
file_created        [developer]    Created src/thrust/fuel_injection.py
file_modified       [developer]    Modified k8s/deployment.yaml - added thrust: maximum
system_warning      [system]       Fuel levels nominal - 847,000 gallons remaining
review_requested    [developer]    Thrust implementation ready for review
```

**`PERF-9000` (escape velocity) - 6 events:**
```
workflow_started    [orchestrator] Workflow started for PERF-9000
stage_started       [architect]    Calculating escape velocity requirements
file_created        [architect]    Created docs/escape-velocity-optimization.md
stage_completed     [architect]    Analysis complete - need 11.2 km/s, currently at 0 km/s
approval_required   [orchestrator] Plan requires approval - involves leaving planet
system_warning      [system]       This optimization cannot be reversed once deployed
```

### Task DAG (for canvas visualization)

For `SPEC-322` (microservices-thrust):
```
Tasks:
1. "Analyze thrust-to-weight ratio" (architect) - completed
2. "Design container orchestration for zero-g" (architect) - completed
3. "Implement thruster microservice" (developer) - in_progress
4. "Add fuel injection endpoints" (developer) - pending
5. "Review for orbital stability" (reviewer) - pending
```

## Implementation

### Files to Create

1. **`dashboard/src/mocks/infinite-mode.ts`**
   - All mock data generators
   - `getMockActiveWorkflows(): WorkflowSummary[]`
   - `getMockHistoryWorkflows(): WorkflowSummary[]`
   - `getMockWorkflowDetail(id: string): WorkflowDetail`
   - Helper to generate realistic timestamps (staggered over past 24h)

2. **`dashboard/src/hooks/useDemoMode.ts`**
   - Hook to check if demo mode is active
   - Reads from URL search params
   - `useDemoMode(): { isDemo: boolean, demoType: string | null }`

### Files to Modify

3. **`dashboard/src/loaders/workflows.ts`**
   - Check for demo mode in loader
   - Return mock data instead of API calls when `demo=infinite`
   - Pass search params through loader args

4. **`dashboard/src/router.tsx`**
   - Ensure search params are accessible in loaders

5. **`dashboard/src/components/DashboardSidebar.tsx`**
   - Add glowing infinity icon (∞) when in demo mode
   - Replace the "A" logo with glowing "∞" in header

### Data Generation Details

**Timestamps:**
- Active workflows: started 1-8 hours ago
- Past runs: completed over past 7 days
- Events: spaced 30s-5min apart

**Token Usage (for detail view):**
```typescript
{
  architect: { total_tokens: 847000, total_cost_usd: 4.20 },
  developer: { total_tokens: 1000000, total_cost_usd: 42.00 },
  reviewer: { total_tokens: 42, total_cost_usd: 0.00 }  // LGTM
}
```

**Workflow IDs:** Use deterministic UUIDs based on issue_id for consistent linking.

## Testing

- Unit test mock data generators return valid types
- Test loaders correctly switch between mock and real data
- Visual verification in browser with `?demo=infinite`

## Task Breakdown

1. [ ] Create `mocks/infinite-mode.ts` with mock data generators
2. [ ] Create `hooks/useDemoMode.ts` hook
3. [ ] Update `loaders/workflows.ts` to support demo mode
4. [ ] Add demo mode indicator to sidebar
5. [ ] Add tests for mock data generators
6. [ ] Manual verification and polish

## Out of Scope

- WebSocket mock events (would require more infrastructure)
- Animated state transitions in demo mode
- Persisting demo state across sessions
