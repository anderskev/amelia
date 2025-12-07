import { describe, it, expect, beforeEach } from 'vitest';
import { useWorkflowStore } from '../workflowStore';
import type { WorkflowEvent } from '../../types';

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

describe('workflowStore', () => {
  beforeEach(() => {
    useWorkflowStore.setState({
      selectedWorkflowId: null,
      eventsByWorkflow: {},
      lastEventId: null,
      isConnected: false,
      connectionError: null,
      pendingActions: [],
    });
    sessionStorageMock.clear();
  });

  describe('selectWorkflow', () => {
    it('should update selectedWorkflowId', () => {
      useWorkflowStore.getState().selectWorkflow('wf-123');

      expect(useWorkflowStore.getState().selectedWorkflowId).toBe('wf-123');
    });

    it('should allow null selection', () => {
      useWorkflowStore.setState({ selectedWorkflowId: 'wf-1' });
      useWorkflowStore.getState().selectWorkflow(null);

      expect(useWorkflowStore.getState().selectedWorkflowId).toBeNull();
    });
  });

  describe('addEvent', () => {
    it('should add event to workflow event list', () => {
      const event: WorkflowEvent = {
        id: 'evt-1',
        workflow_id: 'wf-1',
        sequence: 1,
        timestamp: '2025-12-01T10:00:00Z',
        agent: 'architect',
        event_type: 'workflow_started',
        message: 'Workflow started',
        data: undefined,
        correlation_id: undefined,
      };

      useWorkflowStore.getState().addEvent(event);

      const state = useWorkflowStore.getState();
      expect(state.eventsByWorkflow['wf-1']).toHaveLength(1);
      expect(state.eventsByWorkflow['wf-1']![0]).toEqual(event);
      expect(state.lastEventId).toBe('evt-1');
    });

    it('should append to existing events', () => {
      const event1: WorkflowEvent = {
        id: 'evt-1',
        workflow_id: 'wf-1',
        sequence: 1,
        timestamp: '2025-12-01T10:00:00Z',
        agent: 'architect',
        event_type: 'workflow_started',
        message: 'Started',
        data: undefined,
        correlation_id: undefined,
      };

      const event2: WorkflowEvent = {
        id: 'evt-2',
        workflow_id: 'wf-1',
        sequence: 2,
        timestamp: '2025-12-01T10:01:00Z',
        agent: 'architect',
        event_type: 'stage_started',
        message: 'Planning',
        data: { stage: 'architect' },
        correlation_id: undefined,
      };

      useWorkflowStore.getState().addEvent(event1);
      useWorkflowStore.getState().addEvent(event2);

      const events = useWorkflowStore.getState().eventsByWorkflow['wf-1'];
      expect(events).toHaveLength(2);
      expect(events![0]!.id).toBe('evt-1');
      expect(events![1]!.id).toBe('evt-2');
    });

    it('should trim events when exceeding MAX_EVENTS_PER_WORKFLOW', () => {
      const MAX_EVENTS = 500;

      // Add 501 events
      for (let i = 1; i <= MAX_EVENTS + 1; i++) {
        const event: WorkflowEvent = {
          id: `evt-${i}`,
          workflow_id: 'wf-1',
          sequence: i,
          timestamp: '2025-12-01T10:00:00Z',
          agent: 'architect',
          event_type: 'stage_started',
          message: `Event ${i}`,
          data: undefined,
          correlation_id: undefined,
        };
        useWorkflowStore.getState().addEvent(event);
      }

      const events = useWorkflowStore.getState().eventsByWorkflow['wf-1'];
      expect(events).toHaveLength(MAX_EVENTS);
      // Should keep most recent (evt-2 to evt-501, dropping evt-1)
      expect(events![0]!.id).toBe('evt-2');
      expect(events![MAX_EVENTS - 1]!.id).toBe(`evt-${MAX_EVENTS + 1}`);
    });
  });

  describe('connection state', () => {
    it('should update connection status', () => {
      useWorkflowStore.getState().setConnected(true);

      expect(useWorkflowStore.getState().isConnected).toBe(true);
      expect(useWorkflowStore.getState().connectionError).toBeNull();
    });

    it('should set error when disconnected', () => {
      useWorkflowStore.getState().setConnected(false, 'Connection lost');

      expect(useWorkflowStore.getState().isConnected).toBe(false);
      expect(useWorkflowStore.getState().connectionError).toBe('Connection lost');
    });
  });

  describe('pending actions', () => {
    it('should add pending action', () => {
      useWorkflowStore.getState().addPendingAction('approve-wf-1');

      expect(useWorkflowStore.getState().pendingActions.includes('approve-wf-1')).toBe(true);
    });

    it('should not duplicate pending action', () => {
      useWorkflowStore.getState().addPendingAction('approve-wf-1');
      useWorkflowStore.getState().addPendingAction('approve-wf-1');

      expect(useWorkflowStore.getState().pendingActions.length).toBe(1);
    });

    it('should remove pending action', () => {
      useWorkflowStore.getState().addPendingAction('approve-wf-1');
      useWorkflowStore.getState().removePendingAction('approve-wf-1');

      expect(useWorkflowStore.getState().pendingActions.length).toBe(0);
    });
  });

  describe('persistence', () => {
    it('should persist selectedWorkflowId to sessionStorage', () => {
      useWorkflowStore.getState().selectWorkflow('wf-123');

      const stored = sessionStorageMock.getItem('amelia-workflow-state');
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored!);
      expect(parsed.state.selectedWorkflowId).toBe('wf-123');
    });

    it('should persist lastEventId to sessionStorage', () => {
      useWorkflowStore.getState().addEvent({
        id: 'evt-999',
        workflow_id: 'wf-1',
        sequence: 1,
        timestamp: '2025-12-01T10:00:00Z',
        agent: 'architect',
        event_type: 'workflow_started',
        message: 'Started',
        data: undefined,
        correlation_id: undefined,
      });

      const stored = sessionStorageMock.getItem('amelia-workflow-state');
      const parsed = JSON.parse(stored!);
      expect(parsed.state.lastEventId).toBe('evt-999');
    });

    it('should NOT persist events to sessionStorage', () => {
      useWorkflowStore.getState().addEvent({
        id: 'evt-1',
        workflow_id: 'wf-1',
        sequence: 1,
        timestamp: '2025-12-01T10:00:00Z',
        agent: 'architect',
        event_type: 'workflow_started',
        message: 'Started',
        data: undefined,
        correlation_id: undefined,
      });

      const stored = sessionStorageMock.getItem('amelia-workflow-state');
      const parsed = JSON.parse(stored!);
      expect(parsed.state.eventsByWorkflow).toBeUndefined();
    });
  });
});
