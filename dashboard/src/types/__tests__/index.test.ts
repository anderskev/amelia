import { describe, it, expect } from 'vitest';
import type { EventLevel, WorkflowEvent } from '../index';

describe('WorkflowEvent types', () => {
  it('supports level field', () => {
    const event: WorkflowEvent = {
      id: 'evt-1',
      workflow_id: 'wf-1',
      sequence: 1,
      timestamp: '2025-01-01T00:00:00Z',
      agent: 'developer',
      event_type: 'claude_tool_call',
      level: 'trace',
      message: 'Tool call',
      tool_name: 'Edit',
      tool_input: { file: 'test.py' },
      is_error: false,
    };

    expect(event.level).toBe('trace');
    expect(event.tool_name).toBe('Edit');
  });

  it('level can be info, debug, or trace', () => {
    const levels: EventLevel[] = ['info', 'debug', 'trace'];
    expect(levels).toHaveLength(3);
  });

  it('supports distributed tracing fields', () => {
    const event: WorkflowEvent = {
      id: 'evt-1',
      workflow_id: 'wf-1',
      sequence: 1,
      timestamp: '2025-01-01T00:00:00Z',
      agent: 'developer',
      event_type: 'claude_tool_result',
      level: 'trace',
      message: 'Tool result',
      trace_id: 'trace-abc-123',
      parent_id: 'evt-parent',
    };

    expect(event.trace_id).toBe('trace-abc-123');
    expect(event.parent_id).toBe('evt-parent');
  });
});
