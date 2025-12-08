# Amelia Documentation

> **Amelia** is a local agentic coding orchestrator that coordinates specialized AI agents through a LangGraph state machine.

## Quick Links

| Document | Description |
|----------|-------------|
| [Usage Guide](usage.md) | CLI commands, API reference, and example workflows |
| [Architecture](architecture.md) | Technical deep-dive into components, data flow, and system design |
| [Concepts](concepts.md) | Core agentic AI concepts for engineers new to the system |
| [Configuration](configuration.md) | Complete reference for `settings.amelia.yaml` |
| [Roadmap](roadmap.md) | Project vision, phases, and planned features |
| [Benchmarking](benchmarking.md) | How to evaluate and iterate on LLM agents |
| [Data Model](data-model.md) | Database schema and state machine definitions |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

## Sections

### [Analysis](analysis/)

Evaluations of Amelia against industry frameworks and best practices.

- [12-Factor Agents Compliance](analysis/12-factor-agents-compliance.md) - Alignment with the 12-Factor Agents methodology

### [Brainstorming](brainstorming/)

Design explorations created through collaborative sessions. Ideas refined through discussion before implementation. See the [brainstorming index](brainstorming/README.md) for all documents.

### [Design](design/)

Visual mockups and prototypes for the dashboard UI.

- [Dashboard HTML Prototype](design/amelia-dashboard-dark.html) - Interactive dark-themed dashboard
- [Dashboard JSX Component](design/amelia-dashboard-dark.jsx) - React implementation of the design

### [Plans](plans/)

Active implementation plans for in-progress work. Temporary documents deleted after features merge.

- [Dashboard Setup](plans/phase-2.3-08-dashboard-setup.md) - React frontend with Vite and shadcn/ui
- [Zustand & WebSocket](plans/phase-2.3-09-zustand-websocket.md) - State management and real-time updates
- [Dashboard Components](plans/phase-2.3-10-dashboard-components.md) - UI components for workflow visualization
- [Web Dashboard Design](plans/2025-12-01-web-dashboard-design.md) - Overall dashboard architecture
- [Dashboard Integration](plans/2025-12-07-dashboard-integration.md) - Integration of dashboard with backend
- [Skill Creation Plan](plans/2025-12-06-skill-creation-plan.md) - Adding new skills to the system

### [Testing](testing/)

Manual testing procedures for features requiring human verification.

- [PR Test Plan](testing/pr-test-plan.md) - Current PR test plan (temporary, deleted after merge)

### [Archived](archived/)

Historical documentation from completed, superseded, or abandoned work.

- [001-agentic-orchestrator/](archived/001-agentic-orchestrator/) - Early orchestrator planning
- [speckit/](archived/speckit/) - Abandoned specification toolkit
- [gemini_web/](archived/gemini_web/) - Early Gemini integration experiments

## Document Lifecycle

```
Brainstorming → Roadmap → Plans → Implementation → Archive
```

1. **Brainstorming** - Exploratory design sessions refine ideas
2. **Roadmap** - Approved ideas become planned phases
3. **Plans** - Detailed implementation guides for active work
4. **Implementation** - Code is written, tests pass, PR merges
5. **Archive** - Plans move to archived/ for historical reference
