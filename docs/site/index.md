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
---

<TerminalHero />

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
