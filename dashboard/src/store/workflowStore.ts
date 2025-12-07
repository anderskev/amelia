import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { WorkflowEvent } from '../types';

const MAX_EVENTS_PER_WORKFLOW = 500;

/**
 * Zustand store for real-time WebSocket events and UI state.
 *
 * Note: Workflow data comes from React Router loaders, not this store.
 * This store only manages:
 * - Real-time events from WebSocket
 * - UI state (selected workflow)
 * - Connection state
 * - Pending actions for optimistic UI
 */
interface WorkflowState {
  // UI State
  selectedWorkflowId: string | null;

  // Real-time events from WebSocket (grouped by workflow)
  eventsByWorkflow: Record<string, WorkflowEvent[]>;

  // Last seen event ID for reconnection backfill
  lastEventId: string | null;

  // Connection state
  isConnected: boolean;
  connectionError: string | null;

  // Pending actions for optimistic UI tracking
  pendingActions: string[]; // Action IDs currently in flight

  // Actions
  selectWorkflow: (id: string | null) => void;
  addEvent: (event: WorkflowEvent) => void;
  setLastEventId: (id: string | null) => void;
  setConnected: (connected: boolean, error?: string) => void;
  addPendingAction: (actionId: string) => void;
  removePendingAction: (actionId: string) => void;
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set) => ({
      selectedWorkflowId: null,
      eventsByWorkflow: {},
      lastEventId: null,
      isConnected: false,
      connectionError: null,
      pendingActions: [],

      selectWorkflow: (id) => set({ selectedWorkflowId: id }),

      addEvent: (event) =>
        set((state) => {
          const existing = state.eventsByWorkflow[event.workflow_id] ?? [];
          const updated = [...existing, event];

          // Trim oldest events if exceeding limit (keep most recent)
          const trimmed =
            updated.length > MAX_EVENTS_PER_WORKFLOW
              ? updated.slice(-MAX_EVENTS_PER_WORKFLOW)
              : updated;

          return {
            eventsByWorkflow: {
              ...state.eventsByWorkflow,
              [event.workflow_id]: trimmed,
            },
            lastEventId: event.id,
          };
        }),

      setLastEventId: (id) => set({ lastEventId: id }),

      setConnected: (connected, error) =>
        set({
          isConnected: connected,
          connectionError: connected ? null : (error ?? null),
        }),

      addPendingAction: (actionId) =>
        set((state) => {
          // Don't add duplicates
          if (state.pendingActions.includes(actionId)) {
            return state;
          }
          return {
            pendingActions: [...state.pendingActions, actionId],
          };
        }),

      removePendingAction: (actionId) =>
        set((state) => ({
          pendingActions: state.pendingActions.filter((id) => id !== actionId),
        })),
    }),
    {
      name: 'amelia-workflow-state',
      storage: {
        getItem: (name) => {
          const value = sessionStorage.getItem(name);
          return value ? JSON.parse(value) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
      // Only persist UI state - events are ephemeral
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      partialize: (state) =>
        ({
          selectedWorkflowId: state.selectedWorkflowId,
          lastEventId: state.lastEventId,
        }) as any,
    }
  )
);
