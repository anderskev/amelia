# Spec Builder Token/Cost Display

## Overview

Add token usage and cost display to the Spec Builder chat UI. Shows per-message metrics in the message footer and session totals in the info bar.

**Branch**: `feat/brainstorm-token-display`

## Visual Design

### Message Footer (MessageMetadata)
```
⏱ 2m ago          ◈ 12.4K tok  $0.08                  [Copy]
```
- Monospace font, muted colors
- Token count: compact K notation (e.g., `12.4K tok`)
- Cost: emerald accent color (e.g., `$0.08`)

### Session Info Bar (SessionInfoBar)
```
● claude-sonnet-4.5 via CLI  │  5 messages  │  $0.42 total
```
- Add cost accumulator to existing bar
- Updates as messages complete

## Implementation Tasks

### Task 1: Backend — Add Token Tracking to Brainstorm Messages

**Files:**
- `amelia/server/models/brainstorm.py`
- `amelia/server/routes/brainstorm.py`
- `amelia/server/services/brainstorm_service.py`

**Changes:**

1.1. Add `MessageUsage` model to `brainstorm.py`:
```python
class MessageUsage(BaseModel):
    """Token usage for a single brainstorm message."""
    input_tokens: int
    output_tokens: int
    cost_usd: float
```

1.2. Add optional `usage` field to `Message` model:
```python
class Message(BaseModel):
    # ... existing fields
    usage: MessageUsage | None = None
```

1.3. Extract usage from driver after message completion in `brainstorm_service.py`:
- Call `driver.get_usage()` after agentic execution completes
- Create `MessageUsage` from `DriverUsage`
- Include in `message_complete` WebSocket event

1.4. Persist usage to database (add columns to messages table):
- `input_tokens INTEGER`
- `output_tokens INTEGER`
- `cost_usd REAL`

1.5. Return usage in `GET /api/brainstorm/sessions/{id}` response.

### Task 2: Backend — Add Session Token Summary

**Files:**
- `amelia/server/models/brainstorm.py`
- `amelia/server/routes/brainstorm.py`
- `amelia/server/database/repository.py`

**Changes:**

2.1. Add `SessionUsageSummary` model:
```python
class SessionUsageSummary(BaseModel):
    """Aggregated token usage for a brainstorm session."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    message_count: int
```

2.2. Add repository method to aggregate session usage:
```python
def get_brainstorm_session_usage(self, session_id: str) -> SessionUsageSummary | None
```

2.3. Include `usage_summary` in session responses and WebSocket events.

### Task 3: Frontend — Update TypeScript Types

**Files:**
- `dashboard/src/types/api.ts`

**Changes:**

3.1. Add `MessageUsage` interface:
```typescript
export interface MessageUsage {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}
```

3.2. Add optional `usage` to `BrainstormMessage`:
```typescript
export interface BrainstormMessage {
  // ... existing fields
  usage?: MessageUsage;
}
```

3.3. Add `SessionUsageSummary` interface:
```typescript
export interface SessionUsageSummary {
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: number;
  message_count: number;
}
```

3.4. Add optional `usage_summary` to `BrainstormingSession`:
```typescript
export interface BrainstormingSession {
  // ... existing fields
  usage_summary?: SessionUsageSummary;
}
```

### Task 4: Frontend — Update MessageMetadata Component

**Files:**
- `dashboard/src/components/brainstorm/MessageMetadata.tsx`

**Changes:**

4.1. Add `usage` prop to interface:
```typescript
interface MessageMetadataProps {
  timestamp: string;
  content: string;
  usage?: MessageUsage;
  className?: string;
}
```

4.2. Add token/cost display between timestamp and copy button:
```tsx
{usage && (
  <div className="flex items-center gap-2">
    <span className="text-muted-foreground/50">◈</span>
    <span>{formatTokens(usage.input_tokens + usage.output_tokens)} tok</span>
    <span className="text-emerald-500/70">${usage.cost_usd.toFixed(2)}</span>
  </div>
)}
```

4.3. Add `formatTokens` utility (or import from existing):
```typescript
function formatTokens(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`;
  }
  return count.toString();
}
```

### Task 5: Frontend — Update SessionInfoBar Component

**Files:**
- `dashboard/src/components/brainstorm/SessionInfoBar.tsx`

**Changes:**

5.1. Add `usageSummary` prop:
```typescript
interface SessionInfoBarProps {
  profile: string | null;
  status: SessionStatus;
  messageCount: number;
  usageSummary?: SessionUsageSummary;
}
```

5.2. Add cost display to the bar (after message count):
```tsx
{usageSummary && usageSummary.total_cost_usd > 0 && (
  <>
    <Separator orientation="vertical" className="h-3" />
    <span className="text-emerald-500/70 font-medium">
      ${usageSummary.total_cost_usd.toFixed(2)} total
    </span>
  </>
)}
```

### Task 6: Frontend — Wire Up Components

**Files:**
- `dashboard/src/pages/SpecBuilderPage.tsx`
- `dashboard/src/store/brainstormStore.ts`
- `dashboard/src/hooks/useBrainstormSession.ts`

**Changes:**

6.1. Update store to track session usage summary:
```typescript
interface BrainstormState {
  // ... existing
  sessionUsage: SessionUsageSummary | null;
}
```

6.2. Update `message_complete` handler to extract usage from message.

6.3. Update `session_created` / session load to populate usage summary.

6.4. Pass `usage` prop to `MessageMetadata` in SpecBuilderPage:
```tsx
<MessageMetadata
  timestamp={message.created_at}
  content={message.content}
  usage={message.usage}
/>
```

6.5. Pass `usageSummary` prop to `SessionInfoBar`:
```tsx
<SessionInfoBar
  profile={activeProfile}
  status={...}
  messageCount={messages.length}
  usageSummary={sessionUsage}
/>
```

### Task 7: Tests

**Files:**
- `tests/unit/server/test_brainstorm_usage.py` (new)
- `dashboard/src/components/brainstorm/__tests__/MessageMetadata.test.tsx`
- `dashboard/src/components/brainstorm/__tests__/SessionInfoBar.test.tsx`

**Changes:**

7.1. Backend unit tests:
- Test `MessageUsage` model serialization
- Test usage extraction from driver
- Test session usage aggregation

7.2. Frontend component tests:
- Test `MessageMetadata` renders without usage (backward compat)
- Test `MessageMetadata` renders with usage
- Test `SessionInfoBar` renders without usage
- Test `SessionInfoBar` renders with usage
- Test token formatting (K notation)

## Acceptance Criteria

- [ ] Assistant messages show token count and cost in footer
- [ ] Session info bar shows cumulative cost
- [ ] Existing messages without usage data render correctly (no errors)
- [ ] Usage persists and loads correctly when revisiting sessions
- [ ] All tests pass

## Dependencies

- Existing `DriverUsage` abstraction in `amelia/drivers/`
- Existing `calculate_token_cost()` function in `amelia/server/models/tokens.py`
- Existing token formatting utils in `dashboard/src/utils/workflow.ts`
