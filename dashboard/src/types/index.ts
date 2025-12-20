/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * Shared TypeScript types for the Amelia Dashboard.
 * These types mirror the Python Pydantic models from the backend API.
 */

// ============================================================================
// Workflow Types
// ============================================================================

/**
 * The current execution state of a workflow.
 *
 * - `pending`: Workflow has been created but not yet started
 * - `in_progress`: Workflow is actively executing
 * - `blocked`: Workflow is waiting for human approval or input
 * - `completed`: Workflow finished successfully
 * - `failed`: Workflow encountered an error and stopped
 * - `cancelled`: Workflow was manually cancelled by a user
 *
 * @example
 * ```typescript
 * const status: WorkflowStatus = 'in_progress';
 * ```
 */
export type WorkflowStatus =
  | 'pending'
  | 'in_progress'
  | 'blocked'
  | 'completed'
  | 'failed'
  | 'cancelled';

/**
 * Summary information about a workflow, used in list views.
 * Contains the minimal data needed to display a workflow in a table or card.
 */
export interface WorkflowSummary {
  /** Unique identifier for the workflow. */
  id: string;

  /** The issue ID from the tracking system (e.g., JIRA-123, GitHub #45). */
  issue_id: string;

  /** Name of the git worktree where this workflow is executing. */
  worktree_name: string;

  /** Current execution state of the workflow. */
  status: WorkflowStatus;

  /** ISO 8601 timestamp when the workflow started, or null if not yet started. */
  started_at: string | null;

  /** Name of the current execution stage (e.g., 'architect', 'developer', 'reviewer'). */
  current_stage: string | null;
}

/**
 * Complete detailed information about a workflow.
 * Extends WorkflowSummary with additional metadata, execution plan, token usage, and event history.
 */
export interface WorkflowDetail extends WorkflowSummary {
  /** Absolute filesystem path to the git worktree. */
  worktree_path: string;

  /** ISO 8601 timestamp when the workflow completed, or null if still running. */
  completed_at: string | null;

  /** Human-readable error message if the workflow failed, otherwise null. */
  failure_reason: string | null;

  /** Token usage statistics grouped by agent name. */
  token_usage: Record<string, TokenSummary>;

  /** Recent workflow events for this workflow, ordered by sequence number. */
  recent_events: WorkflowEvent[];

  // Batch execution fields (intelligent execution model)
  /** Batched execution plan, or null if not yet planned. */
  execution_plan: ExecutionPlan | null;

  /** Index of the current batch being executed (0-based). */
  current_batch_index: number;

  /** Results from completed batches. */
  batch_results: BatchResult[];

  /** Current Developer agent status. */
  developer_status: DeveloperStatus | null;

  /** Active blocker report if execution is blocked. */
  current_blocker: BlockerReport | null;

  /** Records of human approvals for batches. */
  batch_approvals: BatchApproval[];
}

// ============================================================================
// Event Types
// ============================================================================

/**
 * Types of events that can occur during workflow execution.
 * Events are emitted by agents and the orchestrator to track workflow progress.
 *
 * **Lifecycle events**: Overall workflow state changes
 * - `workflow_started`: Workflow execution has begun
 * - `workflow_completed`: Workflow finished successfully
 * - `workflow_failed`: Workflow encountered a fatal error
 * - `workflow_cancelled`: Workflow was cancelled by a user
 *
 * **Stage events**: Agent execution state changes
 * - `stage_started`: An agent has started executing
 * - `stage_completed`: An agent has finished executing
 *
 * **Approval events**: Human-in-the-loop interactions
 * - `approval_required`: Workflow is blocked waiting for approval
 * - `approval_granted`: User approved the plan or changes
 * - `approval_rejected`: User rejected the plan or changes
 *
 * **Artifact events**: File system changes
 * - `file_created`: A new file was created
 * - `file_modified`: An existing file was modified
 * - `file_deleted`: A file was deleted
 *
 * **Review cycle events**: Developer-reviewer interaction
 * - `review_requested`: Developer requested code review
 * - `review_completed`: Reviewer approved the changes
 * - `revision_requested`: Reviewer requested changes
 *
 * **Agent messages**: Task-level messages and status updates
 * - `agent_message`: A message from an agent during task execution
 * - `task_started`: A task has started execution
 * - `task_completed`: A task has completed successfully
 * - `task_failed`: A task has failed with an error
 *
 * **System events**: Errors and warnings
 * - `system_error`: An error occurred during execution
 * - `system_warning`: A warning was issued
 */
export type EventType =
  // Lifecycle
  | 'workflow_started'
  | 'workflow_completed'
  | 'workflow_failed'
  | 'workflow_cancelled'
  // Stages
  | 'stage_started'
  | 'stage_completed'
  // Approval
  | 'approval_required'
  | 'approval_granted'
  | 'approval_rejected'
  // Artifacts
  | 'file_created'
  | 'file_modified'
  | 'file_deleted'
  // Review cycle
  | 'review_requested'
  | 'review_completed'
  | 'revision_requested'
  // Agent messages (replaces in-state message accumulation)
  | 'agent_message'
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  // System
  | 'system_error'
  | 'system_warning';

/**
 * A single event emitted during workflow execution.
 * Events are streamed in real-time via WebSocket and stored for historical viewing.
 */
export interface WorkflowEvent {
  /** Unique identifier for this event. */
  id: string;

  /** ID of the workflow this event belongs to. */
  workflow_id: string;

  /** Sequential event number within the workflow (monotonically increasing). */
  sequence: number;

  /** ISO 8601 timestamp when the event was emitted. */
  timestamp: string;

  /** Name of the agent that emitted this event (e.g., 'architect', 'developer'). */
  agent: string;

  /** Type of event that occurred. */
  event_type: EventType;

  /** Human-readable message describing the event. */
  message: string;

  /** Optional additional structured data specific to this event type. */
  data?: Record<string, unknown>;

  /** Optional correlation ID for grouping related events. */
  correlation_id?: string;
}

// ============================================================================
// Token Usage Types
// ============================================================================

/**
 * Aggregated token usage and cost for an agent or workflow.
 * Provides a high-level summary without per-request details.
 */
export interface TokenSummary {
  /** Total number of tokens used (input + output + cache). */
  total_tokens: number;

  /** Total cost in USD for all token usage. */
  total_cost_usd: number;
}

/**
 * Detailed token usage information for a single LLM request.
 * Tracks input, output, and cache tokens separately for cost analysis.
 */
export interface TokenUsage {
  /** ID of the workflow this usage belongs to. */
  workflow_id: string;

  /** Name of the agent that made this request (e.g., 'architect', 'developer'). */
  agent: string;

  /** Name of the LLM model used (e.g., 'claude-sonnet-4-5', 'gpt-4'). */
  model: string;

  /** Number of input tokens sent to the model. */
  input_tokens: number;

  /** Number of output tokens generated by the model. */
  output_tokens: number;

  /** Number of tokens read from the prompt cache (not billed at full rate). */
  cache_read_tokens: number;

  /** Number of tokens written to the prompt cache. */
  cache_creation_tokens: number;

  /** Calculated cost in USD for this request, or null if pricing unavailable. */
  cost_usd: number | null;

  /** ISO 8601 timestamp when this request was made. */
  timestamp: string;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Response payload for listing workflows with pagination support.
 * Used by GET /api/workflows endpoint.
 *
 * @example
 * ```typescript
 * const response: WorkflowListResponse = {
 *   workflows: [{ id: 'wf1', issue_id: 'ISSUE-1', ... }],
 *   total: 42,
 *   cursor: 'eyJsYXN0X2lkIjogIndmMSJ9',
 *   has_more: true
 * };
 * ```
 */
export interface WorkflowListResponse {
  /** Array of workflow summaries for the current page. */
  workflows: WorkflowSummary[];

  /** Total number of workflows across all pages. */
  total: number;

  /** Opaque cursor token for fetching the next page, or null if no more pages. */
  cursor: string | null;

  /** Whether there are more workflows beyond this page. */
  has_more: boolean;
}

/**
 * Response payload for retrieving a single workflow's details.
 * Used by GET /api/workflows/:id endpoint.
 */
export type WorkflowDetailResponse = WorkflowDetail;

/**
 * Standard error response format for all API endpoints.
 * Returned with appropriate HTTP error status codes (4xx, 5xx).
 *
 * @example
 * ```typescript
 * const error: ErrorResponse = {
 *   error: 'Workflow not found',
 *   code: 'WORKFLOW_NOT_FOUND',
 *   details: { workflow_id: 'wf123' }
 * };
 * ```
 */
export interface ErrorResponse {
  /** Human-readable error message. */
  error: string;

  /** Machine-readable error code for programmatic handling. */
  code: string;

  /** Optional additional context about the error. */
  details?: Record<string, unknown>;
}

/**
 * Request payload for starting a new workflow.
 * Used by POST /api/workflows endpoint.
 *
 * @example
 * ```typescript
 * const request: StartWorkflowRequest = {
 *   issue_id: 'JIRA-123',
 *   profile: 'work',
 *   worktree_path: '/tmp/worktrees/jira-123'
 * };
 * ```
 */
export interface StartWorkflowRequest {
  /** Issue ID from the tracking system to work on. */
  issue_id: string;

  /** Optional profile name from settings.amelia.yaml (defaults to active profile). */
  profile?: string;

  /** Optional custom path for the git worktree (auto-generated if not provided). */
  worktree_path?: string;
}

/**
 * Request payload for rejecting a plan or review.
 * Used by POST /api/workflows/:id/reject endpoint.
 */
export interface RejectRequest {
  /** Human feedback explaining why the plan or changes were rejected. */
  feedback: string;
}

/**
 * Resolution action for blockers.
 * - `skip`: Skip the blocked step and continue
 * - `retry`: Retry the blocked step
 * - `abort`: Abort the workflow without reverting
 * - `abort_revert`: Abort the workflow and revert changes
 * - `fix`: Provide a fix instruction for the agent
 */
export type BlockerResolutionAction = 'skip' | 'retry' | 'abort' | 'abort_revert' | 'fix';

/**
 * Request payload for resolving a blocker.
 * Used by POST /api/workflows/:id/resolve-blocker endpoint.
 */
export interface BlockerResolutionRequest {
  /** Resolution action to take. */
  action: BlockerResolutionAction;
  /** Optional feedback or fix instruction. */
  feedback?: string | null;
}

/**
 * Request payload for batch approval.
 * Used by POST /api/workflows/:id/approve-batch endpoint.
 */
export interface BatchApprovalRequest {
  /** Whether to approve or reject the batch. */
  approved: boolean;
  /** Optional feedback for rejection. */
  feedback?: string | null;
}

// ============================================================================
// WebSocket Message Types
// ============================================================================

/**
 * Messages sent from the server to the dashboard client over WebSocket.
 * The dashboard receives these messages to update the UI in real-time.
 *
 * @example
 * ```typescript
 * // Ping message (keepalive)
 * const ping: WebSocketMessage = { type: 'ping' };
 *
 * // Event message
 * const event: WebSocketMessage = {
 *   type: 'event',
 *   payload: { id: 'evt1', workflow_id: 'wf1', ... }
 * };
 *
 * // Backfill complete
 * const backfill: WebSocketMessage = { type: 'backfill_complete', count: 10 };
 * ```
 */
export type WebSocketMessage =
  | { type: 'ping' }
  | { type: 'event'; payload: WorkflowEvent }
  | { type: 'stream'; payload: StreamEvent }
  | { type: 'backfill_complete'; count: number }
  | { type: 'backfill_expired'; message: string };

/**
 * Messages sent from the dashboard client to the server over WebSocket.
 * The dashboard sends these messages to control subscriptions and respond to pings.
 *
 * @example
 * ```typescript
 * // Subscribe to a specific workflow
 * const subscribe: WebSocketClientMessage = {
 *   type: 'subscribe',
 *   workflow_id: 'wf123'
 * };
 *
 * // Subscribe to all workflows
 * const subscribeAll: WebSocketClientMessage = { type: 'subscribe_all' };
 *
 * // Respond to ping
 * const pong: WebSocketClientMessage = { type: 'pong' };
 * ```
 */
export type WebSocketClientMessage =
  | { type: 'subscribe'; workflow_id: string }
  | { type: 'unsubscribe'; workflow_id: string }
  | { type: 'subscribe_all' }
  | { type: 'pong' };

// ============================================================================
// Stream Event Types
// ============================================================================

/**
 * Types of stream events emitted during Claude LLM execution.
 * These events provide real-time insight into agent reasoning and tool usage.
 *
 * @example
 * ```typescript
 * const eventType: StreamEventType = StreamEventType.CLAUDE_THINKING;
 * ```
 */
export const StreamEventType = {
  CLAUDE_THINKING: 'claude_thinking',
  CLAUDE_TOOL_CALL: 'claude_tool_call',
  CLAUDE_TOOL_RESULT: 'claude_tool_result',
  AGENT_OUTPUT: 'agent_output',
} as const;

export type StreamEventType =
  (typeof StreamEventType)[keyof typeof StreamEventType];

/**
 * A single stream event emitted during Claude LLM execution.
 * Stream events are emitted in real-time via WebSocket to show agent reasoning.
 *
 * Note: Uses `subtype` instead of `type` to avoid collision with the wrapper
 * message's `type: "stream"` field in WebSocket messages.
 *
 * @example
 * ```typescript
 * // Thinking event
 * const thinking: StreamEvent = {
 *   subtype: 'claude_thinking',
 *   content: 'I need to analyze the requirements...',
 *   timestamp: '2025-12-13T10:30:00Z',
 *   agent: 'architect',
 *   workflow_id: 'wf123',
 *   tool_name: null,
 *   tool_input: null
 * };
 *
 * // Tool call event
 * const toolCall: StreamEvent = {
 *   subtype: 'claude_tool_call',
 *   content: null,
 *   timestamp: '2025-12-13T10:30:01Z',
 *   agent: 'developer',
 *   workflow_id: 'wf123',
 *   tool_name: 'read_file',
 *   tool_input: { path: '/src/main.py' }
 * };
 * ```
 */
export interface StreamEvent {
  /** Unique identifier for this event (UUID). */
  id: string;

  /** Subtype of stream event (uses subtype to avoid collision with message type). */
  subtype: StreamEventType;

  /** Text content for thinking/output events, null for tool calls. */
  content: string | null;

  /** ISO 8601 timestamp when the event was emitted. */
  timestamp: string;

  /** Name of the agent that emitted this event (e.g., 'architect', 'developer'). */
  agent: string;

  /** ID of the workflow this event belongs to. */
  workflow_id: string;

  /** Name of the tool being called, null for non-tool events. */
  tool_name: string | null;

  /** Input parameters for the tool call, null for non-tool events. */
  tool_input: Record<string, unknown> | null;
}

// ============================================================================
// UI State Types
// ============================================================================

/**
 * WebSocket connection state for the dashboard.
 * Tracks the current connection status and any errors that occurred.
 *
 * @example
 * ```typescript
 * // Successfully connected
 * const state: ConnectionState = { status: 'connected' };
 *
 * // Connection failed
 * const failedState: ConnectionState = {
 *   status: 'disconnected',
 *   error: 'Failed to connect to server'
 * };
 * ```
 */
export interface ConnectionState {
  /** Current WebSocket connection status. */
  status: 'connected' | 'disconnected' | 'connecting';

  /** Error message if connection failed, otherwise undefined. */
  error?: string;
}

// ============================================================================
// Batch Execution Types (Intelligent Execution Model)
// ============================================================================

/**
 * Risk level for execution steps.
 * - `low`: Safe operations, minimal risk of side effects
 * - `medium`: Moderate risk, may have side effects
 * - `high`: High risk, requires careful review
 */
export type RiskLevel = 'low' | 'medium' | 'high';

/**
 * Type of action a step performs.
 * - `code`: Write or modify code in a file
 * - `command`: Execute a shell command
 * - `validation`: Run a validation check
 * - `manual`: Requires manual human action
 */
export type ActionType = 'code' | 'command' | 'validation' | 'manual';

/**
 * Status of a single step in a StepResult (returned from API).
 * Only includes statuses for steps that have been executed.
 * - `completed`: Finished successfully
 * - `skipped`: Skipped due to dependency failure or user request
 * - `failed`: Failed with an error
 * - `cancelled`: Cancelled by user
 */
export type StepStatus = 'completed' | 'skipped' | 'failed' | 'cancelled';

/**
 * UI-specific step status including states for steps not yet executed.
 * Used for visualization in React Flow nodes.
 * - `pending`: Not yet started
 * - `in_progress`: Currently executing
 * - Plus all StepStatus values
 */
export type StepStatusUI = 'pending' | 'in_progress' | StepStatus;

/**
 * Status of a batch execution (returned from API).
 * Only includes statuses for batches that have been executed.
 * - `complete`: All steps completed successfully
 * - `blocked`: Execution blocked, needs human help
 * - `partial`: Some steps completed before blocking/failure
 */
export type BatchStatus = 'complete' | 'blocked' | 'partial';

/**
 * UI-specific batch status including states for batches not yet executed.
 * Used for visualization in React Flow nodes.
 * - `pending`: Not yet started
 * - `in_progress`: Currently executing
 * - Plus all BatchStatus values
 */
export type BatchStatusUI = 'pending' | 'in_progress' | BatchStatus;

/**
 * Type of blocker encountered during execution.
 */
export type BlockerType =
  | 'command_failed'
  | 'validation_failed'
  | 'needs_judgment'
  | 'unexpected_state'
  | 'dependency_skipped'
  | 'user_cancelled';

/**
 * Developer agent execution status.
 * - `executing`: Developer is actively executing steps
 * - `batch_complete`: A batch finished, ready for checkpoint
 * - `blocked`: Execution blocked, needs human help
 * - `all_done`: All batches completed successfully
 */
export type DeveloperStatus = 'executing' | 'batch_complete' | 'blocked' | 'all_done';

/**
 * A single step in an execution plan.
 * Contains all information needed to execute and validate the step.
 */
export interface PlanStep {
  /** Unique identifier for tracking. */
  id: string;
  /** Human-readable description. */
  description: string;
  /** Type of action (code, command, validation, manual). */
  action_type: ActionType;

  // For code actions
  /** File path for code actions. */
  file_path?: string | null;
  /** Exact code or diff for code actions. */
  code_change?: string | null;

  // For command actions
  /** Shell command to execute. */
  command?: string | null;
  /** Working directory (relative to repo root). */
  cwd?: string | null;
  /** Alternative commands to try if primary fails. */
  fallback_commands?: string[];

  // Validation
  /** Expected exit code (primary validation). */
  expect_exit_code?: number;
  /** Regex for stdout (secondary, stripped of ANSI). */
  expected_output_pattern?: string | null;
  /** Command to run for validation actions. */
  validation_command?: string | null;
  /** Description of what success looks like. */
  success_criteria?: string | null;

  // Execution hints
  /** Risk level (low, medium, high). */
  risk_level?: RiskLevel;
  /** Estimated time to complete (2-5 min typically). */
  estimated_minutes?: number;
  /** Whether step needs human review. */
  requires_human_judgment?: boolean;

  // Dependencies
  /** Step IDs this depends on. */
  depends_on?: string[];

  // TDD markers
  /** Whether this is a test step. */
  is_test_step?: boolean;
  /** Step ID this validates. */
  validates_step?: string | null;
}

/**
 * A batch of steps to execute before checkpoint.
 * Architect defines batches based on semantic grouping.
 */
export interface ExecutionBatch {
  /** Sequential batch number. */
  batch_number: number;
  /** Steps in this batch. */
  steps: PlanStep[];
  /** Overall risk level of the batch. */
  risk_summary: RiskLevel;
  /** Optional description of why these steps are grouped. */
  description?: string;
}

/**
 * Complete execution plan with batched execution.
 * Created by Architect, consumed by Developer.
 */
export interface ExecutionPlan {
  /** Overall goal or objective. */
  goal: string;
  /** Sequence of execution batches. */
  batches: ExecutionBatch[];
  /** Total estimated time for all batches. */
  total_estimated_minutes: number;
  /** Whether to use TDD approach. */
  tdd_approach?: boolean;
}

/**
 * Report when execution is blocked.
 * Contains information about the blocker and suggested resolutions.
 */
export interface BlockerReport {
  /** ID of the step that blocked. */
  step_id: string;
  /** Description of the blocked step. */
  step_description: string;
  /** Type of blocker encountered. */
  blocker_type: BlockerType;
  /** Error message describing the blocker. */
  error_message: string;
  /** Actions the agent already tried. */
  attempted_actions: string[];
  /** Agent's suggestions for human (labeled as AI suggestions in UI). */
  suggested_resolutions: string[];
}

/**
 * Result of executing a single step.
 */
export interface StepResult {
  /** ID of the step. */
  step_id: string;
  /** Execution status. */
  status: StepStatus;
  /** Truncated command output. */
  output?: string | null;
  /** Error message if failed. */
  error?: string | null;
  /** Actual command run (may differ from plan if fallback). */
  executed_command?: string | null;
  /** Time taken to execute in seconds. */
  duration_seconds?: number;
  /** Whether user cancelled the step. */
  cancelled_by_user?: boolean;
}

/**
 * Result of executing a batch.
 */
export interface BatchResult {
  /** The batch number. */
  batch_number: number;
  /** Batch execution status. */
  status: BatchStatus;
  /** Results for completed steps. */
  completed_steps: StepResult[];
  /** Blocker report if execution was blocked. */
  blocker?: BlockerReport | null;
}

/**
 * Git snapshot for batch-level rollback.
 */
export interface GitSnapshot {
  /** HEAD commit hash before batch started. */
  head_commit: string;
  /** Files that were dirty before batch started. */
  dirty_files: string[];
  /** Git stash reference if changes were stashed. */
  stash_ref?: string | null;
}

/**
 * Batch approval record.
 */
export interface BatchApproval {
  /** The batch number. */
  batch_number: number;
  /** Whether the batch was approved. */
  approved: boolean;
  /** Optional feedback from reviewer. */
  feedback?: string | null;
  /** ISO 8601 timestamp when approved. */
  approved_at: string;
}
