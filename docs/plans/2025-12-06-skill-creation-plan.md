# Skill Creation Plan for Amelia Dashboard Development

> **For Claude:** This is a standalone plan for creating skills in a new session. All source repositories have been cloned to `~/github/`. Use the exploration summaries below as primary source material, reading repo files only when additional detail is needed.

**Status:** Complete

**Goal:** Optimize 3 existing skills and create 7 new skills to support Phase 2.3 dashboard development, Spec Builder, and Debate Mode features.

**Skill Directory:** `.claude/skills/amelia/`

---

## Existing Skills (Require Optimization)

Three skills already exist and need to be updated to follow best practices:

| Skill | Files | Lines | Issues |
|-------|-------|-------|--------|
| `vitest-testing` | 4 | 542 | Flat structure, UPPERCASE filenames, no TOCs |
| `react-router-v7` | 5 | 782 | Flat structure, UPPERCASE filenames, no TOCs |
| `zustand-state` | 4 | 679 | Flat structure, UPPERCASE filenames, no TOCs |

### Issues to Fix

1. **Directory structure**: Move companion files to `references/` subdirectory
2. **File naming**: Rename UPPERCASE.md → lowercase.md
3. **Missing TOCs**: 8 files >100 lines need table of contents added

### Files Requiring TOC (>100 lines)

| Skill | File | Lines |
|-------|------|-------|
| vitest-testing | MOCKING.md | 114 |
| vitest-testing | PATTERNS.md | 158 |
| vitest-testing | CONFIG.md | 160 |
| react-router-v7 | LOADERS.md | 114 |
| react-router-v7 | NAVIGATION.md | 150 |
| react-router-v7 | ACTIONS.md | 190 |
| react-router-v7 | ADVANCED.md | 227 |
| zustand-state | MIDDLEWARE.md | 154 |
| zustand-state | TYPESCRIPT.md | 201 |
| zustand-state | PATTERNS.md | 218 |

---

## Phase 0: Existing Skill Optimization Details

### 0.1 vitest-testing

**Current structure:**
```
vitest-testing/
├── SKILL.md
├── MOCKING.md
├── PATTERNS.md
└── CONFIG.md
```

**Target structure:**
```
vitest-testing/
├── SKILL.md
└── references/
    ├── mocking.md      (114 lines - needs TOC)
    ├── patterns.md     (158 lines - needs TOC)
    └── config.md       (160 lines - needs TOC)
```

**Changes to SKILL.md:**
```diff
- - **Mocking**: See [MOCKING.md](MOCKING.md) for module mocking, spying, cleanup
- - **Configuration**: See [CONFIG.md](CONFIG.md) for vitest.config, setup files, coverage
- - **Patterns**: See [PATTERNS.md](PATTERNS.md) for timers, snapshots, anti-patterns
+ - **Mocking**: See [references/mocking.md](references/mocking.md) for module mocking, spying, cleanup
+ - **Configuration**: See [references/config.md](references/config.md) for vitest.config, setup files, coverage
+ - **Patterns**: See [references/patterns.md](references/patterns.md) for timers, snapshots, anti-patterns
```

### 0.2 react-router-v7

**Current structure:**
```
react-router-v7/
├── SKILL.md
├── NAVIGATION.md
├── ADVANCED.md
├── ACTIONS.md
└── LOADERS.md
```

**Target structure:**
```
react-router-v7/
├── SKILL.md
└── references/
    ├── loaders.md      (114 lines - needs TOC)
    ├── navigation.md   (150 lines - needs TOC)
    ├── actions.md      (190 lines - needs TOC)
    └── advanced.md     (227 lines - needs TOC)
```

**Changes to SKILL.md:**
```diff
- - **Data Loading**: See [LOADERS.md](LOADERS.md) for loader patterns, parallel loading, search params
- - **Mutations**: See [ACTIONS.md](ACTIONS.md) for actions, Form, fetchers, validation
- - **Navigation**: See [NAVIGATION.md](NAVIGATION.md) for Link, NavLink, programmatic nav
- - **Advanced**: See [ADVANCED.md](ADVANCED.md) for error boundaries, protected routes, lazy loading
+ - **Data Loading**: See [references/loaders.md](references/loaders.md) for loader patterns, parallel loading, search params
+ - **Mutations**: See [references/actions.md](references/actions.md) for actions, Form, fetchers, validation
+ - **Navigation**: See [references/navigation.md](references/navigation.md) for Link, NavLink, programmatic nav
+ - **Advanced**: See [references/advanced.md](references/advanced.md) for error boundaries, protected routes, lazy loading
```

### 0.3 zustand-state

**Current structure:**
```
zustand-state/
├── SKILL.md
├── MIDDLEWARE.md
├── PATTERNS.md
└── TYPESCRIPT.md
```

**Target structure:**
```
zustand-state/
├── SKILL.md
└── references/
    ├── middleware.md   (154 lines - needs TOC)
    ├── patterns.md     (218 lines - needs TOC)
    └── typescript.md   (201 lines - needs TOC)
```

**Changes to SKILL.md:**
```diff
- - **Middleware**: See [MIDDLEWARE.md](MIDDLEWARE.md) for persist, devtools, immer
- - **Patterns**: See [PATTERNS.md](PATTERNS.md) for slices, testing, best practices
- - **TypeScript**: See [TYPESCRIPT.md](TYPESCRIPT.md) for advanced typing patterns
+ - **Middleware**: See [references/middleware.md](references/middleware.md) for persist, devtools, immer
+ - **Patterns**: See [references/patterns.md](references/patterns.md) for slices, testing, best practices
+ - **TypeScript**: See [references/typescript.md](references/typescript.md) for advanced typing patterns
```

### TOC Template

Add this TOC format at the top of each file >100 lines (after any frontmatter):

```markdown
## Contents

- [Section 1 Name](#section-1-name)
- [Section 2 Name](#section-2-name)
- [Section 3 Name](#section-3-name)
...

---
```

---

## Prerequisites

The following repositories are available at `~/github/`:
- `ui` - shadcn/ui (component patterns, CVA, registry)
- `ai-elements` - Vercel workflow components
- `xyflow` - React Flow (custom nodes/edges)
- `tailwindcss` - Tailwind v4 (CSS-first config)
- `vercel-ai-sdk` - AI SDK (useChat, streaming)
- `docling` - Document parsing
- `sqlite-vec` - Vector search extension

---

## Skill Structure Pattern

Each skill follows the canonical structure from [Claude platform best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

```
.claude/skills/amelia/{skill-name}/
├── SKILL.md              # Main entry with YAML frontmatter (required)
├── references/           # Documentation loaded on-demand
│   ├── {topic1}.md       # Detailed topic file (lowercase)
│   ├── {topic2}.md       # Detailed topic file (lowercase)
│   └── ...
└── scripts/              # Utility scripts (optional, if needed)
    └── {script}.py
```

**SKILL.md frontmatter format:**
```yaml
---
name: {skill-name}
description: {Brief description}. Use when {trigger conditions}. Triggers on {keywords}.
---
```

**Frontmatter rules:**
- `name`: Max 64 chars, lowercase letters/numbers/hyphens only, no reserved words (anthropic, claude)
- `description`: Max 1024 chars, must include BOTH what the skill does AND when to use it

**Content guidelines:**
- SKILL.md: Quick reference, key patterns, decision tables, links to references (keep under 500 lines)
- Reference files: Deep dives on specific topics, extensive code examples (use lowercase filenames)
- For reference files >100 lines: Include table of contents at top
- All code examples must be TypeScript with proper typing
- Focus on patterns relevant to Amelia's aviation-themed dashboard
- Write in third person ("Processes..." not "I can help you...")

**Progressive disclosure:**
1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - Loaded when skill triggers (<5k words)
3. **Reference files** - Loaded as needed by Claude

---

## Skill 1: shadcn-ui

**Directory:** `.claude/skills/amelia/shadcn-ui/`

**Structure:**
```
shadcn-ui/
├── SKILL.md
└── references/
    ├── components.md
    ├── cva.md
    └── patterns.md
```

**Files to create:**

### SKILL.md
```yaml
---
name: shadcn-ui
description: shadcn/ui component patterns with Radix primitives and Tailwind styling. Use when building UI components, using CVA variants, implementing compound components, or styling with data-slot attributes. Triggers on shadcn, cva, cn(), data-slot, Radix, Button, Card, Dialog, VariantProps.
---
```

**Content sections:**
- Quick reference: cn() utility, basic CVA pattern
- Component anatomy: props typing, asChild pattern
- data-slot usage for CSS targeting
- Decision table: When to use each pattern
- Links to reference files

### references/components.md
**Content:**
- Button with variants (default, destructive, outline, ghost, link)
- Card compound component (Card, CardHeader, CardTitle, CardContent, CardFooter)
- Badge with status variants
- Input, Label, Textarea patterns
- Dialog/Sheet modal patterns
- Each with full TypeScript types

### references/cva.md
**Content:**
- Basic variant definition
- Compound variants
- Default variants
- Responsive variants with container queries
- Integration with cn() utility
- VariantProps type extraction

### references/patterns.md
**Content:**
- Compound component pattern (Card, Form, Sidebar)
- asChild/Slot polymorphism
- Controlled vs uncontrolled state
- Context for complex components (Sidebar, Form)
- data-slot CSS targeting patterns
- has() selector usage

**Source files to reference:**
- `~/github/ui/apps/v4/lib/utils.ts` (cn utility)
- `~/github/ui/apps/v4/registry/new-york-v4/ui/button.tsx`
- `~/github/ui/apps/v4/registry/new-york-v4/ui/card.tsx`
- `~/github/ui/apps/v4/registry/new-york-v4/ui/badge.tsx`
- `~/github/ui/apps/v4/registry/new-york-v4/ui/sidebar.tsx`

---

## Skill 2: tailwind-v4

**Directory:** `.claude/skills/amelia/tailwind-v4/`

**Structure:**
```
tailwind-v4/
├── SKILL.md
└── references/
    ├── setup.md
    ├── theming.md
    └── dark-mode.md
```

**Files to create:**

### SKILL.md
```yaml
---
name: tailwind-v4
description: Tailwind CSS v4 with CSS-first configuration and design tokens. Use when setting up Tailwind v4, defining theme variables, using OKLCH colors, or configuring dark mode. Triggers on @theme, @tailwindcss/vite, oklch, CSS variables, --color-, tailwind v4.
---
```

**Content sections:**
- Quick reference: Vite plugin setup, @import pattern
- @theme inline directive basics
- OKLCH color format explanation
- Key differences from v3
- Links to reference files

### references/setup.md
**Content:**
- Vite plugin configuration (NOT PostCSS)
- package.json dependencies
- tsconfig.json with @types/node
- index.css with @import 'tailwindcss'
- Why no tailwind.config.js or postcss.config.js

### references/theming.md
**Content:**
- @theme directive modes (default, inline, reference)
- CSS variable naming conventions
- Aviation theme color palette in OKLCH
- Two-tier variable system (semantic + tailwind-mapped)
- Custom fonts configuration
- Animation keyframes

### references/dark-mode.md
**Content:**
- Media query strategy (prefers-color-scheme)
- Class-based strategy (.dark)
- Attribute-based strategy (data-theme)
- Theme switching implementation
- Respecting prefers-reduced-motion

**Source files to reference:**
- `~/github/tailwindcss/packages/tailwindcss/theme.css`
- `~/github/tailwindcss/packages/@tailwindcss-vite/src/index.ts`
- `~/github/tailwindcss/playgrounds/vite/vite.config.ts`

---

## Skill 3: react-flow

**Directory:** `.claude/skills/amelia/react-flow/`

**Structure:**
```
react-flow/
├── SKILL.md
└── references/
    ├── custom-nodes.md
    ├── custom-edges.md
    ├── viewport.md
    └── events.md
```

**Files to create:**

### SKILL.md
```yaml
---
name: react-flow
description: React Flow (@xyflow/react) for workflow visualization with custom nodes and edges. Use when building graph visualizations, creating custom workflow nodes, implementing edge labels, or controlling viewport. Triggers on ReactFlow, @xyflow/react, Handle, NodeProps, EdgeProps, useReactFlow, fitView.
---
```

**Content sections:**
- Quick reference: Basic ReactFlow setup
- Node and edge type definitions
- Key props overview
- Links to reference files

### references/custom-nodes.md
**Content:**
- NodeProps typing pattern
- Handle component (target/source)
- Dynamic handles with useUpdateNodeInternals
- Styling nodes (CSS, Tailwind, inline)
- Aviation map pin node example
- Status-based styling (beacon glow)

### references/custom-edges.md
**Content:**
- EdgeProps typing pattern
- getBezierPath, getStraightPath utilities
- EdgeLabelRenderer for interactive labels
- Animated edges (dash animation, moving circle)
- BaseEdge usage
- Time label edge example

### references/viewport.md
**Content:**
- useReactFlow() hook methods
- fitView() with options
- setViewport(), zoomIn(), zoomOut()
- screenToFlowPosition()
- Save/restore viewport state
- Programmatic pan to node

### references/events.md
**Content:**
- Node events (click, drag, hover, context menu)
- Edge events (click, reconnect)
- Connection events (onConnect, onConnectStart, onConnectEnd)
- Selection events (useOnSelectionChange)
- Viewport events (useOnViewportChange)

**Source files to reference:**
- `~/github/xyflow/packages/react/src/types/`
- `~/github/xyflow/packages/react/src/components/Handle/`
- `~/github/xyflow/packages/react/src/hooks/useReactFlow.ts`
- `~/github/xyflow/examples/react/src/examples/`

---

## Skill 4: ai-elements

**Directory:** `.claude/skills/amelia/ai-elements/`

**Structure:**
```
ai-elements/
├── SKILL.md
└── references/
    ├── conversation.md
    ├── prompt-input.md
    ├── workflow.md
    └── visualization.md
```

**Files to create:**

### SKILL.md
```yaml
---
name: ai-elements
description: Vercel AI Elements for workflow UI components. Use when building chat interfaces, displaying tool execution, showing reasoning/thinking, or creating job queues. Triggers on ai-elements, Queue, Confirmation, Tool, Reasoning, Shimmer, Loader, Message, Conversation, PromptInput.
---
```

**Content sections:**
- Quick reference: Installation via shadcn registry
- Component categories overview
- Integration with shadcn/ui theming
- Links to reference files

### references/conversation.md
**Content:**
- Conversation, ConversationContent, ConversationEmptyState
- Message, MessageContent, MessageResponse, MessageActions
- MessageAttachment for files/images
- MessageBranch for alternative responses
- Auto-scroll behavior (use-stick-to-bottom)

### references/prompt-input.md
**Content:**
- PromptInput with file attachments
- PromptInputTextarea (auto-expanding)
- PromptInputSubmit (status-aware icons)
- PromptInputAttachments display
- PromptInputProvider for global state
- Drag-and-drop file handling
- Speech input (Web Speech API)

### references/workflow.md
**Content:**
- Queue, QueueItem, QueueSection patterns
- Tool component with state handling
- Confirmation for approval workflows
- Tool states: input-streaming → output-available
- Reasoning with auto-collapse
- Shimmer loading animation
- Loader spinner

### references/visualization.md
**Content:**
- Canvas (ReactFlow wrapper)
- Node with handles
- Edge (Temporary, Animated)
- Controls, Panel, Toolbar
- Integration with custom aviation nodes

**Source files to reference:**
- `~/github/ai-elements/packages/elements/src/`
- `~/github/ai-elements/packages/elements/src/queue.tsx`
- `~/github/ai-elements/packages/elements/src/tool.tsx`
- `~/github/ai-elements/packages/elements/src/confirmation.tsx`

---

## Skill 5: vercel-ai-sdk

**Directory:** `.claude/skills/amelia/vercel-ai-sdk/`

**Structure:**
```
vercel-ai-sdk/
├── SKILL.md
└── references/
    ├── use-chat.md
    ├── messages.md
    ├── streaming.md
    └── tools.md
```

**Files to create:**

### SKILL.md
```yaml
---
name: vercel-ai-sdk
description: Vercel AI SDK for building chat interfaces with streaming. Use when implementing useChat hook, handling tool calls, streaming responses, or building chat UI. Triggers on useChat, @ai-sdk/react, UIMessage, ChatStatus, streamText, toUIMessageStreamResponse.
---
```

**Content sections:**
- Quick reference: useChat basic usage
- ChatStatus states (ready, submitted, streaming, error)
- Message structure overview
- Links to reference files

### references/use-chat.md
**Content:**
- Full useChat options and return values
- sendMessage, stop, regenerate methods
- Error handling (error, clearError)
- onFinish, onError callbacks
- experimental_throttle for performance
- Custom transport (DefaultChatTransport)

### references/messages.md
**Content:**
- UIMessage structure (id, role, parts)
- Part types: text, file, tool-*, reasoning
- TextUIPart with streaming state
- ToolUIPart with full state machine
- FileUIPart for attachments
- Type-safe message definitions

### references/streaming.md
**Content:**
- Server-side: streamText + toUIMessageStreamResponse
- UIMessageChunk types
- SSE format and parsing
- Tool execution flow
- Backpressure handling

### references/tools.md
**Content:**
- Server-side tool definition (inputSchema, execute)
- Client-side tools (no execute)
- onToolCall handler
- addToolOutput for client tools
- addToolApprovalResponse for approval flow
- Tool state rendering patterns

**Source files to reference:**
- `~/github/vercel-ai-sdk/packages/react/src/use-chat.ts`
- `~/github/vercel-ai-sdk/packages/ai/src/ui/ui-messages.ts`
- `~/github/vercel-ai-sdk/packages/ai/src/ui-message-stream/`
- `~/github/vercel-ai-sdk/examples/next-openai/`

---

## Skill 6: docling

**Directory:** `.claude/skills/amelia/docling/`

**Structure:**
```
docling/
├── SKILL.md
├── references/
│   ├── parsing.md
│   ├── batch.md
│   ├── chunking.md
│   └── output.md
└── scripts/               # Optional utility scripts
    └── convert_batch.py   # Batch conversion helper
```

**Files to create:**

### SKILL.md
```yaml
---
name: docling
description: Docling document parser for PDF, DOCX, and other formats. Use when parsing documents, extracting text, chunking for RAG, or batch processing files. Triggers on docling, DocumentConverter, convert, export_to_markdown, HierarchicalChunker.
---
```

**Content sections:**
- Quick reference: Basic conversion
- Supported formats list
- Output formats (Markdown, HTML, JSON)
- Links to reference files

### references/parsing.md
**Content:**
- DocumentConverter initialization
- Single file conversion
- URL conversion
- Binary stream conversion (BytesIO)
- Format-specific options (PdfPipelineOptions)
- OCR configuration

### references/batch.md
**Content:**
- convert_all() for multiple files
- ConversionStatus handling (SUCCESS, PARTIAL_SUCCESS, FAILURE)
- Error handling and recovery
- ThreadPoolExecutor concurrency
- Resource limits (max_file_size, max_num_pages)

### references/chunking.md
**Content:**
- HierarchicalChunker (structure-aware)
- HybridChunker (semantic + size)
- Chunk metadata access
- Integration with embeddings
- RAG pipeline patterns

### references/output.md
**Content:**
- DoclingDocument structure
- export_to_markdown()
- export_to_html()
- export_to_dict() / export_to_json()
- save_as_* methods
- Accessing document elements (iter_all)

### scripts/convert_batch.py (optional)
**Purpose:** Batch convert documents with progress reporting and error handling
**Usage:** `python scripts/convert_batch.py input_dir/ output_dir/`

**Source files to reference:**
- `~/github/docling/docling/document_converter.py`
- `~/github/docling/docling/chunking/`
- `~/github/docling/examples/`
- `~/github/docling/README.md`

---

## Skill 7: sqlite-vec

**Directory:** `.claude/skills/amelia/sqlite-vec/`

**Structure:**
```
sqlite-vec/
├── SKILL.md
├── references/
│   ├── setup.md
│   ├── tables.md
│   ├── queries.md
│   └── operations.md
└── scripts/               # Optional utility scripts
    ├── init_db.py         # Database initialization helper
    └── knn_search.py      # KNN query helper
```

**Files to create:**

### SKILL.md
```yaml
---
name: sqlite-vec
description: sqlite-vec for vector similarity search in SQLite. Use when storing embeddings, performing KNN queries, or building semantic search. Triggers on sqlite-vec, vec0, MATCH, vec_distance, partition key, float[N], serialize_float32.
---
```

**Content sections:**
- Quick reference: Extension loading, basic query
- Vector types (float32, int8, bit)
- Binary serialization format
- Links to reference files

### references/setup.md
**Content:**
- Python binding installation
- Extension loading pattern
- serialize_float32() helper
- NumPy integration (register_numpy)
- Connection setup

### references/tables.md
**Content:**
- vec0 virtual table creation
- Column types: float[N], int8[N], bit[N]
- Metadata columns (searchable)
- Partition key columns (sharding)
- Auxiliary columns (+prefix, stored only)
- chunk_size tuning

### references/queries.md
**Content:**
- KNN query syntax (WHERE MATCH, AND k=N)
- Distance functions (L2, cosine, hamming)
- Metadata filtering in KNN
- Partition key filtering
- Point queries (by rowid)
- Full table scan

### references/operations.md
**Content:**
- Vector constructor functions (vec_f32, vec_int8, vec_bit)
- Arithmetic (vec_add, vec_sub)
- vec_normalize, vec_slice
- vec_quantize_binary, vec_quantize_i8
- vec_each for iteration
- Batch insert patterns

### scripts/init_db.py (optional)
**Purpose:** Initialize sqlite-vec database with common table schemas
**Usage:** `python scripts/init_db.py db_path dimensions`

### scripts/knn_search.py (optional)
**Purpose:** Perform KNN queries with proper serialization
**Usage:** `python scripts/knn_search.py db_path query_vector k`

**Source files to reference:**
- `~/github/sqlite-vec/bindings/python/`
- `~/github/sqlite-vec/examples/simple-python/`
- `~/github/sqlite-vec/examples/python-recipes/`
- `~/github/sqlite-vec/ARCHITECTURE.md`

---

## Implementation Order

### Phase 0: Optimize Existing Skills (Priority 0)

Before creating new skills, optimize the 3 existing skills to follow best practices:

| Order | Skill | Changes Required |
|-------|-------|------------------|
| 0.1 | vitest-testing | Restructure + add TOCs to 3 files |
| 0.2 | react-router-v7 | Restructure + add TOCs to 4 files |
| 0.3 | zustand-state | Restructure + add TOCs to 3 files |

**For each existing skill:**
1. Create `references/` subdirectory
2. Move and rename companion files:
   - `MOCKING.md` → `references/mocking.md`
   - `PATTERNS.md` → `references/patterns.md`
   - etc.
3. Add table of contents to files >100 lines
4. Update links in SKILL.md to point to `references/`
5. Verify against checklist

### Phase 1: Core Dashboard Skills (Priority 1)

| Order | Skill | Reason |
|-------|-------|--------|
| 1 | tailwind-v4 | Foundation - theming affects all components |
| 2 | shadcn-ui | Foundation - all UI components depend on this |
| 3 | react-flow | Custom WorkflowCanvas needs this |
| 4 | ai-elements | Queue, Confirmation, Tool components |

### Phase 2: Spec Builder Skills (Priority 2)

| Order | Skill | Reason |
|-------|-------|--------|
| 5 | vercel-ai-sdk | Chat interface for Spec Builder |
| 6 | docling | Document parsing for Spec Builder |
| 7 | sqlite-vec | Vector search for Spec Builder |

---

## Verification Checklist

After creating each skill, verify against [Claude platform best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

### Core Quality
- [ ] SKILL.md has valid YAML frontmatter (name + description only)
- [ ] `name`: max 64 chars, lowercase/numbers/hyphens only
- [ ] `description`: max 1024 chars, includes BOTH what it does AND when to use it
- [ ] Description written in third person ("Processes..." not "I can help...")
- [ ] SKILL.md body under 500 lines
- [ ] Quick reference has working code examples
- [ ] All TypeScript examples have proper types
- [ ] Reference files use lowercase filenames
- [ ] Reference files >100 lines have table of contents
- [ ] All reference files linked from SKILL.md with clear usage context
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout

### Structure & Organization
- [ ] Uses `references/` subdirectory for companion files
- [ ] Uses `scripts/` subdirectory for utility scripts (if applicable)
- [ ] References are one level deep (no nested references)
- [ ] Progressive disclosure pattern followed
- [ ] No extraneous documentation files (README, CHANGELOG, etc.)

### Testing & Evaluation
- [ ] Code examples tested/verified against source repos
- [ ] Patterns relevant to Amelia's aviation theme where applicable
- [ ] At least 3 usage scenarios mentally validated
- [ ] Tested that description triggers skill appropriately

---

## Session Instructions

When starting the new session, provide these instructions:

```
I need to optimize existing skills and create new skills for the Amelia dashboard project.

Read the plan at docs/plans/2025-12-06-skill-creation-plan.md

## Phase 0: Optimize Existing Skills (START HERE)

Three skills exist at .claude/skills/amelia/ that need optimization:
- vitest-testing
- react-router-v7
- zustand-state

For each existing skill:
1. Create `references/` subdirectory
2. Move and rename companion files (UPPERCASE.md → references/lowercase.md)
3. Add table of contents to files >100 lines
4. Update links in SKILL.md to point to references/
5. Verify against checklist

Start with vitest-testing (Phase 0, Order 0.1).

## Phase 1-2: Create New Skills (After Phase 0)

The source repositories are cloned at ~/github/:
- ui (shadcn/ui)
- ai-elements
- xyflow (React Flow)
- tailwindcss (v4)
- vercel-ai-sdk
- docling
- sqlite-vec

For each new skill:
1. Create the directory structure:
   .claude/skills/amelia/{skill-name}/
   ├── SKILL.md
   └── references/
       └── {topic}.md (lowercase filenames)
2. Write SKILL.md with proper YAML frontmatter (name + description only)
3. Write reference files with detailed code examples
4. Reference source files from ~/github/ for accurate patterns
5. Run the verification checklist before marking complete

Key best practices to follow:
- SKILL.md body < 500 lines (use progressive disclosure)
- Description: max 1024 chars, include WHAT + WHEN to use
- Reference files > 100 lines need table of contents
- Use references/ subdirectory (not flat structure)
- Write in third person ("Processes..." not "I can help...")
```

---

## Exploration Summaries (Reference)

### shadcn/ui Key Findings
- cn() = clsx + tailwind-merge in utils.ts
- CVA for variants with defaultVariants, compoundVariants
- data-slot on every component for CSS hooks
- asChild pattern uses @radix-ui/react-slot
- TypeScript: React.ComponentProps<> + VariantProps<typeof variants>
- 54 components in registry/new-york-v4/ui/

### Tailwind v4 Key Findings
- No tailwind.config.js - CSS-first with @theme
- @tailwindcss/vite plugin (NOT PostCSS)
- @theme inline maps CSS vars to utilities
- OKLCH colors: oklch(L% C H)
- Dark mode via media query, class, or attribute

### React Flow Key Findings
- NodeProps<Node<Data, 'type'>> for custom nodes
- Handle component with type="target"/"source"
- getBezierPath() for edge paths
- EdgeLabelRenderer for interactive labels
- useReactFlow() for viewport control
- useUpdateNodeInternals() for dynamic handles

### ai-elements Key Findings
- 30+ components for AI interfaces
- Queue, Confirmation, Tool, Reasoning core components
- Tool states: input-streaming → output-available
- Integrates with shadcn/ui theming
- Canvas wraps ReactFlow for workflows

### Vercel AI SDK Key Findings
- useChat returns messages, status, sendMessage, stop, regenerate
- ChatStatus: 'ready' | 'submitted' | 'streaming' | 'error'
- UIMessage has parts array (text, tool-*, file, reasoning)
- streamText().toUIMessageStreamResponse() for server
- onToolCall, addToolOutput for client-side tools

### Docling Key Findings
- 15+ formats: PDF, DOCX, PPTX, HTML, MD, images
- DocumentConverter().convert() → doc.export_to_markdown()
- HierarchicalChunker, HybridChunker for RAG
- convert_all() for batch with ThreadPoolExecutor
- Sync API only (no native async)

### sqlite-vec Key Findings
- sqlite_vec.load(db) to enable
- vec0 virtual table with float[N], int8[N], bit[N]
- KNN: WHERE embedding MATCH ? AND k=10 ORDER BY distance
- partition key for multi-tenant sharding
- struct.pack for binary serialization
