# VitePress Documentation Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate all existing Amelia documentation into the VitePress site, making it the single source of truth for project documentation.

**Architecture:** The VitePress site currently serves only the Design System. We'll expand it to include all project docs organized into logical sections: Guide (user docs), Architecture (technical docs), Ideas (brainstorming), Reference (roadmap, compliance), and Design System (existing). After migration, the old docs/ structure will be deprecated and the site will become the docs root.

**Tech Stack:** VitePress 1.x, Markdown, GitHub Pages

---

## Task 1: Create New Directory Structure

**Files:**
- Create: `docs/site/architecture/` directory
- Create: `docs/site/reference/` directory
- Create: `docs/site/ideas/` directory

**Step 1: Create the directories**

```bash
mkdir -p docs/site/architecture
mkdir -p docs/site/reference
mkdir -p docs/site/ideas
```

**Step 2: Verify directories exist**

Run: `ls -la docs/site/`
Expected: Shows `architecture/`, `reference/`, `ideas/` directories

**Step 3: Commit**

```bash
git add docs/site/
git commit -m "chore: create directory structure for docs migration"
```

---

## Task 2: Move Guide Documents

**Files:**
- Copy: `docs/usage.md` → `docs/site/guide/usage.md`
- Copy: `docs/configuration.md` → `docs/site/guide/configuration.md`
- Copy: `docs/troubleshooting.md` → `docs/site/guide/troubleshooting.md`

**Step 1: Copy usage.md and update links**

```bash
cp docs/usage.md docs/site/guide/usage.md
```

**Step 2: Copy configuration.md**

```bash
cp docs/configuration.md docs/site/guide/configuration.md
```

**Step 3: Copy troubleshooting.md**

```bash
cp docs/troubleshooting.md docs/site/guide/troubleshooting.md
```

**Step 4: Update internal links in usage.md**

Open `docs/site/guide/usage.md` and replace:
- `configuration.md` → `/guide/configuration`
- `troubleshooting.md` → `/guide/troubleshooting`
- `architecture.md` → `/architecture/overview`
- `concepts.md` → `/architecture/concepts`

**Step 5: Update internal links in configuration.md**

Open `docs/site/guide/configuration.md` and replace links similarly.

**Step 6: Update internal links in troubleshooting.md**

Open `docs/site/guide/troubleshooting.md` and replace links similarly.

**Step 7: Verify files exist**

Run: `ls -la docs/site/guide/`
Expected: Shows `usage.md`, `configuration.md`, `troubleshooting.md` alongside existing files

**Step 8: Commit**

```bash
git add docs/site/guide/
git commit -m "docs: migrate usage, configuration, troubleshooting to VitePress"
```

---

## Task 3: Move Architecture Documents

**Files:**
- Copy: `docs/architecture.md` → `docs/site/architecture/overview.md`
- Copy: `docs/concepts.md` → `docs/site/architecture/concepts.md`
- Copy: `docs/data-model.md` → `docs/site/architecture/data-model.md`

**Step 1: Copy architecture.md as overview.md**

```bash
cp docs/architecture.md docs/site/architecture/overview.md
```

**Step 2: Copy concepts.md**

```bash
cp docs/concepts.md docs/site/architecture/concepts.md
```

**Step 3: Copy data-model.md**

```bash
cp docs/data-model.md docs/site/architecture/data-model.md
```

**Step 4: Update internal links in overview.md**

Open `docs/site/architecture/overview.md` and replace:
- `concepts.md` → `/architecture/concepts`
- `data-model.md` → `/architecture/data-model`
- `usage.md` → `/guide/usage`
- `configuration.md` → `/guide/configuration`

**Step 5: Update internal links in concepts.md**

Open `docs/site/architecture/concepts.md` and replace links similarly.

**Step 6: Update internal links in data-model.md**

Open `docs/site/architecture/data-model.md` and replace links similarly.

**Step 7: Verify files exist**

Run: `ls -la docs/site/architecture/`
Expected: Shows `overview.md`, `concepts.md`, `data-model.md`

**Step 8: Commit**

```bash
git add docs/site/architecture/
git commit -m "docs: migrate architecture, concepts, data-model to VitePress"
```

---

## Task 4: Move Reference Documents

**Files:**
- Copy: `docs/roadmap.md` → `docs/site/reference/roadmap.md`
- Copy: `docs/benchmarking.md` → `docs/site/reference/benchmarking.md`
- Copy: `docs/analysis/12-factor-agents-compliance.md` → `docs/site/reference/12-factor-compliance.md`

**Step 1: Copy roadmap.md**

```bash
cp docs/roadmap.md docs/site/reference/roadmap.md
```

**Step 2: Copy benchmarking.md**

```bash
cp docs/benchmarking.md docs/site/reference/benchmarking.md
```

**Step 3: Copy 12-factor-agents-compliance.md**

```bash
cp docs/analysis/12-factor-agents-compliance.md docs/site/reference/12-factor-compliance.md
```

**Step 4: Update internal links in all three files**

Replace links to point to new VitePress paths.

**Step 5: Verify files exist**

Run: `ls -la docs/site/reference/`
Expected: Shows `roadmap.md`, `benchmarking.md`, `12-factor-compliance.md`

**Step 6: Commit**

```bash
git add docs/site/reference/
git commit -m "docs: migrate roadmap, benchmarking, 12-factor compliance to VitePress"
```

---

## Task 5: Create Ideas Section with Brainstorming Docs

**Files:**
- Create: `docs/site/ideas/index.md`
- Copy: `docs/brainstorming/2025-12-13-session-continuity-design.md` → `docs/site/ideas/session-continuity.md`
- Copy: `docs/brainstorming/2025-12-07-capex-tracking-design.md` → `docs/site/ideas/capex-tracking.md`
- Copy: `docs/brainstorming/2025-12-06-knowledge-library-design.md` → `docs/site/ideas/knowledge-library.md`
- Copy: `docs/brainstorming/2025-12-06-aws-agentcore-deployment-design.md` → `docs/site/ideas/aws-agentcore.md`
- Copy: `docs/brainstorming/2025-12-05-debate-mode-design.md` → `docs/site/ideas/debate-mode.md`
- Copy: `docs/brainstorming/2025-12-05-spec-builder-design.md` → `docs/site/ideas/spec-builder.md`
- Copy: `docs/brainstorming/2025-12-10-context-compiler-design.md` → `docs/site/ideas/context-compiler.md`
- Copy: `docs/brainstorming/2025-12-13-planning-workflow-variations.md` → `docs/site/ideas/planning-workflows.md`

**Step 1: Create ideas/index.md with disclaimer**

Create `docs/site/ideas/index.md`:

```markdown
# Ideas & Explorations

> **Note:** Documents in this section are exploratory designs created through brainstorming sessions. They represent ideas under consideration but **are not commitments**. Some may never be implemented, others may change significantly before implementation.

These documents are created using the [superpowers:brainstorming](https://github.com/obra/superpowers) skill in Claude Code, which provides structured exploration through Socratic questioning.

## Current Explorations

| Idea | Description | Status |
|------|-------------|--------|
| [Session Continuity](./session-continuity) | Structured handoff protocol for long-running workflows | Draft |
| [CAPEX Tracking](./capex-tracking) | Attribute engineering work to initiatives for financial reporting | Draft |
| [Knowledge Library](./knowledge-library) | Co-learning system for developers and agents | Draft |
| [AWS AgentCore](./aws-agentcore) | Deploy Amelia to AWS for parallel cloud execution | Draft |
| [Debate Mode](./debate-mode) | Multi-agent deliberation for design decisions | Draft |
| [Spec Builder](./spec-builder) | Document-assisted technical design tool | Draft |
| [Context Compiler](./context-compiler) | Intelligent context assembly for LLM prompts | Draft |
| [Planning Workflows](./planning-workflows) | Variations on the planning workflow | Draft |

## Lifecycle

```
Brainstorming Session → Idea Document (here) → Roadmap Item → Implementation Plan → Code
```

Ideas that mature may be added to the [Roadmap](/reference/roadmap) as planned features.
```

**Step 2: Copy brainstorming docs**

```bash
cp docs/brainstorming/2025-12-13-session-continuity-design.md docs/site/ideas/session-continuity.md
cp docs/brainstorming/2025-12-07-capex-tracking-design.md docs/site/ideas/capex-tracking.md
cp docs/brainstorming/2025-12-06-knowledge-library-design.md docs/site/ideas/knowledge-library.md
cp docs/brainstorming/2025-12-06-aws-agentcore-deployment-design.md docs/site/ideas/aws-agentcore.md
cp docs/brainstorming/2025-12-05-debate-mode-design.md docs/site/ideas/debate-mode.md
cp docs/brainstorming/2025-12-05-spec-builder-design.md docs/site/ideas/spec-builder.md
cp docs/brainstorming/2025-12-10-context-compiler-design.md docs/site/ideas/context-compiler.md
cp docs/brainstorming/2025-12-13-planning-workflow-variations.md docs/site/ideas/planning-workflows.md
```

**Step 3: Verify files exist**

Run: `ls -la docs/site/ideas/`
Expected: Shows `index.md` and all brainstorming documents

**Step 4: Commit**

```bash
git add docs/site/ideas/
git commit -m "docs: add ideas section with brainstorming documents"
```

---

## Task 6: Reorganize Design System Section

**Files:**
- Create: `docs/site/design-system/` directory
- Move: `docs/site/guide/color-system.md` → `docs/site/design-system/color-system.md`
- Move: `docs/site/guide/typography.md` → `docs/site/design-system/typography.md`
- Move: `docs/site/guide/diagrams.md` → `docs/site/design-system/diagrams.md`
- Move: `docs/site/guide/presentations.md` → `docs/site/design-system/presentations.md`
- Move: `docs/site/guide/getting-started.md` → `docs/site/design-system/index.md`

**Step 1: Create design-system directory**

```bash
mkdir -p docs/site/design-system
```

**Step 2: Move design system files**

```bash
mv docs/site/guide/color-system.md docs/site/design-system/
mv docs/site/guide/typography.md docs/site/design-system/
mv docs/site/guide/diagrams.md docs/site/design-system/
mv docs/site/guide/presentations.md docs/site/design-system/
mv docs/site/guide/getting-started.md docs/site/design-system/index.md
```

**Step 3: Update internal links in design-system/index.md**

Replace:
- `/guide/color-system` → `/design-system/color-system`
- `/guide/typography` → `/design-system/typography`
- `/guide/diagrams` → `/design-system/diagrams`
- `/guide/presentations` → `/design-system/presentations`
- `/api/tokens` → `/design-system/tokens`

**Step 4: Update internal links in other design-system files**

Update links in color-system.md, typography.md, diagrams.md, presentations.md.

**Step 5: Move api/tokens.md to design-system/**

```bash
mv docs/site/api/tokens.md docs/site/design-system/tokens.md
rmdir docs/site/api
```

**Step 6: Verify structure**

Run: `ls -la docs/site/design-system/`
Expected: Shows `index.md`, `color-system.md`, `typography.md`, `diagrams.md`, `presentations.md`, `tokens.md`

**Step 7: Commit**

```bash
git add docs/site/
git commit -m "docs: reorganize design system into dedicated section"
```

---

## Task 7: Create New Project Landing Page

**Files:**
- Modify: `docs/site/index.md`

**Step 1: Backup existing index.md**

```bash
cp docs/site/index.md docs/site/index.md.bak
```

**Step 2: Write new landing page**

Replace `docs/site/index.md` with:

```markdown
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
```

**Step 3: Delete backup**

```bash
rm docs/site/index.md.bak
```

**Step 4: Verify index.md**

Run: `cat docs/site/index.md | head -20`
Expected: Shows new hero with "Amelia" and "Agentic Coding Orchestrator"

**Step 5: Commit**

```bash
git add docs/site/index.md
git commit -m "docs: update landing page for full project documentation"
```

---

## Task 8: Update VitePress Configuration

**Files:**
- Modify: `docs/site/.vitepress/config.ts`

**Step 1: Read current config**

Review `docs/site/.vitepress/config.ts` to understand current structure.

**Step 2: Update config.ts**

Replace the configuration with:

```typescript
/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { defineConfig } from 'vitepress'

/**
 * VitePress Configuration
 *
 * Configures the Amelia documentation site with:
 * - Project-wide documentation
 * - Design system reference
 * - Ideas/brainstorming section
 * - Dark/light mode support
 */
export default defineConfig({
  title: 'Amelia',
  description: 'Documentation for the Amelia agentic coding orchestrator',

  // Base path for deployment
  base: '/amelia/',

  // Dark mode as default
  appearance: 'dark',

  // Theme configuration
  themeConfig: {
    // Use text title styled with Bebas Neue (see style.css)
    siteTitle: 'AMELIA',

    // Navigation menu
    nav: [
      { text: 'Guide', link: '/guide/usage' },
      { text: 'Architecture', link: '/architecture/overview' },
      { text: 'Design System', link: '/design-system/' },
      { text: 'Ideas', link: '/ideas/' },
      {
        text: 'Reference',
        items: [
          { text: 'Roadmap', link: '/reference/roadmap' },
          { text: 'Benchmarking', link: '/reference/benchmarking' },
          { text: '12-Factor Compliance', link: '/reference/12-factor-compliance' }
        ]
      },
      {
        text: 'Resources',
        items: [
          { text: 'GitHub', link: 'https://github.com/anderskev/amelia' },
          { text: 'License', link: 'https://github.com/anderskev/amelia/blob/main/LICENSE' }
        ]
      }
    ],

    // Sidebar navigation
    sidebar: {
      '/guide/': [
        {
          text: 'User Guide',
          items: [
            { text: 'Usage', link: '/guide/usage' },
            { text: 'Configuration', link: '/guide/configuration' },
            { text: 'Troubleshooting', link: '/guide/troubleshooting' }
          ]
        }
      ],
      '/architecture/': [
        {
          text: 'Architecture',
          items: [
            { text: 'Overview', link: '/architecture/overview' },
            { text: 'Concepts', link: '/architecture/concepts' },
            { text: 'Data Model', link: '/architecture/data-model' }
          ]
        }
      ],
      '/design-system/': [
        {
          text: 'Design System',
          items: [
            { text: 'Getting Started', link: '/design-system/' },
            { text: 'Color System', link: '/design-system/color-system' },
            { text: 'Typography', link: '/design-system/typography' }
          ]
        },
        {
          text: 'Themes',
          items: [
            { text: 'Diagrams', link: '/design-system/diagrams' },
            { text: 'Presentations', link: '/design-system/presentations' }
          ]
        },
        {
          text: 'API',
          items: [
            { text: 'Design Tokens', link: '/design-system/tokens' }
          ]
        }
      ],
      '/ideas/': [
        {
          text: 'Ideas & Explorations',
          items: [
            { text: 'Overview', link: '/ideas/' },
            { text: 'Session Continuity', link: '/ideas/session-continuity' },
            { text: 'CAPEX Tracking', link: '/ideas/capex-tracking' },
            { text: 'Knowledge Library', link: '/ideas/knowledge-library' },
            { text: 'AWS AgentCore', link: '/ideas/aws-agentcore' },
            { text: 'Debate Mode', link: '/ideas/debate-mode' },
            { text: 'Spec Builder', link: '/ideas/spec-builder' },
            { text: 'Context Compiler', link: '/ideas/context-compiler' },
            { text: 'Planning Workflows', link: '/ideas/planning-workflows' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'Roadmap', link: '/reference/roadmap' },
            { text: 'Benchmarking', link: '/reference/benchmarking' },
            { text: '12-Factor Compliance', link: '/reference/12-factor-compliance' }
          ]
        }
      ]
    },

    // Social links
    socialLinks: [
      { icon: 'github', link: 'https://github.com/anderskev/amelia' }
    ],

    // Footer
    footer: {
      message: 'Built by hey-amelia bot. Released under the MPL-2.0 License.',
      copyright: 'Copyright © 2024-2025 @anderskev'
    },

    // Search configuration
    search: {
      provider: 'local'
    },

    // Last updated timestamp
    lastUpdated: {
      text: 'Last updated',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short'
      }
    }
  },

  // Markdown configuration
  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    lineNumbers: true,
    languageAlias: {
      'd2': 'yaml'
    }
  },

  // Head configuration
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/amelia/logo/amelia-gold.svg' }],
    ['link', { rel: 'stylesheet', href: '/amelia/fonts/fonts.css' }]
  ]
})
```

**Step 3: Verify config syntax**

Run: `cd docs/site && pnpm build`
Expected: Build completes without errors

**Step 4: Commit**

```bash
git add docs/site/.vitepress/config.ts
git commit -m "docs: update VitePress config for full documentation structure"
```

---

## Task 9: Create Getting Started Page for Guide Section

**Files:**
- Create: `docs/site/guide/index.md`

**Step 1: Create guide/index.md**

Create `docs/site/guide/index.md`:

```markdown
# User Guide

Welcome to the Amelia user guide. This section covers everything you need to use Amelia in your projects.

## Quick Links

- [Usage](/guide/usage) - CLI commands, API reference, example workflows
- [Configuration](/guide/configuration) - Profile setup, driver options, retry settings
- [Troubleshooting](/guide/troubleshooting) - Common issues and solutions

## Getting Started

1. **Install Amelia**
   ```bash
   uv tool install git+https://github.com/anderskev/amelia.git
   ```

2. **Create configuration** in your project root:
   ```yaml
   # settings.amelia.yaml
   active_profile: dev
   profiles:
     dev:
       driver: api:openai
       tracker: github
   ```

3. **Run your first workflow**:
   ```bash
   amelia plan-only 123  # Generate plan for issue #123
   ```

## Next Steps

- Read the full [Usage Guide](/guide/usage) for all CLI commands
- Configure [drivers and trackers](/guide/configuration) for your environment
- Understand [how agents work](/architecture/concepts)
```

**Step 2: Verify file exists**

Run: `cat docs/site/guide/index.md | head -10`
Expected: Shows "# User Guide" header

**Step 3: Update sidebar to include index**

The sidebar already links to `/guide/usage` as the first item, which is correct.

**Step 4: Commit**

```bash
git add docs/site/guide/index.md
git commit -m "docs: add guide section index page"
```

---

## Task 10: Test VitePress Build Locally

**Files:**
- No new files

**Step 1: Install dependencies if needed**

```bash
cd docs/site && pnpm install
```

**Step 2: Run dev server**

```bash
cd docs/site && pnpm dev
```

**Step 3: Verify pages load**

Open browser to `http://localhost:5173/amelia/` and verify:
- [ ] Landing page loads with new hero
- [ ] Guide section: usage, configuration, troubleshooting
- [ ] Architecture section: overview, concepts, data-model
- [ ] Design System section: all pages load
- [ ] Ideas section: index and all brainstorming docs
- [ ] Reference section: roadmap, benchmarking, 12-factor
- [ ] Navigation works correctly
- [ ] Search works

**Step 4: Run production build**

```bash
cd docs/site && pnpm build
```

Expected: Build completes without errors

**Step 5: Preview production build**

```bash
cd docs/site && pnpm preview
```

**Step 6: Commit any fixes**

If any issues found, fix and commit separately.

---

## Task 11: Add GitHub Actions Workflow for Deployment

**Files:**
- Create: `.github/workflows/docs.yml`

**Step 1: Create workflow file**

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/site/**'
      - '.github/workflows/docs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        working-directory: docs/site
        run: pnpm install

      - name: Build
        working-directory: docs/site
        run: pnpm build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/site/.vitepress/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Step 2: Verify workflow syntax**

Run: `cat .github/workflows/docs.yml | head -20`
Expected: Shows valid YAML structure

**Step 3: Commit**

```bash
git add .github/workflows/docs.yml
git commit -m "ci: add GitHub Actions workflow for docs deployment"
```

---

## Task 12: Clean Up Old Documentation Structure

**Files:**
- Delete: `docs/usage.md`
- Delete: `docs/configuration.md`
- Delete: `docs/troubleshooting.md`
- Delete: `docs/architecture.md`
- Delete: `docs/concepts.md`
- Delete: `docs/data-model.md`
- Delete: `docs/roadmap.md`
- Delete: `docs/benchmarking.md`
- Delete: `docs/analysis/` directory
- Delete: `docs/brainstorming/` directory
- Delete: `docs/archived/` directory
- Delete: `docs/plans/` directory (except this plan until merge)
- Delete: `docs/testing/` directory
- Modify: `docs/README.md` (redirect to site)

**Step 1: Delete migrated files**

```bash
rm docs/usage.md
rm docs/configuration.md
rm docs/troubleshooting.md
rm docs/architecture.md
rm docs/concepts.md
rm docs/data-model.md
rm docs/roadmap.md
rm docs/benchmarking.md
```

**Step 2: Delete migrated directories**

```bash
rm -rf docs/analysis
rm -rf docs/brainstorming
rm -rf docs/archived
rm -rf docs/testing
```

**Step 3: Keep docs/plans/ for now**

Keep the plans directory until this PR merges, then delete in follow-up.

**Step 4: Keep docs/design/**

Keep the design directory (HTML/JSX prototypes) as referenced by README.

**Step 5: Update docs/README.md**

Replace `docs/README.md` with:

```markdown
# Amelia Documentation

📚 **Documentation has moved to the VitePress site.**

Visit: https://anderskev.github.io/amelia/

## Local Development

```bash
cd docs/site
pnpm install
pnpm dev
```

## Structure

- `site/` - VitePress documentation source
- `design/` - HTML/JSX design prototypes
- `plans/` - Temporary implementation plans (deleted after merge)
```

**Step 6: Verify structure**

Run: `ls -la docs/`
Expected: Shows only `README.md`, `design/`, `plans/`, `site/`

**Step 7: Commit**

```bash
git add -A docs/
git commit -m "docs: remove migrated files, update README redirect"
```

---

## Task 13: Update Root README.md Links

**Files:**
- Modify: `README.md`

**Step 1: Update documentation links**

In `README.md`, replace all `docs/*.md` links with VitePress site links:

- `docs/usage.md` → `https://anderskev.github.io/amelia/guide/usage`
- `docs/configuration.md` → `https://anderskev.github.io/amelia/guide/configuration`
- `docs/troubleshooting.md` → `https://anderskev.github.io/amelia/guide/troubleshooting`
- `docs/architecture.md` → `https://anderskev.github.io/amelia/architecture/overview`
- `docs/concepts.md` → `https://anderskev.github.io/amelia/architecture/concepts`
- `docs/roadmap.md` → `https://anderskev.github.io/amelia/reference/roadmap`
- `docs/benchmarking.md` → `https://anderskev.github.io/amelia/reference/benchmarking`
- `docs/analysis/12-factor-agents-compliance.md` → `https://anderskev.github.io/amelia/reference/12-factor-compliance`
- `docs/brainstorming/` → `https://anderskev.github.io/amelia/ideas/`

**Step 2: Update "Learn More" section**

Replace the Learn More section with links to the hosted docs site.

**Step 3: Verify links**

Run: `grep -n "docs/" README.md`
Expected: Only `docs/design/` references remain (for images)

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README links to VitePress site"
```

---

## Task 14: Final Verification and PR

**Files:**
- No new files

**Step 1: Run full build**

```bash
cd docs/site && pnpm build
```

Expected: No errors

**Step 2: Run local preview**

```bash
cd docs/site && pnpm preview
```

Verify all pages and links work.

**Step 3: Create PR**

```bash
git push -u origin feature/docs-migration
gh pr create --title "docs: migrate all documentation to VitePress site" --body "## Summary
- Migrates all project documentation into the VitePress site
- Adds Ideas section for brainstorming documents with disclaimer
- Reorganizes Design System into dedicated section
- Adds GitHub Actions workflow for GitHub Pages deployment
- Deprecates old docs/ structure

## Test Plan
- [ ] All pages load correctly
- [ ] Navigation works
- [ ] Search works
- [ ] Links resolve correctly
- [ ] GitHub Pages deployment succeeds"
```

**Step 4: Merge after CI passes**

Once CI passes and review approved, merge to main.

---

## Post-Merge Cleanup

After this PR merges:

1. Delete `docs/plans/2025-12-13-vitepress-docs-migration.md` (this file)
2. Verify GitHub Pages deployment at https://anderskev.github.io/amelia/
3. Consider deleting `docs/plans/` directory entirely if empty
