# AWS AgentCore Deployment Design

> **Status:** Draft
> **Date:** 2025-12-06
> **Author:** Brainstorming session

## Overview

Deploy Amelia to AWS AgentCore to enable parallel workflow execution in the cloud, with a thin local CLI client communicating with the deployed backend. Local web UI can also connect to the cloud backend.

## Goals

- Run multiple workflows in parallel (not limited by local resources)
- Thin CLI client for submitting and monitoring workflows
- Web UI connectivity to cloud backend
- Preserve existing local-only mode (no breaking changes)

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Communication | REST + WebSocket | Real-time updates, matches existing server patterns |
| Execution model | Agent-per-workflow | Natural isolation via AgentCore microVM, scales per-workflow |
| Human approval | Webhook + pre-approval option | Async by default, auto-approve for CI/CD pipelines |
| Code execution | Git worktree in Runtime | Full shell access, 8-hour sessions, git credentials via Identity |
| LLM drivers | Bedrock + direct APIs | Bedrock for AWS-native auth, direct APIs for flexibility |
| State management | Hybrid (AgentCore Memory + Aurora) | Hot state in Memory, historical data in Aurora for reporting |
| Authentication | GitHub OAuth via Cognito | Natural for developers, federated identity |
| Database | Aurora Serverless v2 | SQL flexibility, serverless scaling, smooth migration from SQLite |

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Clients                              │
│  ┌─────────────┐                           ┌─────────────┐       │
│  │  Thin CLI   │                           │   Web UI    │       │
│  │  (local)    │                           │  (local)    │       │
│  └──────┬──────┘                           └──────┬──────┘       │
└─────────┼────────────────────────────────────────┼───────────────┘
          │            REST + WebSocket            │
          └──────────────────┬─────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AWS Cloud (AgentCore)                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    API Gateway + ALB                        │  │
│  │                   (GitHub OAuth via Cognito)                │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Amelia Control Plane (ECS/Lambda)              │  │
│  │  • Workflow management    • WebSocket hub                   │  │
│  │  • Approval handling      • Event broadcasting              │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              AgentCore Runtime (per workflow)               │  │
│  │  • LangGraph orchestrator  • Git worktree execution         │  │
│  │  • Bedrock/API drivers     • 8-hour sessions                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  AgentCore  │  │   Aurora    │  │  AgentCore Observability │  │
│  │   Memory    │  │ Serverless  │  │   (CloudWatch + OTEL)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Key components:**

- **Thin CLI/Web UI**: Local clients that submit workflows and receive real-time updates
- **Control Plane**: Stateless service handling workflow lifecycle, approvals, and WebSocket connections
- **AgentCore Runtime**: Isolated execution environments (one per workflow) running the LangGraph orchestrator
- **Data Layer**: AgentCore Memory for hot state, Aurora for historical data

---

## Workflow Lifecycle

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  START  │────▶│   PENDING   │────▶│ IN_PROGRESS │────▶│  BLOCKED    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                           ▲                    │
                                           │    ┌───────────────┴───────────────┐
                                           │    ▼                               ▼
                                    ┌─────────────┐                     ┌─────────────┐
                                    │  APPROVED   │                     │  REJECTED   │
                                    └──────┬──────┘                     └──────┬──────┘
                                           │                                   │
                                           ▼                                   ▼
                                    ┌─────────────┐                     ┌─────────────┐
                                    │  COMPLETED  │                     │   FAILED    │
                                    └─────────────┘                     └─────────────┘
```

**Workflow steps:**

1. **Submit** (CLI/Web UI → Control Plane)
   - User submits issue ID + repo + profile config
   - Control Plane validates, creates workflow record in Aurora
   - Returns `workflow_id`, establishes WebSocket subscription

2. **Spawn Runtime** (Control Plane → AgentCore)
   - Control Plane invokes AgentCore Runtime with workflow payload
   - Runtime clones git repo, initializes LangGraph orchestrator
   - Architect agent generates plan

3. **Approval Gate** (Runtime → Control Plane → User)
   - Runtime stores state in AgentCore Memory, enters BLOCKED state
   - Control Plane emits `approval_required` event via WebSocket
   - User reviews plan in CLI/Web UI, submits approve/reject
   - **Pre-approval mode**: If enabled, auto-approves and continues

4. **Execution** (Runtime)
   - Developer agent executes tasks in git worktree
   - Reviewer agent reviews changes
   - Loop until approved or max iterations

5. **Completion** (Runtime → Control Plane → Aurora)
   - Final state synced to Aurora for historical record
   - WebSocket emits `workflow_completed` event
   - Runtime terminates, resources released

---

## Codebase Changes

**New packages to add:**

```
amelia/
├── cloud/                          # NEW - Cloud deployment layer
│   ├── __init__.py
│   ├── runtime_wrapper.py          # BedrockAgentCoreApp entrypoint
│   ├── control_plane/
│   │   ├── app.py                  # FastAPI control plane service
│   │   ├── websocket_hub.py        # WebSocket connection management
│   │   └── approval_handler.py     # Approval gate logic
│   └── auth/
│       └── github_oauth.py         # Cognito + GitHub OAuth
│
├── drivers/
│   ├── api/
│   │   ├── openai.py               # Existing
│   │   ├── anthropic.py            # NEW - Direct Anthropic API
│   │   └── bedrock.py              # NEW - Amazon Bedrock driver
│   └── ...
│
├── client/                         # MODIFY - Thin CLI client
│   ├── remote.py                   # NEW - Remote backend client
│   └── ...
│
└── memory/                         # NEW - Memory abstraction
    ├── base.py                     # MemoryInterface protocol
    ├── local.py                    # SQLite (existing behavior)
    └── agentcore.py                # AgentCore Memory adapter
```

**Key modifications to existing code:**

| File | Change |
|------|--------|
| `core/orchestrator.py` | Add async approval callback (replace `typer.confirm`) |
| `server/orchestrator/service.py` | Add AgentCore Runtime invocation |
| `drivers/factory.py` | Register new `api:bedrock`, `api:anthropic` drivers |
| `main.py` | Add `--remote` flag to use cloud backend |
| `config.py` | Add cloud deployment settings (region, auth) |

**What stays the same:**

- LangGraph state machine logic
- Agent implementations (Architect, Developer, Reviewer)
- TaskDAG and ExecutionState models
- Tracker integrations (Jira, GitHub)

---

## API Contracts

**Control Plane REST API:**

```
POST   /api/v1/workflows              # Start new workflow
GET    /api/v1/workflows              # List user's workflows
GET    /api/v1/workflows/{id}         # Get workflow details
POST   /api/v1/workflows/{id}/approve # Approve blocked workflow
POST   /api/v1/workflows/{id}/reject  # Reject with feedback
DELETE /api/v1/workflows/{id}         # Cancel running workflow

GET    /api/v1/auth/login             # Initiate GitHub OAuth
GET    /api/v1/auth/callback          # OAuth callback
POST   /api/v1/auth/refresh           # Refresh token
```

**WebSocket Events (server → client):**

```typescript
// Workflow lifecycle
{ type: "workflow_started",    workflow_id, issue_id, timestamp }
{ type: "workflow_blocked",    workflow_id, plan: TaskDAG, requires: "approval" }
{ type: "workflow_approved",   workflow_id, approved_by }
{ type: "workflow_completed",  workflow_id, result: "success" | "failed" }

// Real-time progress
{ type: "agent_started",  workflow_id, agent: "architect" | "developer" | "reviewer" }
{ type: "task_started",   workflow_id, task_id, description }
{ type: "task_completed", workflow_id, task_id, status: "completed" | "failed" }
{ type: "agent_message",  workflow_id, agent, content }  // Streaming output
```

**Thin CLI usage:**

```bash
# Start workflow (connects to cloud)
amelia start PROJ-123 --remote

# With pre-approval for CI/CD
amelia start PROJ-123 --remote --auto-approve

# List active workflows
amelia workflows list --remote

# Approve pending workflow
amelia workflows approve <workflow_id>

# Stream logs from running workflow
amelia workflows logs <workflow_id> --follow
```

---

## Infrastructure

**AWS Resources (via CDK/Terraform):**

```
┌─────────────────────────────────────────────────────────────────┐
│ VPC                                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Public Subnets                                               ││
│  │  • ALB (HTTPS termination)                                   ││
│  │  • NAT Gateway                                               ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Private Subnets                                              ││
│  │  • ECS Fargate (Control Plane)                               ││
│  │  • Aurora Serverless v2                                      ││
│  │  • AgentCore Runtime (via PrivateLink)                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘

Supporting Services:
  • Cognito User Pool (GitHub federation)
  • Secrets Manager (API keys, OAuth secrets)
  • CloudWatch (logs, metrics, OTEL traces)
  • ECR (container images)
  • S3 (artifact storage, workflow outputs)
```

**Environment configuration:**

```yaml
# settings.amelia.yaml (cloud profile)
profiles:
  cloud-prod:
    driver: "api:bedrock"
    tracker: "github"
    strategy: "single"
    cloud:
      region: "us-east-1"
      control_plane_url: "https://amelia.example.com"
      auto_approve: false
```

---

## Implementation Sequence

**Phase 1: Driver Layer**
- Add `api:bedrock` driver (Bedrock SDK integration)
- Add `api:anthropic` driver (direct Anthropic API)
- Register in `DriverFactory`
- Tests for both drivers

**Phase 2: Async Approval**
- Refactor `human_approval_node` to emit event + await callback
- Add `MemoryInterface` abstraction
- AgentCore Memory adapter
- Tests for approval flow

**Phase 3: Control Plane**
- FastAPI service with workflow CRUD
- WebSocket hub (extend existing `ConnectionManager`)
- GitHub OAuth via Cognito
- Aurora repository layer

**Phase 4: Runtime Wrapper**
- `BedrockAgentCoreApp` entrypoint wrapping LangGraph
- Git worktree initialization in Runtime
- State sync between AgentCore Memory ↔ Aurora

**Phase 5: Thin CLI**
- `RemoteClient` class for Control Plane communication
- `--remote` flag on existing commands
- `amelia workflows` subcommand group
- WebSocket event streaming

**Phase 6: Infrastructure**
- CDK stack for all AWS resources
- CI/CD pipeline for deployment
- Integration tests

Each phase builds on the previous. Dependency order, not calendar time.

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Runtime timeout (8hr limit) | Checkpoint state to Memory, emit `workflow_timeout` event, allow resume |
| Git clone fails | Retry with exponential backoff, fail workflow with clear error |
| LLM API errors | Retry transient errors (429, 5xx), fail on auth/validation errors |
| Approval timeout | Configurable timeout (default 24hr), auto-reject with notification |
| WebSocket disconnect | Client auto-reconnects, replays missed events from sequence number |
| Control Plane crash | Stateless design - ECS restarts, workflows continue in Runtime |
| Runtime crash | AgentCore handles restart, resume from last Memory checkpoint |

---

## Testing Strategy

| Layer | Approach |
|-------|----------|
| Drivers | Mock LLM responses, verify request formatting |
| Memory adapters | Integration tests against local + AgentCore Memory |
| Control Plane | FastAPI TestClient, mock AgentCore Runtime |
| Runtime wrapper | Local `agentcore dev` testing before deploy |
| End-to-end | Dedicated test AWS account, real AgentCore Runtime |
| CLI | Mock Control Plane responses, verify output formatting |

---

## Observability

```
Traces: CLI → Control Plane → Runtime → Agents → LLM
        └── correlation_id flows through all components

Metrics:
  • workflow_duration_seconds (histogram)
  • workflow_status_total (counter by status)
  • approval_wait_seconds (histogram)
  • llm_tokens_total (counter by model)
```

---

## References

- [AWS AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore Python SDK](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore Starter Toolkit](https://github.com/aws/bedrock-agentcore-starter-toolkit)
- [Amelia Architecture](../architecture.md)
