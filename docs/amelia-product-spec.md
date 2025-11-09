# Amelia: Product Specification
## Local LLM Workflow Orchestration - Web UI

**Document Version:** 1.0  
**Target Audience:** LLM UI/UX Design & Implementation  
**Last Updated:** 2025-11-08  
**Design System:** shadcn/ui + Radix UI Primitives  

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [User Personas](#2-user-personas)
3. [Core User Flows](#3-core-user-flows)
4. [Information Architecture](#4-information-architecture)
5. [Screen Specifications](#5-screen-specifications)
6. [Component Library](#6-component-library)
7. [Design Principles](#7-design-principles)
8. [Interaction Patterns](#8-interaction-patterns)
9. [Data Visualization](#9-data-visualization)
10. [Responsive Design](#10-responsive-design)
11. [Accessibility](#11-accessibility)
12. [State Management](#12-state-management)

---

## 1. Product Vision

### 1.1 Product Overview

Amelia is a **developer-first command center** for orchestrating LLM agents in local software development workflows. The web interface provides a visual control panel for managing complex agent workflows, RAG document knowledge bases, and interactive chat sessions with Claude and other LLMs.

### 1.2 Key Value Propositions

1. **Visual Workflow Management**: See agent execution in real-time with clear dependency graphs
2. **Unified Knowledge Hub**: Centralized document management with RAG-powered context retrieval
3. **Developer-Centric Design**: Clean, functional UI optimized for technical users
4. **Real-Time Feedback**: Live progress updates and streaming responses
5. **Git-Integrated**: Seamless worktree and branch management alongside agent tasks

### 1.3 Design Philosophy

- **Function Over Form**: Prioritize clarity and usability over decorative elements
- **Information Density**: Display relevant data without overwhelming the user
- **Rapid Access**: Common actions should be 1-2 clicks away
- **Progressive Disclosure**: Show complexity only when needed
- **Developer Aesthetic**: Clean, modern, technical look (think VS Code, Linear, Vercel)

---

## 2. User Personas

### 2.1 Primary Persona: Sarah - Senior Backend Engineer

**Background:**
- 8 years of experience in Python/FastAPI
- Works on complex microservices architecture
- Uses AI tools daily for code generation and documentation
- Comfortable with terminal but prefers visual tools for complex tasks

**Goals:**
- Orchestrate multiple agents for full feature development
- Maintain context across different development phases
- Track agent progress and intervene when needed
- Query documentation knowledge base efficiently

**Pain Points:**
- Juggling multiple AI chat windows loses context
- Hard to track dependencies between agent tasks
- Managing relevant documentation is manual and error-prone
- No visibility into agent reasoning process

**Usage Patterns:**
- Opens Amelia at start of workday
- Runs 3-5 workflows daily
- Uploads 10-20 documents per week
- Uses chat for quick queries between workflow runs

---

## 3. Core User Flows

### 3.1 Primary Flow: Run Discovery → Design → Planning Workflow

**Goal:** Execute a complete requirements-to-plan workflow with document context

**Steps:**
1. User opens Workflows page
2. Selects "Discovery → Design → Planning" preset
3. Clicks "Configure Workflow"
4. Enters project description in textarea
5. Toggles "Use RAG" to include document context
6. Reviews selected documents (auto-selected based on recency)
7. Clicks "Start Workflow"
8. Redirected to workflow execution view
9. Watches real-time progress of each agent
10. Reviews output from each stage
11. Downloads final planning document
12. Creates Git branch for implementation

**Success Criteria:**
- Workflow completes without errors
- User understands what each agent did
- Output is immediately actionable

### 3.2 Secondary Flow: Upload & Query Documents

**Goal:** Add technical documentation and ask questions against it

**Steps:**
1. User opens Documents page
2. Clicks "Upload Documents" button
3. Drags and drops PDF/Markdown files (or uses file picker)
4. Files are processed with progress indicators
5. User sees document list update with new entries
6. User clicks "Query Documents" in header
7. Types question in search bar
8. Sees relevant document chunks with similarity scores
9. Clicks chunk to expand full context
10. Copies relevant section to clipboard

**Success Criteria:**
- Upload is fast and provides clear feedback
- Search results are relevant and well-formatted
- Easy to scan and extract information

### 3.3 Tertiary Flow: Interactive Chat with RAG

**Goal:** Have a conversation with Claude using project documentation as context

**Steps:**
1. User opens Chat page
2. Clicks "New Chat" button
3. Toggles "Use Project Knowledge" switch
4. Types first message
5. Sees streaming response with citations to source documents
6. Clicks citation to view source
7. Continues conversation with follow-up questions
8. Bookmarks particularly useful responses
9. Exports conversation as Markdown

**Success Criteria:**
- Responses feel natural and contextual
- Source citations are clear and clickable
- Conversation history is preserved
- Export is clean and readable

---

## 4. Information Architecture

### 4.1 Navigation Structure

```
Amelia Web App
│
├── Home (Dashboard)
│   ├── Recent Activity
│   ├── Quick Actions
│   └── System Status
│
├── Chat
│   ├── Session List (Sidebar)
│   ├── Active Chat View
│   └── Settings Panel
│
├── Workflows
│   ├── Workflow List
│   ├── Workflow Detail/Execution
│   └── Workflow Configuration
│
├── Documents
│   ├── Document Library
│   ├── Upload Interface
│   ├── Web Scraper
│   └── Document Search/Query
│
├── Agents
│   ├── Agent Roster
│   ├── Agent Detail View
│   └── Agent Logs
│
├── Git
│   ├── Branch Manager
│   ├── Worktree List
│   └── Git Actions
│
└── Settings
    ├── LLM Configuration
    ├── RAG Settings
    ├── Git Settings
    └── System Preferences
```

### 4.2 Content Hierarchy

**Priority Levels:**

1. **Critical (Always Visible):**
   - Current page navigation
   - Active task status
   - Error messages
   - System health indicator

2. **Primary (Default View):**
   - Main content area
   - Primary actions
   - Key metrics
   - Recent activity

3. **Secondary (On Demand):**
   - Configuration options
   - Historical data
   - Detailed logs
   - Advanced settings

4. **Tertiary (Discoverable):**
   - Help documentation
   - Keyboard shortcuts
   - Debug information
   - Export options

---

## 5. Screen Specifications

### 5.1 Layout Shell

**Purpose:** Consistent wrapper for all pages providing navigation and context

**Components:**

```tsx
<Layout>
  <Header>
    <Logo />
    <SystemStatus />
    <QuickActions />
    <UserMenu />
  </Header>
  
  <Sidebar>
    <Navigation />
    <ActiveTasks />
  </Sidebar>
  
  <MainContent>
    {/* Page content */}
  </MainContent>
  
  <StatusBar>
    <ConnectionStatus />
    <BackgroundTasks />
  </StatusBar>
</Layout>
```

**Visual Design:**

- **Header:** 64px height, white background, subtle bottom border
- **Sidebar:** 240px width, light gray background (zinc-50), collapsible
- **Main Content:** Flexible, white background, 24px padding
- **Status Bar:** 32px height, dark background, white text

**Navigation Items:**

1. Home (House icon)
2. Chat (MessageSquare icon)
3. Workflows (GitBranch icon)
4. Documents (FileText icon)
5. Agents (Bot icon)
6. Git (GitBranch icon)
7. Settings (Settings icon)

**State Indicators:**

- Active page: Primary color background, white text
- Hover: Light gray background
- Running task: Pulsing blue dot
- Error: Red dot with count badge

---

### 5.2 Home (Dashboard)

**Purpose:** Overview of system activity and quick access to common tasks

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│ Welcome back, Sarah                    🟢 All Systems Go │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Quick Actions   │  │ Recent Activity │               │
│  │                 │  │                 │               │
│  │ [New Chat]      │  │ Workflow: DDP   │               │
│  │ [Run Workflow]  │  │ ├─ Discovery ✓  │               │
│  │ [Upload Docs]   │  │ ├─ Design ✓     │               │
│  │ [Git Branch]    │  │ └─ Planning ⟳   │               │
│  └─────────────────┘  │                 │               │
│                        │ Chat: API Help  │               │
│  ┌─────────────────┐  │ 5 messages      │               │
│  │ Active Tasks    │  │                 │               │
│  │                 │  │ Upload: docs.pdf│               │
│  │ Planning Agent  │  │ Processing...   │               │
│  │ [Progress Bar]  │  └─────────────────┘               │
│  │ 67% complete    │                                     │
│  └─────────────────┘                                     │
│                                                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │ System Resources                                   │  │
│  │ CPU: ████████░░ 80%  RAM: ██████░░░░ 60%          │  │
│  │ Active Agents: 2     Documents: 47                │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Components:**

1. **Welcome Header**
   - Greeting with user name
   - System status indicator (green dot + text)
   - Component: `<Card>` with flex header

2. **Quick Actions**
   - 4 large buttons with icons
   - Component: `<Button variant="outline" size="lg">`
   - Grid layout: 2x2

3. **Recent Activity**
   - Scrollable list of recent items
   - Component: `<ScrollArea>` with custom list items
   - Show last 10 activities
   - Each item shows: icon, title, timestamp, status

4. **Active Tasks**
   - Live-updating progress indicators
   - Component: `<Card>` with `<Progress>` bars
   - Click to view details

5. **System Resources**
   - Visual metrics for system health
   - Component: `<Card>` with progress bars and labels
   - Updates every 5 seconds

**Interactions:**

- Click Quick Action → Navigate to relevant page
- Click Recent Activity item → Open detail view
- Click Active Task → Expand to show full logs
- Hover on metric → Show tooltip with details

---

### 5.3 Chat Interface

**Purpose:** Conversational interface with LLMs, optionally using RAG context

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Chat with Claude                    [Use Project Knowledge] │
├──────────────┬──────────────────────────────────────────────┤
│ Sessions     │ Message History                              │
│              │                                              │
│ • API Help   │ ┌────────────────────────────────────────┐  │
│   5 msgs     │ │ You: How do I structure a FastAPI...   │  │
│              │ └────────────────────────────────────────┘  │
│ • Bug Fix    │                                              │
│   12 msgs    │ ┌────────────────────────────────────────┐  │
│              │ │ Claude: Based on the FastAPI docs...   │  │
│ + New Chat   │ │ [Source: fastapi-docs.pdf p.42] ──────→│  │
│              │ └────────────────────────────────────────┘  │
│              │                                              │
│              │ ┌────────────────────────────────────────┐  │
│              │ │ You: Can you show an example?          │  │
│              │ └────────────────────────────────────────┘  │
│              │                                              │
│              │ ┌────────────────────────────────────────┐  │
│              │ │ Claude: Here's a complete example...   │  │
│              │ │ ```python                              │  │
│              │ │ from fastapi import FastAPI            │  │
│              │ │ ...                                    │  │
│              │ │ ```                                    │  │
│              │ └────────────────────────────────────────┘  │
│              │                                              │
│              ├──────────────────────────────────────────────┤
│              │ Type your message...                     [↑] │
│              └──────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Chat Header**
   - Title showing model name
   - Toggle: "Use Project Knowledge"
   - Settings menu (model selection, temperature)
   - Component: `<Card>` header with `<Switch>` and `<DropdownMenu>`

2. **Session Sidebar**
   - List of chat sessions
   - Component: `<ScrollArea>` with custom list items
   - Each session shows: title, message count, timestamp
   - "New Chat" button at top
   - Active session highlighted

3. **Message Area**
   - Scrollable message list
   - Component: `<ScrollArea>` with message cards
   - User messages: Right-aligned, light blue background
   - Assistant messages: Left-aligned, white background
   - System messages: Center-aligned, gray background

4. **Message Item**
   - Avatar (user icon or Claude icon)
   - Message content (supports markdown)
   - Timestamp
   - Source citations (if from RAG)
   - Actions: Copy, Bookmark, Delete
   - Component: `<Card>` with `<Avatar>` and markdown renderer

5. **Citation Links**
   - Inline citations in messages
   - Component: `<Badge variant="secondary">` with hover card
   - Hover shows: Document name, page, preview
   - Click opens document viewer

6. **Input Area**
   - Multi-line text input
   - Component: `<Textarea>` with auto-resize
   - Send button with loading state
   - File attachment option (future)
   - Character count (subtle, gray)

**Interactions:**

- Type message + Enter → Send (Shift+Enter for newline)
- Streaming response → Animate text appearance
- Click citation → Open source document preview in modal
- Click session → Load that conversation
- Toggle RAG → Show toast confirming state
- New Chat → Create session and clear messages

**Special States:**

- **Loading:** Show typing indicator with animated dots
- **Error:** Display error message in red banner
- **Empty:** Show welcome message with suggestions
- **Streaming:** Show blinking cursor at end of text

---

### 5.4 Workflows Page

**Purpose:** Manage and execute multi-agent workflows

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Workflows                          [+ Create Workflow]       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Discovery →     │ │ Full SDLC      │ │ Bug Analysis   ││
│ │ Design →        │ │                 │ │                 ││
│ │ Planning        │ │ 7 agents        │ │ 3 agents        ││
│ │                 │ │                 │ │                 ││
│ │ 3 agents        │ │ 45 min avg     │ │ 15 min avg     ││
│ │ 15 min avg      │ │                 │ │                 ││
│ │                 │ │ [Run]           │ │ [Run]           ││
│ │ [Run]           │ └─────────────────┘ └─────────────────┘│
│ └─────────────────┘                                          │
│                                                               │
│ Recent Executions                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Discovery → Design → Planning        Running     [View] ││
│ │ ├─ Discovery Agent            ✓ Complete               ││
│ │ ├─ Design Agent               ✓ Complete               ││
│ │ └─ Planning Agent             ⟳ 67% complete           ││
│ │                                                          ││
│ │ Full SDLC                            Complete    [View] ││
│ │ All 7 agents completed successfully                     ││
│ │ 42 minutes ago                                          ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Workflow Cards (List View)**
   - Card for each workflow preset
   - Component: `<Card>` with hover effects
   - Shows: Name, description, agent count, avg duration
   - "Run" button (primary action)
   - Edit icon (secondary action)

2. **Create Workflow Button**
   - Prominent button in header
   - Component: `<Button variant="default">`
   - Opens workflow builder modal

3. **Recent Executions**
   - List of recent workflow runs
   - Component: `<Card>` with table or list
   - Each execution shows:
     - Workflow name
     - Status (running/complete/failed)
     - Progress breakdown by agent
     - Timestamp
     - "View" button

4. **Workflow Execution View**
   - Detailed view when running or viewing workflow
   - Shows live progress of each agent
   - Component: Multi-panel layout with graph visualization

**Workflow Execution Detail Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Workflows     Discovery → Design → Planning       │
│                         Running (23 minutes elapsed)         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐│
│ │          Agent Flow Visualization                        ││
│ │                                                          ││
│ │     ┌─────────────┐                                     ││
│ │     │  Discovery  │  ✓ Complete                        ││
│ │     │   Agent     │  12:34 - 12:38 (4 min)            ││
│ │     └──────┬──────┘                                     ││
│ │            │                                             ││
│ │            ▼                                             ││
│ │     ┌─────────────┐                                     ││
│ │     │   Design    │  ✓ Complete                        ││
│ │     │   Agent     │  12:38 - 12:45 (7 min)            ││
│ │     └──────┬──────┘                                     ││
│ │            │                                             ││
│ │            ▼                                             ││
│ │     ┌─────────────┐                                     ││
│ │     │  Planning   │  ⟳ Running (67%)                   ││
│ │     │   Agent     │  [████████████░░░░░░]               ││
│ │     └─────────────┘  12:45 - Now                       ││
│ │                                                          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                               │
│ ┌────────────┬────────────────────────────────────────────┐│
│ │ Agents  │ Output  │ Logs                               ││
│ ├────────────┼────────────────────────────────────────────┤│
│ │• Discovery │ Planning Agent: Analyzing design document...││
│ │• Design    │                                            ││
│ │• Planning ⟳│ Retrieved 5 relevant document chunks      ││
│ │            │                                            ││
│ │            │ Generating implementation plan...          ││
│ │            │                                            ││
│ │            │ Progress: Creating task breakdown (67%)    ││
│ │            │                                            ││
│ └────────────┴────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Execution View Components:**

1. **Breadcrumb Navigation**
   - Back to list link
   - Workflow name
   - Status badge
   - Component: Breadcrumb with status `<Badge>`

2. **Agent Flow Graph**
   - Visual representation of agent DAG
   - Component: Custom SVG visualization or Mermaid diagram
   - Nodes show: Agent name, status icon, duration
   - Edges show dependencies
   - Current agent highlighted with animation

3. **Progress Panel**
   - Tabbed interface: Agents | Output | Logs
   - Component: `<Tabs>` with `<ScrollArea>` content
   - **Agents Tab:** List of agents with status and duration
   - **Output Tab:** Combined output from all agents (markdown)
   - **Logs Tab:** Raw logs with timestamps (monospace font)

4. **Action Bar**
   - Pause/Resume button (for running workflows)
   - Stop button
   - Export results button
   - Component: Button group in header

**Interactions:**

- Click workflow card → Open configuration modal
- Click "Run" on card → Start workflow with defaults
- Configure workflow → Show modal with input form
- View execution → Navigate to detailed view
- Pause workflow → Show confirmation dialog
- Click agent in list → Jump to that agent's output
- Export results → Download as markdown or JSON

---

### 5.5 Documents Page

**Purpose:** Manage RAG document library and perform searches

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Documents               [Upload] [Scrape Web] [Query Docs]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Search documents...                                 [🔍] ││
│ └─────────────────────────────────────────────────────────┘│
│                                                               │
│ ┌────────┬──────────┬─────────┬──────────┬─────────┬──────┐│
│ │ Name   │ Type     │ Size    │ Uploaded │ Chunks  │      ││
│ ├────────┼──────────┼─────────┼──────────┼─────────┼──────┤│
│ │📄 api- │ PDF      │ 2.3 MB  │ 2h ago   │ 142     │ ⋮    ││
│ │  guide │          │         │          │         │      ││
│ │        │          │         │          │         │      ││
│ │📄 arch │ Markdown │ 45 KB   │ 1d ago   │ 23      │ ⋮    ││
│ │  docs  │          │         │          │         │      ││
│ │        │          │         │          │         │      ││
│ │📄 reqs │ PDF      │ 1.1 MB  │ 3d ago   │ 67      │ ⋮    ││
│ │  doc   │          │         │          │         │      ││
│ └────────┴──────────┴─────────┴──────────┴─────────┴──────┘│
│                                                               │
│ Showing 47 documents                            [1][2][3][4] │
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Action Buttons**
   - Upload: Opens file picker or drag-drop zone
   - Scrape Web: Opens URL input dialog
   - Query Docs: Opens search interface
   - Component: `<Button>` group in header

2. **Search Bar**
   - Full-text search across documents
   - Component: `<Input>` with search icon
   - Debounced search (500ms delay)
   - Clear button when text entered

3. **Document Table**
   - Sortable columns
   - Component: `<Table>` with shadcn styling
   - Columns: Name, Type, Size, Uploaded, Chunks, Actions
   - Row actions: View, Delete, Download
   - Hover shows full name if truncated

4. **Pagination**
   - Page numbers and navigation
   - Component: `<Pagination>`
   - Shows X of Y documents

**Upload Modal:**

```
┌─────────────────────────────────────────┐
│ Upload Documents                    [×] │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │                                   │ │
│  │   Drag and drop files here       │ │
│  │   or click to browse             │ │
│  │                                   │ │
│  │   Supported: PDF, Markdown, HTML │ │
│  │                                   │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Selected Files:                        │
│  • api-guide.pdf (2.3 MB)              │
│  • architecture.md (45 KB)             │
│                                         │
│              [Cancel]  [Upload (2)]    │
└─────────────────────────────────────────┘
```

**Components:**

- Drag-drop zone: `<div>` with dashed border and hover state
- File list: Shows selected files before upload
- Progress bars: Show during processing
- Success notification: Toast after completion

**Query Interface Modal:**

```
┌─────────────────────────────────────────┐
│ Query Documents                     [×] │
├─────────────────────────────────────────┤
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ What are the authentication       │  │
│ │ requirements for the API?         │  │
│ └───────────────────────────────────┘  │
│                           [Search]      │
│                                         │
│ Results (5):                            │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ 📄 api-guide.pdf (p. 42)          │  │
│ │ Similarity: 0.89                  │  │
│ │                                   │  │
│ │ "Authentication requires a valid  │  │
│ │ API key passed in the Authorization│ │
│ │ header as Bearer token..."        │  │
│ │                                   │  │
│ │               [View Full] [Copy]  │  │
│ └───────────────────────────────────┘  │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ 📄 auth-spec.md                   │  │
│ │ Similarity: 0.85                  │  │
│ │ ...                               │  │
└─────────────────────────────────────────┘
```

**Components:**

- Query input: `<Textarea>` with search button
- Result cards: `<Card>` for each result
- Similarity score: Progress bar or badge
- Content preview: First 200 chars with expand option
- Actions: View full document, copy content

**Interactions:**

- Click Upload → Open modal with drag-drop
- Drag files to table → Auto-open upload modal
- Click Scrape Web → Show URL input dialog
- Enter URL → Fetch and process, show progress
- Click Query → Open search interface
- Search documents → Live filtering of table
- Click document row → Open preview modal
- Click actions menu (⋮) → Show View/Delete/Download
- Sort column → Re-order table

---

### 5.6 Agents Page

**Purpose:** View available agents and monitor their execution

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Agents                                                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Available Agents                                             │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ 🔍 Discovery    │ │ 🎨 Design       │ │ 📋 Planning     ││
│ │                 │ │                 │ │                 ││
│ │ Analyzes reqs   │ │ Creates tech    │ │ Generates impl  ││
│ │ and documents   │ │ design from     │ │ plans and tasks ││
│ │ to discover     │ │ features        │ │                 ││
│ │ features        │ │                 │ │                 ││
│ │                 │ │                 │ │                 ││
│ │ Status: Idle    │ │ Status: Idle    │ │ Status: Running ││
│ │                 │ │                 │ │ [████████░░]    ││
│ │ [View] [Config] │ │ [View] [Config] │ │ [View] [Stop]   ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ 🔧 Code Review  │ │ 🐛 Bug Analysis │ │ 📝 Docs Writer  ││
│ │ ...             │ │ ...             │ │ ...             ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘│
│                                                               │
│ Execution History                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Planning Agent          Complete  ✓    23 min ago       ││
│ │ Discovery Agent         Complete  ✓    1 hour ago       ││
│ │ Design Agent            Failed    ✗    2 hours ago      ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Agent Cards**
   - Card for each available agent
   - Component: `<Card>` with hover effects
   - Shows: Icon, name, description, current status
   - Status indicator: Badge with color
   - Progress bar if running
   - Action buttons: View, Config/Stop

2. **Execution History**
   - List of recent agent runs
   - Component: `<Table>` or card list
   - Shows: Agent name, status, duration, timestamp
   - Click to view details

**Agent Detail Modal:**

```
┌─────────────────────────────────────────┐
│ Planning Agent                      [×] │
├─────────────────────────────────────────┤
│                                         │
│ Configuration                           │
│ ┌───────────────────────────────────┐  │
│ │ Model: claude-sonnet-4-5-20250929 │  │
│ │ Temperature: 0.7                  │  │
│ │ Max Tokens: 4096                  │  │
│ │ Timeout: 300s                     │  │
│ └───────────────────────────────────┘  │
│                                         │
│ Recent Outputs                          │
│ ┌───────────────────────────────────┐  │
│ │ # Implementation Plan             │  │
│ │                                   │  │
│ │ ## Phase 1: Setup                 │  │
│ │ - Initialize project structure    │  │
│ │ - Configure dependencies          │  │
│ │ ...                               │  │
│ └───────────────────────────────────┘  │
│                                         │
│ Execution Logs                          │
│ ┌───────────────────────────────────┐  │
│ │ [12:45:23] Starting agent...      │  │
│ │ [12:45:24] Loading context...     │  │
│ │ [12:45:26] Generating plan...     │  │
│ └───────────────────────────────────┘  │
│                                         │
│                          [Close]        │
└─────────────────────────────────────────┘
```

**Components:**

- Configuration display: Read-only form fields
- Output viewer: Markdown renderer in scroll area
- Logs viewer: Monospace text with timestamps
- Export button: Download output as file

**Interactions:**

- Click agent card → Open detail modal
- Click Config → Open configuration editor
- Click Stop (if running) → Confirm and stop
- View execution history → Filter by agent or status

---

### 5.7 Git Page

**Purpose:** Manage Git branches and worktrees for agent-driven development

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Git Integration            Current Branch: main              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────┬─────────────────────────────────────┐
│ │ Branches            │ Worktrees                           │
│ │                     │                                     │
│ │ • main *            │ ┌─────────────────────────────────┐│
│ │ • feature/auth      │ │ 📁 worktrees/feature-auth       ││
│ │ • feature/api       │ │ Branch: feature/auth            ││
│ │ • bugfix/login      │ │ Status: Clean                   ││
│ │                     │ │                                 ││
│ │ [+ New Branch]      │ │ [Open] [Remove]                 ││
│ │                     │ └─────────────────────────────────┘│
│ │                     │                                     │
│ │                     │ ┌─────────────────────────────────┐│
│ │                     │ │ 📁 worktrees/feature-api        ││
│ │                     │ │ Branch: feature/api             ││
│ │                     │ │ Status: Modified (3 files)      ││
│ │                     │ │                                 ││
│ │                     │ │ [Open] [Remove]                 ││
│ │                     │ └─────────────────────────────────┘│
│ │                     │                                     │
│ │                     │ [+ New Worktree]                    │
│ └─────────────────────┴─────────────────────────────────────┘
│                                                               │
│ Quick Actions                                                │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [Create Branch & Worktree for Workflow]                  ││
│ │ [Sync All Worktrees]                                     ││
│ │ [Clean Up Merged Branches]                               ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Header**
   - Shows current branch
   - Component: Header with badge

2. **Two-Panel Layout**
   - Left: Branch list
   - Right: Worktree list
   - Component: `<div>` with grid layout

3. **Branch List**
   - Scrollable list of branches
   - Component: `<ScrollArea>` with list items
   - Current branch marked with asterisk
   - Click to checkout (with confirmation)
   - "New Branch" button

4. **Worktree Cards**
   - Card for each worktree
   - Component: `<Card>`
   - Shows: Path, branch, status (clean/modified)
   - Actions: Open in editor, Remove
   - Status badge with color coding

5. **Quick Actions**
   - Common Git operations
   - Component: Large `<Button>` elements
   - Create branch + worktree in one action
   - Sync all worktrees (pull latest)
   - Clean up merged branches

**New Branch Modal:**

```
┌─────────────────────────────────────────┐
│ Create New Branch                   [×] │
├─────────────────────────────────────────┤
│                                         │
│ Branch Name                             │
│ ┌───────────────────────────────────┐  │
│ │ feature/                          │  │
│ └───────────────────────────────────┘  │
│                                         │
│ Branch From                             │
│ ┌───────────────────────────────────┐  │
│ │ main                          ▼   │  │
│ └───────────────────────────────────┘  │
│                                         │
│ ☑ Create worktree                      │
│                                         │
│ Worktree Path                           │
│ ┌───────────────────────────────────┐  │
│ │ worktrees/feature-                │  │
│ └───────────────────────────────────┘  │
│                                         │
│              [Cancel]  [Create]         │
└─────────────────────────────────────────┘
```

**Components:**

- Text input for branch name
- Select dropdown for base branch
- Checkbox for creating worktree
- Auto-populated worktree path
- Validation for branch name format

**Interactions:**

- Click branch → Switch to that branch (confirmation)
- New Branch → Open creation modal
- New Worktree → Open creation modal
- Open worktree → Open in VS Code or default editor
- Remove worktree → Confirm and remove
- Sync worktrees → Pull latest for all

---

### 5.8 Settings Page

**Purpose:** Configure system preferences, LLM settings, and RAG parameters

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌──────────┬──────────────────────────────────────────────┐│
│ │ General  │ LLM Configuration                             ││
│ │ LLM      │                                               ││
│ │ RAG      │ Default Model                                 ││
│ │ Git      │ ┌────────────────────────────────────────┐   ││
│ │ System   │ │ claude-sonnet-4-5-20250929        ▼   │   ││
│ │          │ └────────────────────────────────────────┘   ││
│ │          │                                               ││
│ │          │ Temperature                                   ││
│ │          │ ┌────────────────────────────────────────┐   ││
│ │          │ │ 0.7                                    │   ││
│ │          │ └────────────────────────────────────────┘   ││
│ │          │ [━━━━━━━●━━━━━━━━━━━━━━━━━━━━━━━━━]           ││
│ │          │                                               ││
│ │          │ Max Tokens                                    ││
│ │          │ ┌────────────────────────────────────────┐   ││
│ │          │ │ 4096                                   │   ││
│ │          │ └────────────────────────────────────────┘   ││
│ │          │                                               ││
│ │          │ API Keys                                      ││
│ │          │ Anthropic API Key                            ││
│ │          │ ┌────────────────────────────────────────┐   ││
│ │          │ │ ••••••••••••••••••••••••••         │   ││
│ │          │ └────────────────────────────────────────┘   ││
│ │          │                                               ││
│ │          │ OpenRouter API Key                           ││
│ │          │ ┌────────────────────────────────────────┐   ││
│ │          │ │ ••••••••••••••••••••••••••         │   ││
│ │          │ └────────────────────────────────────────┘   ││
│ │          │                                               ││
│ │          │                        [Save]  [Reset]       ││
│ └──────────┴──────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Components:**

1. **Settings Navigation**
   - Vertical tab list
   - Component: Custom vertical `<Tabs>`
   - Sections: General, LLM, RAG, Git, System

2. **Settings Panels**
   - Content area for each section
   - Component: Form with labeled inputs
   - Grouped by logical categories

**Settings Sections:**

**General:**
- Theme (Light/Dark/System)
- Language
- Keyboard shortcuts

**LLM:**
- Default model selection
- Temperature slider
- Max tokens input
- API keys (masked)
- Timeout settings

**RAG:**
- Embedding model
- Chunk size
- Chunk overlap
- Top K results
- Similarity threshold

**Git:**
- Default worktree directory
- Auto-sync enabled
- Git executable path

**System:**
- Database connection
- Log level
- Enable debug mode
- Clear cache

**Interactions:**

- Change setting → Mark as unsaved (show indicator)
- Click Save → Persist changes, show success toast
- Click Reset → Revert to defaults (confirmation)
- Test API key → Validate connection, show result

---

## 6. Component Library

### 6.1 Core shadcn/ui Components Used

**Form Components:**
- `<Button>` - All action triggers
- `<Input>` - Text inputs
- `<Textarea>` - Multi-line text
- `<Select>` - Dropdowns
- `<Switch>` - Toggle controls
- `<Slider>` - Numeric ranges
- `<Checkbox>` - Boolean options
- `<RadioGroup>` - Single choice

**Layout Components:**
- `<Card>` - Content containers
- `<Tabs>` - Tabbed interfaces
- `<ScrollArea>` - Scrollable content
- `<Separator>` - Visual dividers
- `<Dialog>` - Modal dialogs
- `<Sheet>` - Slide-out panels

**Feedback Components:**
- `<Toast>` - Notifications
- `<Progress>` - Progress indicators
- `<Badge>` - Status labels
- `<Alert>` - Important messages
- `<Skeleton>` - Loading states

**Navigation Components:**
- `<DropdownMenu>` - Action menus
- `<NavigationMenu>` - Main nav
- `<Breadcrumb>` - Page hierarchy
- `<Pagination>` - Page navigation

**Data Display:**
- `<Table>` - Tabular data
- `<Avatar>` - User icons
- `<Tooltip>` - Hover info
- `<HoverCard>` - Expanded info
- `<Accordion>` - Collapsible sections

### 6.2 Custom Components

**WorkflowGraph:**
- Visual DAG representation
- Shows agent dependencies
- Real-time status updates
- Interactive nodes

**MessageList:**
- Chat message display
- Markdown rendering
- Code syntax highlighting
- Citation handling

**AgentProgressCard:**
- Live progress tracking
- Log streaming
- Expandable details
- Action controls

**DocumentPreview:**
- PDF/Markdown viewer
- Syntax highlighting
- Search within document
- Copy functionality

**StatusIndicator:**
- System health display
- Resource monitoring
- Connection status
- Real-time updates

---

## 7. Design Principles

### 7.1 Visual Design

**Color Palette:**

Primary Colors:
- Primary: Blue (#3B82F6) - Actions, links
- Secondary: Zinc (#71717A) - Secondary elements
- Success: Green (#10B981) - Completed states
- Warning: Amber (#F59E0B) - Warnings
- Error: Red (#EF4444) - Errors, failures
- Info: Sky (#0EA5E9) - Information

Neutral Colors:
- Background: White (#FFFFFF)
- Surface: Zinc-50 (#FAFAFA)
- Border: Zinc-200 (#E4E4E7)
- Text Primary: Zinc-900 (#18181B)
- Text Secondary: Zinc-600 (#52525B)
- Text Disabled: Zinc-400 (#A1A1AA)

**Typography:**

- Font Family: Inter (sans-serif)
- Headings: 
  - H1: 2rem (32px), font-weight 700
  - H2: 1.5rem (24px), font-weight 600
  - H3: 1.25rem (20px), font-weight 600
  - H4: 1rem (16px), font-weight 600
- Body: 0.875rem (14px), font-weight 400
- Small: 0.75rem (12px), font-weight 400
- Code: 'Fira Code' (monospace)

**Spacing:**

- Base unit: 4px
- Common spacing:
  - xs: 4px
  - sm: 8px
  - md: 16px
  - lg: 24px
  - xl: 32px
  - 2xl: 48px

**Border Radius:**

- Small: 4px (inputs, badges)
- Medium: 8px (cards, buttons)
- Large: 12px (modals, large cards)
- Full: 9999px (avatars, pills)

**Shadows:**

- Small: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- Medium: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
- Large: 0 10px 15px -3px rgba(0, 0, 0, 0.1)

### 7.2 Component States

**Interactive States:**

1. **Default:** Base appearance
2. **Hover:** Subtle background change, cursor pointer
3. **Active:** Pressed state, slightly darker
4. **Focus:** Blue ring outline (2px)
5. **Disabled:** Reduced opacity (50%), no interaction
6. **Loading:** Spinner or skeleton, disabled interaction

**Status States:**

1. **Idle:** Gray badge, no animation
2. **Running:** Blue badge, pulsing animation
3. **Complete:** Green badge, checkmark icon
4. **Failed:** Red badge, X icon
5. **Paused:** Amber badge, pause icon

### 7.3 Animation Guidelines

**Timing:**
- Quick: 150ms (hover, focus)
- Standard: 300ms (modal open/close)
- Slow: 500ms (complex transitions)

**Easing:**
- Ease-out: Most transitions
- Ease-in-out: Modal animations
- Spring: Dragging, physics

**Common Animations:**
- Fade in: Opacity 0 → 1
- Slide in: Transform translateY
- Scale: Transform scale
- Pulse: Opacity/scale loop
- Spin: Rotate 360deg loop

**What to Animate:**
- Modal open/close
- Toast notifications
- Progress indicators
- Hover effects
- Status changes
- Loading states

**What NOT to Animate:**
- Large content areas
- Tables with many rows
- Text content
- Critical actions

---

## 8. Interaction Patterns

### 8.1 Common Patterns

**Create/New:**
1. Click "New" button (+ icon)
2. Open modal/dialog
3. Fill form fields
4. Validate input
5. Show loading state
6. Display success toast
7. Navigate to new item or refresh list

**Edit:**
1. Click edit icon/button
2. Load current values into form
3. Modify fields
4. Show unsaved indicator
5. Save with confirmation
6. Update UI optimistically
7. Revert on error

**Delete:**
1. Click delete icon/button
2. Show confirmation dialog
3. Explain consequences
4. Confirm or cancel
5. Show loading state
6. Remove from UI
7. Show success toast with undo option

**Search/Filter:**
1. Type in search input
2. Debounce (500ms)
3. Show loading indicator
4. Update results
5. Highlight matches
6. Show count
7. Provide clear action

**Streaming Content:**
1. Show typing indicator
2. Stream text chunk by chunk
3. Scroll to bottom automatically
4. Show "Stop" button
5. Complete with final state
6. Enable copy/export

### 8.2 Keyboard Shortcuts

**Global:**
- `Cmd/Ctrl + K` - Command palette
- `Cmd/Ctrl + /` - Help/shortcuts
- `Cmd/Ctrl + ,` - Settings
- `Esc` - Close modal/dialog

**Navigation:**
- `Cmd/Ctrl + 1-7` - Jump to page
- `Cmd/Ctrl + B` - Toggle sidebar
- `Arrow keys` - Navigate lists

**Chat:**
- `Enter` - Send message
- `Shift + Enter` - New line
- `Cmd/Ctrl + K` - Clear chat
- `Arrow Up` - Edit last message

**Workflows:**
- `Cmd/Ctrl + Enter` - Start workflow
- `Cmd/Ctrl + .` - Pause workflow
- `Cmd/Ctrl + P` - Export results

### 8.3 Error Handling

**Validation Errors:**
- Inline error messages below fields
- Red border on invalid fields
- Error icon with tooltip
- Disable submit until valid

**API Errors:**
- Toast notification with error message
- Retry button for transient errors
- Contact support for severe errors
- Log details for debugging

**Network Errors:**
- Offline banner at top
- Disable network actions
- Queue actions for retry
- Show reconnection status

**Loading States:**
- Skeleton loaders for content
- Spinners for actions
- Progress bars for long tasks
- Estimated time for workflows

---

## 9. Data Visualization

### 9.1 Workflow Progress

**Linear Progress:**
- Single progress bar
- Percentage label
- Estimated time remaining
- Cancel button

```
Planning Agent (67%)
[████████████████████░░░░░░░░░░] 
Estimated: 2 minutes remaining
[Cancel]
```

**Multi-Agent Flow:**
- Vertical flowchart
- Color-coded status
- Connections between agents
- Time for each stage

```
┌─────────────┐
│  Discovery  │ ✓ 4 min
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Design    │ ✓ 7 min
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Planning   │ ⟳ Running
└─────────────┘
```

### 9.2 System Metrics

**Resource Usage:**
- Horizontal bar charts
- Color thresholds (green/amber/red)
- Current value and max
- Update every 5 seconds

```
CPU Usage
[████████████░░░░░░░░░░] 60%

Memory Usage
[████████░░░░░░░░░░░░░░] 40%
```

**Activity Timeline:**
- Chronological event list
- Icons for event types
- Relative timestamps
- Expandable details

```
• Workflow completed (2 min ago)
• Document uploaded (15 min ago)
• Chat session started (1 hour ago)
```

### 9.3 Document Metrics

**Storage Stats:**
- Pie chart or donut chart
- Document type breakdown
- Total size and count
- Hover for details

**Search Results:**
- Relevance score bars
- Source document badges
- Preview snippets
- Similarity visualization

```
┌─────────────────────────────┐
│ api-guide.pdf (p. 42)       │
│ ████████████░░░░░░ 89%      │
│ "Authentication requires..."│
└─────────────────────────────┘
```

---

## 10. Responsive Design

### 10.1 Breakpoints

- **Mobile:** 320px - 767px (not primary focus)
- **Tablet:** 768px - 1023px (limited support)
- **Desktop:** 1024px+ (primary target)

### 10.2 Layout Adaptations

**Desktop (1024px+):**
- Full sidebar visible
- Multi-column layouts
- Larger cards and spacing
- Hover states prominent

**Tablet (768px-1023px):**
- Collapsible sidebar
- Single column in some views
- Slightly reduced spacing
- Touch-friendly targets

**Mobile (320px-767px):**
- Hidden sidebar (hamburger menu)
- Single column everywhere
- Bottom navigation bar
- Simplified interfaces

### 10.3 Component Responsiveness

**Cards:**
- Desktop: 3-4 per row
- Tablet: 2 per row
- Mobile: 1 per row

**Tables:**
- Desktop: All columns
- Tablet: Hide less important columns
- Mobile: Card view instead of table

**Modals:**
- Desktop: Centered, max-width 600px
- Tablet: Full width, 80% height
- Mobile: Full screen

---

## 11. Accessibility

### 11.1 WCAG 2.1 Level AA Compliance

**Color Contrast:**
- Text: Minimum 4.5:1 ratio
- Large text: Minimum 3:1 ratio
- UI components: Minimum 3:1 ratio

**Keyboard Navigation:**
- All interactive elements focusable
- Logical tab order
- Visible focus indicators
- Keyboard shortcuts documented

**Screen Readers:**
- Semantic HTML elements
- ARIA labels where needed
- Alt text for icons
- Live regions for updates

**Motion:**
- Respect prefers-reduced-motion
- Disable animations if requested
- Provide alternative feedback

### 11.2 ARIA Patterns

**Common Attributes:**
- `aria-label` - Element labels
- `aria-describedby` - Extended descriptions
- `aria-expanded` - Expandable elements
- `aria-live` - Dynamic content
- `aria-busy` - Loading states

**Roles:**
- `role="navigation"` - Nav menus
- `role="main"` - Main content
- `role="complementary"` - Sidebars
- `role="dialog"` - Modals
- `role="alert"` - Important messages

---

## 12. State Management

### 12.1 Zustand Store Structure

**Agent Store:**
- agents: Agent[]
- activeAgent: Agent | null
- loading: boolean
- error: string | null

**Workflow Store:**
- workflows: Workflow[]
- activeWorkflow: Workflow | null
- executionState: WorkflowState | null

**Document Store:**
- documents: Document[]
- selectedDocuments: string[]
- uploadProgress: Record<string, number>

**Chat Store:**
- sessions: ChatSession[]
- activeSessionId: string | null
- messages: Message[]
- isStreaming: boolean

**UI Store:**
- sidebarOpen: boolean
- theme: 'light' | 'dark'
- activeModal: string | null

### 12.2 Real-Time Updates

**WebSocket Events:**
- agent.started
- agent.progress
- agent.completed
- agent.failed
- workflow.progress
- chat.stream
- system.status

**Update Strategy:**
- Optimistic updates for user actions
- WebSocket updates for background tasks
- Polling fallback if WebSocket fails
- Conflict resolution for simultaneous edits

---

## Appendix A: Component Examples

### Example 1: Agent Card Component

```tsx
interface AgentCardProps {
  agent: Agent;
  onRun: (agentId: string) => void;
  onConfig: (agentId: string) => void;
}

function AgentCard({ agent, onRun, onConfig }: AgentCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {getAgentIcon(agent.type)}
            {agent.name}
          </CardTitle>
          <Badge variant={getStatusVariant(agent.status)}>
            {agent.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-zinc-600 mb-4">
          {agent.description}
        </p>
        
        {agent.status === 'running' && (
          <div className="mb-4">
            <Progress value={agent.progress * 100} />
            <p className="text-xs text-zinc-500 mt-1">
              {Math.round(agent.progress * 100)}% complete
            </p>
          </div>
        )}
        
        <div className="flex gap-2">
          <Button
            onClick={() => onRun(agent.id)}
            disabled={agent.status === 'running'}
            className="flex-1"
          >
            {agent.status === 'running' ? 'Running...' : 'Run'}
          </Button>
          
          <Button
            variant="outline"
            onClick={() => onConfig(agent.id)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Example 2: Workflow Graph Component

```tsx
interface WorkflowGraphProps {
  workflow: Workflow;
  onNodeClick: (nodeId: string) => void;
}

function WorkflowGraph({ workflow, onNodeClick }: WorkflowGraphProps) {
  return (
    <Card className="p-6">
      <div className="space-y-8">
        {workflow.nodes.map((node, index) => (
          <div key={node.id} className="relative">
            <button
              onClick={() => onNodeClick(node.id)}
              className="w-full text-left"
            >
              <Card className={cn(
                "p-4 transition-all hover:shadow-md",
                node.status === 'running' && "ring-2 ring-blue-500"
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(node.status)}
                    <div>
                      <h3 className="font-semibold">{node.name}</h3>
                      <p className="text-sm text-zinc-500">
                        {node.description}
                      </p>
                    </div>
                  </div>
                  
                  {node.status === 'running' && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-600">
                        {Math.round(node.progress * 100)}%
                      </span>
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  )}
                </div>
                
                {node.status === 'running' && (
                  <Progress 
                    value={node.progress * 100} 
                    className="mt-3"
                  />
                )}
              </Card>
            </button>
            
            {index < workflow.nodes.length - 1 && (
              <div className="flex justify-center py-2">
                <ChevronDown className="h-6 w-6 text-zinc-400" />
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
```

### Example 3: Chat Message Component

```tsx
interface MessageProps {
  message: Message;
  onCitationClick: (citation: Citation) => void;
}

function ChatMessage({ message, onCitationClick }: MessageProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn(
      "flex gap-3 mb-4",
      isUser && "flex-row-reverse"
    )}>
      <Avatar>
        <AvatarImage 
          src={isUser ? '/user.png' : '/claude.png'} 
        />
        <AvatarFallback>
          {isUser ? 'U' : 'C'}
        </AvatarFallback>
      </Avatar>
      
      <Card className={cn(
        "flex-1 max-w-[80%]",
        isUser ? "bg-blue-50" : "bg-white"
      )}>
        <CardContent className="p-4">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              citation: ({ node, ...props }) => (
                <Badge
                  variant="secondary"
                  className="cursor-pointer hover:bg-zinc-200"
                  onClick={() => onCitationClick(props)}
                >
                  {props.children}
                </Badge>
              ),
              code: ({ node, inline, ...props }) => (
                inline ? (
                  <code className="bg-zinc-100 px-1 rounded" {...props} />
                ) : (
                  <pre className="bg-zinc-900 text-white p-4 rounded-lg overflow-x-auto">
                    <code {...props} />
                  </pre>
                )
              )
            }}
          >
            {message.content}
          </ReactMarkdown>
          
          <div className="flex items-center justify-between mt-3 pt-3 border-t">
            <span className="text-xs text-zinc-500">
              {formatTimestamp(message.timestamp)}
            </span>
            
            <div className="flex gap-2">
              <Button variant="ghost" size="sm">
                <Copy className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="sm">
                <Bookmark className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Appendix B: API Integration Examples

### WebSocket Integration

```tsx
// useWebSocket hook
function useWebSocket() {
  const { wsService } = useServices();
  const { updateAgent } = useAgentStore();
  
  useEffect(() => {
    wsService.connect();
    
    wsService.on(EventType.AGENT_PROGRESS, (data) => {
      updateAgent(data.agent_id, {
        progress: data.progress,
        status: 'running'
      });
    });
    
    wsService.on(EventType.AGENT_COMPLETED, (data) => {
      updateAgent(data.agent_id, {
        status: 'completed',
        progress: 1.0
      });
    });
    
    return () => {
      wsService.disconnect();
    };
  }, []);
}
```

### Streaming Chat

```tsx
// useChat hook with streaming
function useChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentChunk, setCurrentChunk] = useState('');
  
  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    setCurrentChunk('');
    
    try {
      const response = await fetch(
        `/api/chat/sessions/${sessionId}/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: content })
        }
      );
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        setCurrentChunk(prev => prev + chunk);
      }
      
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: currentChunk,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setCurrentChunk('');
      
    } finally {
      setIsStreaming(false);
    }
  };
  
  return { messages, isStreaming, currentChunk, sendMessage };
}
```

---

## Summary

This product specification provides comprehensive guidance for building Amelia's web interface using shadcn/ui and Radix UI primitives. The document covers:

- **Complete user flows** for all major features
- **Detailed screen specifications** with ASCII wireframes
- **Component library** specifications using shadcn/ui
- **Design system** with colors, typography, spacing
- **Interaction patterns** and keyboard shortcuts
- **Data visualization** approaches
- **Accessibility** requirements
- **Code examples** for key components

The design prioritizes **developer experience** with a clean, functional aesthetic optimized for technical users. All components use shadcn/ui and Radix UI primitives, ensuring consistency, accessibility, and maintainability.

The interface is designed to be:
1. **Information-dense** without being cluttered
2. **Action-oriented** with clear CTAs
3. **Real-time** with live updates and streaming
4. **Context-aware** showing relevant information
5. **Developer-friendly** with technical aesthetics

This specification should enable an LLM to generate a complete, production-ready web interface for the Amelia platform.
