# Brainstorming Integration & Polish Design

**Issue**: #300 - Brainstorming Integration & Polish (Phase 4)
**Date**: 2026-01-20
**Status**: Draft

## Problem Statement

When a user completes a brainstorming session and hands off an artifact to implementation, the design document content is never passed to the implementation pipeline. The `BrainstormService.handoff_to_implementation()` creates a workflow but:

1. `CreateWorkflowRequest` has no field for artifact path
2. `OrchestratorService._prepare_workflow_state()` doesn't load the design
3. `ImplementationState.design` remains `None`
4. Architect generates a new plan from scratch, ignoring brainstorming work

Additionally:
- Error handling is incomplete (3 TODO comments for missing error toasts)
- WebSocket disconnection leaves messages stuck in "streaming" status
- No mobile responsiveness in SpecBuilderPage
- Basic accessibility gaps (no focus management, no aria-live regions)

## Goals

1. Pass design artifacts through handoff - Architect receives and uses brainstorming output
2. Show error feedback - Users see toast notifications when operations fail
3. Handle WebSocket disconnects - Messages don't hang in "streaming" state forever
4. Mobile responsiveness - SpecBuilderPage works on mobile devices
5. Accessibility - Focus management, aria-live regions, screen reader support

## Non-Goals (Deferred)

- Pagination for long conversations
- Multi-tab conflict resolution
- User documentation updates
- Oracle integration

---

## Design

### 1. Handoff Flow Fix

Thread the artifact path from handoff through to `ImplementationState.design`. Three files need changes:

**Add `artifact_path` to `CreateWorkflowRequest`** (`amelia/server/models/requests.py`):

```python
class CreateWorkflowRequest(BaseModel):
    # ... existing fields ...
    artifact_path: str | None = None  # Path to design artifact from brainstorming
```

**Pass artifact path in handoff** (`amelia/server/services/brainstorm.py:974`):

```python
request = CreateWorkflowRequest(
    issue_id=issue_id,
    worktree_path=worktree_path,
    task_title=issue_title or f"Implement design from {artifact_path}",
    task_description=issue_description,
    artifact_path=artifact_path,  # NEW
    start=False,
)
```

**Load design in orchestrator** (`amelia/server/orchestrator/service.py:_prepare_workflow_state`):

```python
design = None
if request.artifact_path:
    design = Design.from_file(request.artifact_path)

execution_state = ImplementationState(
    # ... existing fields ...
    design=design,  # Now populated when artifact_path provided
)
```

**Why this approach**:
- Minimal changes (3 files, ~10 lines)
- Uses existing `Design.from_file()` classmethod
- `ImplementationState.design` field already exists but is unused
- Architect already checks for `state.design` - no agent changes needed

---

### 2. Error Handling

#### Toast Notifications

Three locations in `SpecBuilderPage.tsx` have TODO comments for missing error toasts:

| Location | Error Case | Message |
|----------|------------|---------|
| Line 135 | Session creation fails | "Failed to create session" |
| Line 172 | Handoff fails | "Handoff failed: {error}" |
| Line 190 | Start brainstorming fails | "Failed to start session" |

Import `toast` from existing Toast component, replace `console.error` with `toast.error()`.

#### WebSocket Disconnect Handling

When WebSocket disconnects mid-stream, messages stay in `status: "streaming"` forever.

**Solution** in `useBrainstormSession.ts`:

1. Track active streaming message ID in hook state
2. On WebSocket disconnect event, check if there's an active streaming message
3. Set that message's status to `"error"` with `errorMessage: "Connection lost"`

```typescript
// In useWebSocket connection close handler
if (activeStreamingMessageId) {
  updateMessage(activeStreamingMessageId, {
    status: 'error',
    errorMessage: 'Connection lost. Please retry.',
  });
}
```

#### Message Error Display

`MessageContent` component renders error state:

```tsx
{message.status === 'error' && (
  <div className="text-red-500 text-sm mt-2">
    ⚠ {message.errorMessage || 'Message failed'}
  </div>
)}
```

---

### 3. Mobile Responsiveness

Use Tailwind responsive breakpoints. No structural changes - just class additions.

**SessionDrawer** (`SessionDrawer.tsx`):
```tsx
// Current: w-80
// Change to: w-full sm:w-80
// On mobile: full-width overlay. On desktop: fixed sidebar.
```

**SpecBuilderPage layout**:
```tsx
// Add responsive padding and max-width
<div className="px-2 sm:px-4 py-4 sm:py-6">
  <div className="max-w-full sm:max-w-3xl mx-auto">
```

**Touch targets** - ensure buttons are at least 44x44px on mobile:
```tsx
// Add min-h-11 min-w-11 to icon buttons for accessibility
<Button className="min-h-11 min-w-11 sm:min-h-0 sm:min-w-0">
```

**SessionDrawer toggle** - on mobile, drawer overlays content with backdrop:
```tsx
// Add overlay behavior on small screens
<div className="fixed inset-0 bg-black/50 sm:hidden" onClick={onClose} />
```

**Breakpoint Strategy**:

| Breakpoint | Behavior |
|------------|----------|
| < 640px (mobile) | Full-width drawer overlay, larger touch targets, reduced padding |
| >= 640px (sm+) | Current desktop layout |

---

### 4. Accessibility Improvements

**Focus Management**:

After message submit, return focus to the input textarea:
```tsx
// In handleSubmit, after clearing input
textareaRef.current?.focus();
```

After closing SessionDrawer, return focus to the menu button:
```tsx
// In drawer close handler
onClose={() => {
  setDrawerOpen(false);
  menuButtonRef.current?.focus();
}}
```

**Aria-live for Streaming Messages**:

Wrap the conversation area in a live region so screen readers announce new messages:
```tsx
<div role="log" aria-live="polite" aria-atomic="false">
  {messages.map(msg => <Message key={msg.id} ... />)}
</div>
```

**Aria-busy During Loading**:

Add busy state to conversation container during streaming:
```tsx
<div role="log" aria-busy={isStreaming}>
```

**Drawer Announcement**:

Add aria attributes to SessionDrawer:
```tsx
<aside
  role="dialog"
  aria-modal="true"
  aria-label="Brainstorming sessions"
>
```

---

## Files to Change

| File | Changes |
|------|---------|
| `amelia/server/models/requests.py` | Add `artifact_path` field to `CreateWorkflowRequest` |
| `amelia/server/services/brainstorm.py` | Pass `artifact_path` in handoff request |
| `amelia/server/orchestrator/service.py` | Load `Design` from artifact path in `_prepare_workflow_state` |
| `dashboard/src/pages/SpecBuilderPage.tsx` | Error toasts (3 locations), responsive classes, focus management |
| `dashboard/src/hooks/useBrainstormSession.ts` | Handle WebSocket disconnect for streaming messages |
| `dashboard/src/components/ai-elements/message.tsx` | Render error state in messages |
| `dashboard/src/components/brainstorm/SessionDrawer.tsx` | Responsive width, mobile overlay, aria attributes |
| `dashboard/src/components/brainstorm/ConversationContent.tsx` | `aria-busy` during streaming |

---

## Testing Strategy

### Integration Tests (mock only at external HTTP boundary)

| Test | What It Validates |
|------|-------------------|
| `test_handoff_passes_design_to_implementation` | Full flow: create session -> send message -> create artifact -> handoff -> verify `ImplementationState.design` is populated with artifact content |
| `test_handoff_without_artifact_path` | Handoff with `artifact_path=None` leaves `design=None` (backward compatible) |
| `test_handoff_with_missing_artifact_file` | Returns 404 when artifact file doesn't exist on disk |

These tests use real `BrainstormService`, `OrchestratorService`, and `Design.from_file()` - only mocking the LLM HTTP calls via `httpx.AsyncClient.post`.

### Frontend Integration Tests (mock only fetch/WebSocket)

| Test | What It Validates |
|------|-------------------|
| `test_error_toast_on_session_creation_failure` | API returns 500 -> toast.error called |
| `test_error_toast_on_handoff_failure` | API returns 400 -> toast.error called with message |
| `test_message_error_on_websocket_disconnect` | WebSocket closes -> streaming message status becomes "error" |

### Unit Tests (fill gaps)

- `CreateWorkflowRequest` model validation for `artifact_path`
- `Design.from_file()` error handling for malformed markdown
- Responsive class assertions via snapshot tests
- Focus management ref assertions

---

## Out of Scope (Future Work)

- Pagination for long conversations
- Multi-tab conflict resolution
- User documentation for Spec Builder feature
- Oracle integration during brainstorming
