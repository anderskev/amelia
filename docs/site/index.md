---
layout: home

hero:
  name: "Amelia"
  text: "Agentic Coding Orchestrator"
  tagline: A local AI orchestrator that coordinates specialized agents through a LangGraph state machine. Built for developers who want AI assistance with full control.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/usage
    - theme: alt
      text: Architecture
      link: /architecture/overview
    - theme: alt
      text: View on GitHub
      link: https://github.com/anderskev/amelia

features:
  - title: Multi-Agent Orchestration
    details: Architect plans, Developer executes, Reviewer validates. Coordinated through LangGraph with human approval gates.
    link: /architecture/overview
  - title: Driver Abstraction
    details: Switch between API calls (api:openai) and CLI wrappers (cli:claude) without code changes. Enterprise SSO compatible.
    link: /guide/configuration
  - title: Real-Time Dashboard
    details: Web UI with workflow visualization, activity logs, and approval controls via WebSocket.
    link: /guide/usage#dashboard
  - title: Design System
    details: Dark-first design tokens, diagram themes, and presentation templates for consistent project artifacts.
    link: /design-system/
  - title: Ideas & Research
    details: Exploratory designs created through brainstorming sessions. Transparency into what we're considering.
    link: /ideas/
  - title: 12-Factor Agents
    details: Built following the 12-Factor Agents methodology for production-ready agentic systems.
    link: /reference/12-factor-compliance

---

## Quick Start

```bash
# Install amelia globally
uv tool install git+https://github.com/anderskev/amelia.git

# Configure in your project
cat > settings.amelia.yaml << 'EOF'
active_profile: dev
profiles:
  dev:
    driver: api:openai
    tracker: github
EOF

# Generate a plan for an issue
amelia plan-only 123

# Or run the full workflow
amelia start 123
```

## How It Works

| Agent | Role | Output |
|-------|------|--------|
| **Architect** | Plans the work | TaskDAG with ordered tasks |
| **Developer** | Executes tasks | Code changes via tools |
| **Reviewer** | Validates changes | Approval or feedback |

The orchestrator loops Developer → Reviewer until changes are approved.

## Learn More

- [Usage Guide](/guide/usage) - CLI commands and API reference
- [Architecture](/architecture/overview) - Technical deep dive
- [Configuration](/guide/configuration) - Profile and driver setup
- [Roadmap](/reference/roadmap) - Where we're headed
