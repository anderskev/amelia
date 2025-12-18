# Thinking Token Streaming: Problem Analysis & Solution Context

**Date:** 2025-12-16
**Status:** Research Complete - Ready for Solution Design

## Executive Summary

Amelia cannot stream extended thinking tokens to the dashboard, despite the dashboard being fully prepared to display them. The root cause is that Amelia's Claude CLI driver wrapper neither enables extended thinking nor parses thinking content blocks from the stream output.

---

## Problem Statement

When running the architect prompt directly in Claude Code CLI, users see thinking tokens streamed in real-time. However, when the same prompt runs through Amelia's orchestrator, thinking tokens are not displayed in:
- The Logs view (real-time stream events)
- The Activity Log (interleaved with workflow events)

**User expectation:** See Claude's reasoning process in real-time, just like in Claude Code CLI.

**Current behavior:** Only text responses and tool calls appear; thinking is invisible.

---

## Architecture Overview

### Amelia's Driver Abstraction

Amelia supports two driver types configured via `settings.amelia.yaml`:

| Driver | Implementation | Use Case |
|--------|---------------|----------|
| `cli:claude` | `amelia/drivers/cli/claude.py` | Wraps Claude Code CLI for enterprise compliance |
| `api:openai` | `amelia/drivers/api/openai.py` | Direct API via PydanticAI |

The CLI driver is the primary focus since it's what wraps Claude Code.

### Current Streaming Flow

```
Claude Code CLI (--output-format stream-json)
    │
    ▼
ClaudeStreamEvent.from_stream_json()  ← PARSING GAP HERE
    │
    ▼
convert_to_stream_event()
    │
    ▼
StreamEvent (unified type)
    │
    ▼
WebSocket → Dashboard
```

---

## Gap Analysis

### Gap 1: Extended Thinking Not Enabled

**Location:** `amelia/drivers/cli/claude.py:506`

**Current command construction:**
```python
cmd_args = ["claude", "-p", "--verbose", "--model", self.model, "--output-format", "stream-json"]

# Add permission flags
if self.skip_permissions:
    cmd_args.append("--dangerously-skip-permissions")
if self.allowed_tools:
    cmd_args.extend(["--allowedTools", ",".join(self.allowed_tools)])
if self.disallowed_tools:
    cmd_args.extend(["--disallowedTools", ",".join(self.disallowed_tools)])
```

**Missing:** The `--max-thinking-tokens` flag that enables extended thinking.

### Gap 2: Thinking Content Blocks Not Parsed

**Location:** `amelia/drivers/cli/claude.py:155-179`

**Current parsing logic:**
```python
# Handle assistant messages (contain content blocks)
if msg_type == "assistant":
    message = data.get("message", {})
    content_blocks = message.get("content", [])

    for block in content_blocks:
        block_type = block.get("type", "")

        if block_type == "text":
            return cls(type="assistant", content=block.get("text", ""))

        if block_type == "tool_use":
            return cls(
                type="tool_use",
                tool_name=block.get("name"),
                tool_input=block.get("input")
            )

# Handle system messages
if msg_type == "system":
    return cls(type="system", content=data.get("message", ""))

# Unknown type - return as system event
return cls(type="system", content=f"Unknown event type: {msg_type}")
```

**Problem:** When a `thinking` block is encountered, it doesn't match `text` or `tool_use`, so the loop continues and the thinking content is discarded.

### Gap 3: No Thinking Event Type in CLI Driver

**Location:** `amelia/drivers/cli/claude.py:21`

**Current event types:**
```python
ClaudeStreamEventType = Literal["assistant", "tool_use", "result", "error", "system"]
```

**Missing:** A `"thinking"` type for thinking content blocks.

---

## Claude Agent SDK Reference Implementation

The Claude Agent SDK Python (`../claude-agent-sdk-python`) properly implements thinking token support. Here's how:

### Enabling Extended Thinking

**File:** `claude_agent_sdk/types.py` (line 673)
```python
@dataclass
class ClaudeAgentOptions:
    """Options for configuring a Claude agent."""
    # ... other fields ...
    max_thinking_tokens: int | None = None  # Enable extended thinking
```

**File:** `claude_agent_sdk/_internal/transport/subprocess_cli.py` (lines 311-314)
```python
# Build CLI arguments from options
if options.max_thinking_tokens is not None:
    args.extend(["--max-thinking-tokens", str(options.max_thinking_tokens)])
```

### Content Block Types

**File:** `claude_agent_sdk/types.py` (lines 512-546)
```python
@dataclass
class TextBlock:
    """Text content block."""
    text: str

@dataclass
class ThinkingBlock:
    """Thinking content block."""
    thinking: str
    signature: str  # Cryptographic signature for verification

@dataclass
class ToolUseBlock:
    """Tool use content block."""
    id: str
    name: str
    input: dict[str, Any]

@dataclass
class ToolResultBlock:
    """Tool result content block."""
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None

# Union type for all content blocks
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### Parsing Thinking Blocks

**File:** `claude_agent_sdk/_internal/message_parser.py` (lines 98-104)
```python
case "thinking":
    content_blocks.append(
        ThinkingBlock(
            thinking=block["thinking"],
            signature=block["signature"],
        )
    )
```

### Streaming Events

**File:** `claude_agent_sdk/types.py` (lines 604-611)
```python
@dataclass
class StreamEvent:
    """Stream event for partial message updates during streaming."""
    uuid: str
    session_id: str
    event: dict[str, Any]  # The raw Anthropic API stream event
    parent_tool_use_id: str | None = None
```

**Stream event types for thinking:**
- `content_block_start` with `type: "thinking"` - Start of thinking block
- `content_block_delta` with `delta.type: "thinking_delta"` - Incremental thinking text
- `content_block_stop` - End of thinking block

### Example: Handling Streaming Thinking

```python
async for message in client.receive_response():
    # Complete thinking blocks (after generation)
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, ThinkingBlock):
                print(f"Thinking: {block.thinking}")
            elif isinstance(block, TextBlock):
                print(f"Response: {block.text}")

    # Streaming thinking deltas (real-time)
    elif isinstance(message, StreamEvent):
        event = message.event
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "thinking_delta":
                thinking_text = delta.get("thinking", "")
                print(f"Thinking: {thinking_text}")
```

---

## Claude CLI Stream JSON Format

When extended thinking is enabled, the Claude CLI outputs JSON in this format:

### Thinking Block Start
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "thinking",
        "thinking": "Let me analyze this problem step by step...",
        "signature": "sig_abc123..."
      }
    ]
  }
}
```

### Thinking Delta (Streaming)
```json
{
  "type": "content_block_delta",
  "index": 0,
  "delta": {
    "type": "thinking_delta",
    "thinking": "First, I need to consider..."
  }
}
```

### Text Block (After Thinking)
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "text",
        "text": "Here's my response..."
      }
    ]
  }
}
```

---

## Dashboard Readiness

The Amelia dashboard is **already prepared** to display thinking events:

### Backend Types

**File:** `amelia/core/types.py` (lines 156-168)
```python
class StreamEventType(StrEnum):
    """Types of streaming events from Claude Code."""
    CLAUDE_THINKING = "claude_thinking"
    CLAUDE_TOOL_CALL = "claude_tool_call"
    CLAUDE_TOOL_RESULT = "claude_tool_result"
    AGENT_OUTPUT = "agent_output"
```

### Frontend Types

**File:** `dashboard/src/types/index.ts` (lines 503-507)
```typescript
export const StreamEventType = {
  CLAUDE_THINKING: 'claude_thinking',
  CLAUDE_TOOL_CALL: 'claude_tool_call',
  CLAUDE_TOOL_RESULT: 'claude_tool_result',
  AGENT_OUTPUT: 'agent_output',
} as const;
```

### UI Components

**File:** `dashboard/src/pages/LogsPage.tsx` (lines 32-35)
```typescript
const eventTypeIcons: Record<StreamEventType, React.ReactNode> = {
  [StreamEventType.CLAUDE_THINKING]: (
    <Brain className="w-4 h-4 text-yellow-500" />
  ),
  // ...
};

const eventTypeColors: Record<StreamEventType, string> = {
  [StreamEventType.CLAUDE_THINKING]: 'bg-yellow-500/10 border-yellow-500/20',
  // ...
};
```

---

## Solution Requirements

### Functional Requirements

1. **Enable extended thinking** - Pass `--max-thinking-tokens` to CLI when configured
2. **Parse thinking blocks** - Extract thinking content from assistant messages
3. **Stream thinking deltas** - Support real-time thinking token streaming
4. **Preserve signature** - Store the cryptographic signature for verification
5. **Display in dashboard** - Route thinking events to existing UI components

### Configuration Requirements

1. **Profile-level config** - Allow `max_thinking_tokens` in `settings.amelia.yaml`
2. **Agent-level override** - Different agents may need different thinking budgets
3. **Default behavior** - Sensible default (enabled for capable models)

### Non-Functional Requirements

1. **Backward compatibility** - Don't break existing functionality
2. **Performance** - Thinking can generate many tokens; handle efficiently
3. **Memory** - Dashboard already has buffer limits for stream events

---

## Files to Modify

### Backend (Python)

| File | Changes |
|------|---------|
| `amelia/drivers/cli/claude.py` | Add thinking block parsing, add `--max-thinking-tokens` flag |
| `amelia/core/types.py` | Possibly add thinking-specific fields to `StreamEvent` |
| `amelia/drivers/base.py` | Add `max_thinking_tokens` to driver interface if needed |

### Configuration

| File | Changes |
|------|---------|
| `amelia/core/types.py` (Profile) | Add `max_thinking_tokens` field |

### Tests

| File | Changes |
|------|---------|
| `tests/unit/drivers/cli/test_claude_convert.py` | Add thinking block parsing tests |
| `tests/unit/core/test_stream_types.py` | Add thinking event tests |

---

## Open Questions for Solution Design

1. **Streaming granularity** - Should we emit one event per thinking block, or stream deltas?
2. **Signature handling** - Should we validate/store the cryptographic signature?
3. **Token budget** - What's a sensible default for `max_thinking_tokens`?
4. **Model detection** - Should we auto-enable thinking for models that support it?
5. **UI treatment** - Should thinking be collapsible/expandable in the dashboard?
6. **Cost visibility** - Thinking tokens have different pricing; show this to users?

---

## Reference Links

- Claude Agent SDK Python: `../claude-agent-sdk-python`
- Amelia CLI Driver: `amelia/drivers/cli/claude.py`
- Dashboard Logs Page: `dashboard/src/pages/LogsPage.tsx`
- Stream Store: `dashboard/src/store/stream-store.ts`
