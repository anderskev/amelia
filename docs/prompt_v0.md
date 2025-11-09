# Amelia

## Problem

I am a software engineer who manages multiple AI agent workflows in parallel and I need a user interface where I can manage, monitor, debug and control these workflows. There should be a web application and a command line application, both sharing a common backend.

The application enables kicking off Claude Code agents locally to perform workflows for writing technical design docs, discovery docs, planning docs, bug fixing, testing, and code implementation. We will have many different agents with different system prompts representing different parts of the software development lifecycle, including product management functions.

The UI should show realtime updates from running agents such as the work they are doing, summary of what is done so far, and what is upcoming. The UI should also show how different agents are ordered in a workflow.

## Core Workflow

The primary workflow this application needs to support is:

1. **Observe Phase**: Download multiple documents from Google Docs and upload them to the RAG database via the web UI
2. **Orient Phase**: Use the web UI to kick off Claude Code agents to perform discovery for features mentioned in the uploaded documents. The agents will use documents in the RAG database as well as local code repositories to develop comprehensive technical design documents in markdown
3. **Decide Phase**: Review the generated technical design documents and planning phase documents. While agents work, progress and summary updates should be visible in the web UI
4. **Act Phase**:
   - Use the web UI to kick off agents for the software development lifecycle
   - Agents plan out implementation of the design from planning phase documents, showing progress updates in the web UI
   - Trigger code implementation Claude Code agents and testing/validation agents
   - Manage git worktrees through the web UI

## Frontend Web

- use "A sidebar that collapses to icons" from https://ui.shadcn.com/blocks/sidebar#sidebar-07
- sidebar header should just contain "Amelia" logo text Momo Trust Display 40px
- sidebar groups should correspond to phases: observe, orient, design, acta
- additional sidebar group: configuration

### Frontend Web Tech Stack

- react router v7, framework mode, single-page application
- shadcn/ui following theme in @docs/global.css
- ai-elements for all llm chat ui https://ai-sdk.dev/elements
- vite

### Observe

- collapsible menu items: Local RAG, Remote Sources
- Local RAG
  - Upload
  - Documents
  - Memories
- Remote Sources
  - Web Scraper (coming soon)
  - Scheduled Jobs (coming soon)

#### Local RAG - Upload

- accepts markdown, pdf, txt
- uses shadcn Input https://ui.shadcn.com/docs/components/input
- uses shadcn Progress https://ui.shadcn.com/docs/components/progress

#### Local RAG - Documents

- show documents currently in RAG database, use Data Table https://ui.shadcn.com/docs/components/data-table
- can filter by filename, 
- can sort by filename, created, size

#### Local RAG - Memories

- show all memories in Data Table https://ui.shadcn.com/docs/components/data-table
- columns: title, tags (as badges), importance level, created date, last used date
- filter by tags (multi-select dropdown)
- search by content (full-text search)
- sort by date created, last used, importance, or title
- actions per memory: edit, archive, delete, pin/unpin
- "Add Memory" button opens creation form
- creation form fields:
  - title (required, text input)
  - content/description (required, textarea with markdown preview)
  - tags (multi-select combobox, supports creating new tags)
  - importance level (optional dropdown: Low/Medium/High/Critical)
  - "pin to all conversations" checkbox

### Orient

- collapsible menu items: Chat, Prioritize, Inform
- Chat
  - New Conversation
  - Old Conversation 1
  - Old Conversation 2
  - ...
  - Conversation History
- Priotitize
  - Coming Soon
- Inform
  - Documents
  - Memories
  - Remote Sources

#### Chat - New/Existing Conversation

- Support blank/new state or loading historic chat
- Should use ai-elements components, example: https://ai-sdk.dev/elements/examples/chatbot
- should support reasoning: https://ai-sdk.dev/elements/components/reasoning
- should use shimmer: https://ai-sdk.dev/elements/components/shimmer
- can upload markdown or text files to chat
- should show current context information using https://ai-sdk.dev/elements/components/context
- agent messages should have action buttons to: retry, copy, add to long term memory
- agent messages should support markdown rendering: https://ai-sdk.dev/elements/components/message
- should replicate features of popular LLM chat interfaces: "thinking" indicator, streaming chunks as they arrive, copy buttons, markdown display
- chat should be configurable to use either a local instance of Claude Code (via Agent Client Protocol) or stream messages from OpenRouter
- memory review side panel:
  - appears as notification when agent suggests new memories during conversation
  - shows extracted memory with editable title, content, and auto-suggested tags
  - actions: approve (saves as-is), edit (modify before saving), reject (dismiss)
  - multiple suggestions stack in panel, can review one at a time
  - unreviewed suggestions persist across sessions until addressed

#### Chat - Conversation History

- show conversation title, context window remaining (if available), cost (if available) date and time of last message in Data Table https://ui.shadcn.com/docs/components/data-table
- we can navigate to an old conversation from this view

### Decide

This collection of views is the workflow planning and queue management center. Users review generated artifacts (design docs, plans), configure workflow templates with minimal parameters, queue workflows for execution, and manage git worktrees for isolated development.

- collapsible menu items: Agent Workflows, Git Worktrees

#### Agent Workflows

**Workflow Templates Library:**
- Templates organized in categorized collapsible groups using shadcn Accordion:
  - **SDLC Workflows**: Requirements Analysis, Design, Implementation, Testing, Deployment
  - **Task Workflows**: Generate Design Doc, Implement Feature, Fix Bug, Write Tests, Refactor Code
  - **Composite Workflows**: Full Feature Development, Bug Fix End-to-End
- Each template card shows: name, description, estimated duration, required inputs
- Search/filter bar at top for finding templates quickly

**Starting a Workflow:**
- Click template opens configuration modal (shadcn Dialog)
- Essential parameters only (workflow-specific):
  - Workflow name/identifier (auto-generated, editable)
  - Target design doc / feature spec (dropdown from RAG docs)
  - Target branch/worktree (with "Create new worktree?" prompt if applicable)
  - Number of iterations (default: 1)
- Hybrid context system:
  - Essential inputs are explicit (user selects from dropdowns)
  - RAG documents and memories automatically available as MCP tools for agents to query on demand
  - Optional "Advanced" section to manually add/remove context sources
- Workflow suggests creating a new worktree for isolation (Yes/No prompt with smart naming: `worktree-{workflow-name}-{timestamp}`)
- User-controlled parallelism: checkbox "Allow parallel execution" (default: unchecked for safety)

**Workflow Queue:**
- Data table showing queued and recently completed workflows
- Columns: Status (queued/running/completed/failed), Workflow Name, Template Type, Created, Progress, Actions
- Status uses shadcn Badge component with color coding
- Progress shows: "Step 2 of 5 (40%)" for running workflows, "Queued" or "Completed"
- Actions: View Details, Start (if queued), Pause Dependencies, Cancel, Run Again
- Queue executes based on user-controlled parallelism settings
- Linear execution per workflow (Step 1 → 2 → 3), but multiple workflows can run in parallel if allowed

**Workflow Monitoring in Decide:**
- High-level status only (detailed monitoring in Act section's Operations Control)
- Each running workflow shows: current step, progress percentage, estimated time remaining, status indicator
- Click workflow row to see more details in expandable section

**Workflow Results:**
- Simple file links (no inline previews):
  - Generated files: [docs/design-2025-11-09.md](docs/design-2025-11-09.md), [tests/test_feature.py](tests/test_feature.py)
  - Git commits: "3 commits in worktree-feature-auth"
  - Status: "All tests passed ✓" or "2 tests failed ✗"
- Optional context passing:
  - Checkbox on completed workflow: "Use results as context for next workflow"
  - When checked, output files automatically added to next workflow's context
  - Default: unchecked (explicit opt-in)

**Workflow History:**
- Reproducibility-focused execution records for each workflow run
- Stores: complete parameter snapshot, execution trace (agent, step, duration, files), token usage, environment state (branch, worktree, commit SHA)
- "Replay" button to re-run with identical configuration
- History table filterable by: template type, date range, status, worktree

**Workflow Visualization:**
- Uses ai-elements workflow components https://ai-sdk.dev/elements/examples/workflow
- Shows step-by-step flow with progress indicators in expandable detail sections

#### Git Worktrees

**Worktrees View:**
- Data table showing all worktrees
- Columns: Name, Branch, Status (active/idle), Created, Last Activity, Associated Workflows, Actions
- Status badge: green (currently running workflow), gray (idle), blue (has uncommitted changes)
- Associated Workflows column shows which workflows are using/used this worktree
- Actions: Switch To, View Changes, Delete, Create New

**Worktree-Workflow Integration:**
- When starting workflows that modify code (Implementation, Testing, Refactor):
  - Modal prompts: "Create new worktree for isolation?"
  - Smart default naming: `worktree-{workflow-name}-{timestamp}`
  - Option to use existing worktree from dropdown
- Worktree creation integrated into workflow start process:
  - If "Yes, create new worktree" → creates worktree → queues workflow → workflow runs in that worktree
  - If "Use existing" → validates no conflicts → queues workflow
  - If "No worktree" (main branch) → shows warning → requires confirmation
- Worktrees automatically track which workflows ran in them for context

**Worktree Management Actions:**
- Create: Opens form with branch name, base branch, path (auto-generated)
- Switch: Changes active working directory context for CLI/local agents
- View Changes: Shows git diff summary and uncommitted files
- Delete: Validates no running workflows, prompts for merge/discard decision

### Act

This section provides detailed, real-time monitoring and control of executing workflows. Unlike the Decide section's high-level queue management, Act offers granular visibility into agent behavior, tool usage, and file changes as they happen.

- single menu item: Operations Control

#### Operations Control

**Main Layout:**
- Single unified scrollable view showing all running workflows with expandable sections
- Each workflow appears as a card with collapsible sections for different monitoring aspects
- WebSocket-powered near-realtime updates (acceptable small delays)
- Sticky header with global controls: "Pause All", "Resume All", filter/search running workflows

**Workflow Card Structure:**
Each running workflow card contains:
- Header: workflow name, current status badge (running/paused/error), elapsed time, estimated time remaining
- Linear step indicator showing completed (✓) → current (spinner) → upcoming (grayed) steps
- Collapsible sections: Agent Activity, File Changes, Tool Activity, Logs, Performance Metrics, Execution Controls

**Agent Activity Display:**
- Shows current agent's descriptive activity (e.g., "Code Implementation Agent: Writing tests for UserService")
- Medium-detail tracking: displays current file being worked on, current action, last tool used
- Example: "Editing src/services/UserService.ts - Writing test cases - Last: Read tool"
- Updates stream in real-time as agent progresses through tasks
- Activity history scrollable within expandable section

**Step Progress Visualization:**
- Uses ai-elements workflow component for overall linear flow visualization
- Each step shows: name, status (completed ✓/current spinner/pending), duration
- Current step expanded to show detailed substep breakdown with agent activities
- Completed steps show summary: duration, files affected, key outcomes
- Timestamps for step start/completion times
- Overall workflow progress: "Step 2 of 5 (40%)" with progress bar
- Per-step progress: granular substep completion percentage where applicable
- Estimated time remaining based on historical data from similar workflow runs

**File Changes Tracking:**
- Simple list of modified files with timestamps in collapsible section
- Each file entry shows: filename, operation badge (added/modified/deleted), timestamp
- Files grouped by workflow step for context
- Real-time updates as agent modifies files

**Tool Activity Monitoring:**
- Real-time tool feed streams each tool call as it happens
- Each tool entry shows: tool name, brief description, timestamp
- Examples: "Read: src/UserService.ts", "Bash: npm test", "Edit: src/UserService.ts"
- Feed is scrollable and auto-scrolls to latest activity
- Color-coded by tool type for quick scanning
- Collapsed by default, expandable section per workflow

**Agent Logs:**
- Stream agent logs similar to watching Claude Code in terminal
- Log entries show: timestamp, log level (info/warning/error), message
- Filter controls: by log level (info/warning/error) or agent type
- Search/find within logs
- Download logs button for full debugging session export
- Auto-scroll toggle (on by default, can disable for reviewing history)
- Logs viewable in expandable sections, collapsed by default

**Workflow Execution Control:**
Per-workflow control buttons in workflow card header:
- Pause: temporarily halt workflow execution (agent saves state)
- Resume: continue paused workflow from where it stopped
- Stop: terminate workflow completely (with confirmation dialog)
- View Full Logs: opens dedicated logs view/modal

Queue management (inherited from Decide, accessible here):
- Drag-and-drop reordering of queued workflows
- Bulk actions: pause all, resume all (in sticky header)

**Error Handling:**
When workflow encounters error:
- Workflow pauses automatically
- Error notification toast appears with severity level
- Error details displayed in workflow card with highlighted error badge
- User presented with action options:
  - Auto-retry (configurable attempts: 1-5, default 3)
  - Manual Fix & Resume (pause, wait for manual intervention)
  - Skip Step (with confirmation)
  - Abort Workflow (with confirmation)
- Error context shown: step name, error message, relevant logs, last successful action

**Performance Metrics:**
Comprehensive metrics shown in collapsible "Performance" section per workflow:
- Token Usage:
  - Input tokens / Output tokens (running totals)
  - Cost estimation based on model pricing
  - Per-step token breakdown (expandable)
  - Tokens-per-minute rate
- Execution Timing:
  - Overall workflow duration (elapsed time)
  - Per-step execution time with start/end timestamps
  - Time remaining estimate (based on historical averages)
  - Comparison to average duration for this template type (e.g., "15% faster than average")
- Performance Breakdown:
  - Step-by-step performance summary showing duration and token usage per step
  - Average tokens per tool call
  - Tool efficiency metrics (reads/writes/edits per minute)

**Notifications and Alerts:**
Configurable notification system (settings in Configuration > Settings):
- Default notifications (in-app toasts):
  - Workflow completion
  - Workflow failure/error
  - Error requiring user intervention
- Optional notifications (user toggles on/off):
  - Workflow start
  - Step completion
  - Warnings
  - Test results (pass/fail)
- Per-event configuration: choose which events trigger notifications

**UI Components:**
- Accordion (shadcn) for collapsible workflow card sections
- Badge (shadcn) for status indicators (running/paused/error/completed)
- Card (shadcn) for workflow containers
- Progress (shadcn) for step progress bars
- Button (shadcn) for control actions
- ScrollArea (shadcn) for logs and tool activity feeds
- Separator (shadcn) for visual section divisions
- Toast (shadcn) for notifications
- Dialog (shadcn) for confirmations (stop, skip step, error actions)
- ai-elements workflow components for step visualization

**Data Flow and Backend Integration:**
- WebSocket connection per browser session subscribes to workflow events
- Backend EventBus publishes updates: agent activity, step transitions, file changes, tool calls, logs, metrics
- Frontend receives events and updates relevant workflow card in real-time
- Acceptable small delays (100-500ms) between backend action and UI update
- Events include: workflow_started, step_started, step_completed, agent_activity, tool_called, file_modified, log_entry, error_occurred, workflow_completed
- Frontend maintains workflow state locally, reconciles with backend on reconnect
- Log streaming uses chunked transfer to handle high-volume output without overwhelming UI
- Running workflows stored in frontend state with unique IDs
- Collapsible sections remember expand/collapse state per workflow
- Auto-scroll preferences persisted in localStorage
- Filter/search settings maintained across page refreshes


### Configuration

- 2 menu items, not collapsible: Monitoring, Settings

#### Monitoring

- show current size of RAG database
- show graphs of token usage by hour,day, week, month: https://ui.shadcn.com/charts/area#charts
- show all time token usage
- health checks for backend

#### Settings

- username
- how long to retain chat history in db
- RAG document folder path
- openrouter api key
- chat mode (local or cloud)
- local chat agent (claude code via agent client protocol only option for now)
- cloud chat model (default to )

## Frontend Command Line

- all functionality of frontend web EXCEPT chat

### Frontend Command Line Stack

- ink https://github.com/vadimdemedes/ink

## Backend API

### Backend Tech Stack
- astral uv
- python >= 3.12
- fastapi >= 0.121.1
- postres >= with pgvector
- rich >= 14.1
- pydantic AI https://ai.pydantic.dev/
- langgraph >= 1.0.2 https://docs.langchain.com/oss/python/langgraph/overview
- langchain >= 1.0.2
- docling >= 2.61.1 https://docling-project.github.io/docling/reference/document_converter/
- agent client protocol https://github.com/agentclientprotocol/python-sdk

### Features

#### Agent Orchestration
- Controls and coordinates multiple Claude Code agents running locally via Agent Client Protocol
- Each agent has a specific system prompt for different SDLC phases (discovery, planning, implementation, testing, validation), or can use claude code default prompt
- Provides APIs for starting, stopping, pausing, and monitoring agents
- Tracks agent progress and status in real-time
- Manages agent workflows and execution order

**Workflow Execution:**
- Backend spawns Claude Code agents locally using Agent Client Protocol SDK
- Workflow queue manager respects user-controlled parallelism settings
- Each workflow executes steps linearly (Step 1 → 2 → 3)
- Agents receive minimal explicit context: workflow parameters (target doc, feature name, iteration count, worktree path)
- Agents have MCP tool access to:
  - RAG database query tool (semantic search on demand)
  - Memory system query tool (retrieve relevant memories as needed)
  - File system access within assigned worktree
- Agents query RAG/memories dynamically based on execution needs
- Progress updates published to EventBus → WebSocket pushes to frontend
- Workflow execution records stored for reproducibility: parameters, environment state, execution trace, token usage

#### Chat
- Can stream messages to OpenRouter using langchain_openai python library
- Uses Agent Client Protocol to interact with Claude Code running locally https://github.com/zed-industries/claude-code-acp
- Chats persisted based on configuration
- Supports both local Claude Code and cloud-based LLM models via OpenRouter

#### Local RAG
- Accepts multiple document formats: markdown, PDF, txt, HTML
- Uses either Ollama local embeddings or OpenRouter via openai/text-embedding-3-small model
- Provides document upload, storage, and retrieval capabilities
- Integrates with Claude Code agents to provide context from uploaded documents
- Supports website scraping to add content to RAG database (future)

#### Memory System
- Stores memories in Postgres with pgvector for semantic search
- Each memory has: id, title, content, tags (array), importance level, embedding vector, created_at, last_used_at, is_pinned, is_archived
- Generates embeddings using same model as RAG (Ollama local or OpenRouter text-embedding-3-small)
- Semantic search retrieves top-N most relevant memories based on conversation context
- Pinned memories always included in context regardless of relevance score
- LangGraph agent workflow analyzes conversation messages in real-time to identify facts, decisions, preferences worth preserving
- Generates memory suggestions with title, content, and suggested tags
- Sends suggestions to frontend via WebSocket/SSE for side panel notification
- Stores approved memories after user review
- Relevance-based context window management: calculates semantic similarity between conversation context and all active (non-archived) memories, includes only top-N most relevant
- Token budget awareness: tracks total tokens used by memories, adjusts N dynamically to stay within limits
- Manual management APIs: archive/unarchive, edit, delete, pin/unpin memories
- Tracks last_used_at timestamp when memory is included in agent context
- Supports short-term (conversation-scoped) and long-term (persistent) memory as described in https://docs.langchain.com/oss/python/langgraph/add-memory


## General Tech Principles

- use structured logging
- use Test Driven Development
- don't pin dependencies unless absolutely necessary, use >=
- entire stack (frontend and backend) should be runnable via docker-compose command
- we do not need performance monitoring beyond basic healthchecks
- we do not need observability or user accounts - this is an open source project run locally by software engineers
- strongly favor using pre-built components from ai-elements, shadcn, or Radix UI; only create custom components as a last resort
- use shadcn theme from [global.css](global.css)
- generally favor simple solutions over complex unless otherwise specified
- small delays between agent and UI are acceptable; realtime communication is not strictly required