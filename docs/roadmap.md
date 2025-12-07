# Amelia Roadmap

> **Vision:** Complete end-to-end workflow control without ever opening GitHub, Jira, or any tracker web UI—with agents that maintain context across sessions and verify their own work. Built on the assumption that LLMs will continually improve, so Amelia automatically gets better as models advance.

## Design Principles

These principles, informed by [Anthropic's research on effective agent harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), guide all roadmap decisions:

1. **Model Improvement as Tailwind** - Build features assuming LLMs will get smarter; prefer prompts over code, delegation over hardcoding
2. **Structured Handoffs** - Agents working across sessions need explicit state transfer mechanisms
3. **One Feature at a Time** - Context exhaustion is the enemy; focused work with clear completion criteria
4. **Verify Before Declaring Done** - Agents must test as humans would, not just claim completion
5. **Incremental Accountability** - Every change is committed, logged, and recoverable
6. **Environment as Truth** - Git history and artifacts are the source of truth, not agent memory

---

## Phase 1: Core Orchestration [Complete]

*Multi-agent coordination with human oversight*

The foundation: specialized AI agents working in sequence with explicit approval gates before any code changes ship.

**Key Capabilities:**
- Agent orchestration via state machine (Architect → Developer → Reviewer loop)
- Human approval gates before execution proceeds
- Multi-driver support for API and CLI-based LLM access
- Jira and GitHub issue tracker integrations

---

## Phase 2: Web Dashboard [In Progress]

*Observable orchestration through a local web interface*

A browser-based dashboard that provides visibility into workflow state, enables approvals, and streams real-time updates.

**Key Capabilities:**
- FastAPI server with SQLite persistence
- Workflow and task state tracking with event history
- REST API for workflow management (create, list, approve, reject, cancel)
- React dashboard with workflow visualization
- Real-time updates via WebSocket events

---

## Phase 3: Session Continuity [Planned]

*Structured handoff mechanisms for long-running work*

Long-running agents fail across context windows because each session starts fresh. This phase adds explicit progress tracking so any agent can resume where another left off.

**Key Capabilities:**
- Machine-readable progress artifacts persisted to the repository
- Session kickoff protocol (verify environment, review history, select next feature)
- One-feature-per-session discipline to prevent context exhaustion
- Mergeable state guarantee—every session ends with passing tests and committed changes

See [Session Continuity Design](brainstorming/) for detailed specification.

---

## Phase 4: Verification Framework [Planned]

*Agents must verify before declaring done*

A major failure mode: agents mark features complete without proper verification. This phase adds browser-based end-to-end testing so agents test as humans would.

**Key Capabilities:**
- Browser automation integration (Puppeteer/Playwright) for agents
- Pre-completion verification: run happy paths, check for errors, capture evidence
- Feature tracking with explicit passing/failing status
- Health checks at session start—tests must pass before new work begins

---

## Phase 5: Bidirectional Tracker Sync [Planned]

*Eliminate tracker web UI entirely*

Full issue lifecycle management from the command line: create, update, transition, comment, and close issues without opening a browser.

**Key Capabilities:**
- Create and update issues via CLI
- Transition issue status (To Do → In Progress → Review → Done)
- Add comments and close with resolution summary
- Label, milestone, and related-issue management
- Bidirectional sync with conflict resolution

---

## Phase 6: Pull Request Lifecycle [Planned]

*Eliminate GitHub web for code review*

Complete PR management from creation through merge, including handling reviewer feedback and automated merge when checks pass.

**Key Capabilities:**
- Generate PRs from task metadata with auto-assigned reviewers
- Fetch and address review comments with fixup commits
- Monitor CI status and auto-merge when approved
- Automatic branch cleanup post-merge

---

## Phase 7: Quality Gates [Planned]

*Objective verification before subjective review*

Automated gates that must pass before code reaches human reviewers: linting, type checking, tests, security scans, and architecture rules.

**Key Capabilities:**
- Pre-review automation (lint, typecheck, test, security scan)
- Configurable coverage thresholds with regression tracking
- Architecture rules (import restrictions, module boundaries, naming conventions)
- Specialized reviewers (Security, Performance, Accessibility) running in parallel

---

## Phase 8: Parallel Execution [Planned]

*Multiply throughput without proportional attention cost*

Run multiple independent workflows concurrently, each isolated in its own worktree, with a unified dashboard view.

**Key Capabilities:**
- Concurrent workflows on independent issues
- DAG-aware task scheduling within workflows
- Resource management (LLM rate limiting, compute allocation)
- Fire-and-forget execution with notifications on completion

---

## Phase 9: Chat Integration [Planned]

*Async and mobile workflow management*

Manage workflows via Slack or Discord: receive status updates, approve plans, and monitor progress from your phone.

**Key Capabilities:**
- Slack DM interface with approval action buttons
- Discord bot commands and role-based permissions
- Configurable notification verbosity and quiet hours
- Thread-per-workflow isolation

---

## Phase 10: Continuous Improvement [Planned]

*Quality flywheel that compounds over time*

Track outcomes, learn from patterns, and automatically improve agent behavior based on historical performance.

**Key Capabilities:**
- Success/failure rate tracking per agent, project, and task type
- Reviewer pattern detection (preemptively address common feedback)
- Project-specific knowledge base (idioms, pitfalls, architectural decisions)
- Prompt refinement via A/B testing with benchmark suite

---

## Phase 11: Spec Builder [Planned]

*Local NotebookLM for technical design documents*

A document-assisted design tool: upload reference materials, explore them through guided chat, and generate structured specs that feed directly into the Architect.

**Key Capabilities:**
- Document ingestion (PDF, DOCX, PPTX, Markdown, HTML)
- Semantic search with source citations
- Section-by-section spec generation from templates
- Dashboard integration with chat interface and spec preview

See [Spec Builder Design](brainstorming/2025-12-05-spec-builder-design.md) for detailed specification.

---

## Phase 12: Debate Mode [Planned]

*Multi-agent deliberation for design decisions*

When facing complex decisions without clear answers, spawn multiple agents with assigned perspectives to argue different viewpoints, moderated by a Judge that synthesizes a recommendation.

**Key Capabilities:**
- Moderator analyzes prompts and assigns relevant perspectives
- Parallel debate rounds with convergence detection
- Human checkpoints for guidance injection
- Synthesis documents with recommendations, confidence levels, and caveats

See [Debate Mode Design](brainstorming/2025-12-05-debate-mode-design.md) for detailed specification.

---

## Phase 13: Knowledge Library [Planned]

*Co-learning system where developers and agents share framework knowledge*

A shared knowledge base that helps developers learn frameworks while providing agents with documentation context for better code generation.

**Key Capabilities:**
- Framework documentation ingestion and indexing
- Chat-based Q&A grounded in official docs
- Contextual code explanations ("Explain" button on agent-generated code)
- Agent RAG integration for pertinent retrieval during tasks

See [Knowledge Library Design](brainstorming/2025-12-06-knowledge-library-design.md) for detailed specification.

---

## Phase 14: Capitalization Tracking [Planned]

*Attribute engineering work to initiatives for financial reporting*

Map PRs and issues to capitalizable initiatives, estimate engineering hours from workflow execution, and produce auditable reports for finance.

**Key Capabilities:**
- Initiative resolution from JIRA Epics or GitHub Projects
- Hours estimation from workflow execution timestamps
- OPEX vs CAPEX classification per initiative
- CLI and dashboard reporting with full audit trails

See [Capitalization Tracking Design](brainstorming/2025-12-07-capex-tracking-design.md) for detailed specification.

---

## Phase 15: Cloud Deployment [Planned]

*Parallel workflow execution in the cloud*

Deploy Amelia to AWS to enable parallel workflow execution without local resource limitations, while preserving local-only mode as the default.

**Key Capabilities:**
- Multiple workflows running in parallel (not limited by local resources)
- Thin CLI client for submitting and monitoring workflows
- Web dashboard connectivity to cloud backend
- OAuth-based authentication with GitHub

See [Cloud Deployment Design](brainstorming/2025-12-06-aws-agentcore-deployment-design.md) for detailed specification.

---

## References

- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) - Anthropic's research on session continuity patterns
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - Agent design principles
