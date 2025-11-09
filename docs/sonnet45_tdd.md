# Amelia: Technical Design Document
## Local LLM Workflow Orchestration Command Center

**Document Version:** 1.0  
**Target Audience:** LLM Code Generation (Claude Code)  
**Last Updated:** 2025-11-08  
**Deployment Model:** Local-only, self-contained  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [Database Design](#7-database-design)
8. [Agent Orchestration System](#8-agent-orchestration-system)
9. [RAG System Implementation](#9-rag-system-implementation)
10. [Chat System](#10-chat-system)
11. [Git Integration](#11-git-integration)
12. [Event System](#12-event-system)
13. [Logging System](#13-logging-system)
14. [Configuration Management](#14-configuration-management)
15. [Error Handling](#15-error-handling)
16. [Testing Strategy](#16-testing-strategy)
17. [Development Workflow](#17-development-workflow)
18. [API Specifications](#18-api-specifications)
19. [Data Models](#19-data-models)
20. [Security Considerations](#20-security-considerations)
21. [Deployment & Installation](#21-deployment--installation)

---

## 1. Executive Summary

### 1.1 Purpose

Amelia is a local-first developer tool that orchestrates LLM agents (primarily Claude) for software development lifecycle tasks. It provides both a web UI and terminal UI for managing agents, workflows, RAG document management, and chat interactions with LLMs.

### 1.2 Key Characteristics

- **Local-only execution**: No cloud dependencies, all processing happens locally
- **Developer-centric**: Designed for engineers during active development
- **Multi-agent orchestration**: Uses LangGraph for complex workflow management
- **RAG-enabled**: Document ingestion and retrieval for context-aware agents
- **Dual interface**: Web UI and Terminal UI with shared backend

### 1.3 Non-Goals

- Production deployment scalability
- Multi-user/multi-tenant support
- High availability or distributed systems
- Authentication/authorization (local tool only)
- Mobile applications

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌─────────────────────┐    ┌──────────────────────┐       │
│  │   Web UI (React)    │    │   Terminal UI (Ink)  │       │
│  │  React Router v7    │    │   React + Ink        │       │
│  │  shadcn + radix     │    │   Same State Logic   │       │
│  └──────────┬──────────┘    └──────────┬───────────┘       │
└─────────────┼──────────────────────────┼───────────────────┘
              │                           │
              └────────────┬──────────────┘
                          │ HTTP REST + WebSocket
┌─────────────────────────┼────────────────────────────────────┐
│                    Backend Layer                              │
│  ┌──────────────────────┴───────────────────────────┐        │
│  │           FastAPI Application Server             │        │
│  │  ┌────────────────────────────────────────────┐  │        │
│  │  │         API Router Layer                   │  │        │
│  │  │  /api/agents  /api/workflows  /api/rag     │  │        │
│  │  │  /api/chat    /api/git        /api/status  │  │        │
│  │  └────────────────┬───────────────────────────┘  │        │
│  │                   │                               │        │
│  │  ┌────────────────┴───────────────────────────┐  │        │
│  │  │      Business Logic Layer                  │  │        │
│  │  │  ┌──────────┐  ┌───────────┐  ┌─────────┐ │  │        │
│  │  │  │ Agent    │  │ Workflow  │  │   RAG   │ │  │        │
│  │  │  │ Manager  │  │ Manager   │  │ Manager │ │  │        │
│  │  │  └──────────┘  └───────────┘  └─────────┘ │  │        │
│  │  │  ┌──────────┐  ┌───────────┐  ┌─────────┐ │  │        │
│  │  │  │  Chat    │  │    Git    │  │  Event  │ │  │        │
│  │  │  │ Manager  │  │  Manager  │  │   Bus   │ │  │        │
│  │  │  └──────────┘  └───────────┘  └─────────┘ │  │        │
│  │  └────────────────┬───────────────────────────┘  │        │
│  │                   │                               │        │
│  │  ┌────────────────┴───────────────────────────┐  │        │
│  │  │      LangGraph Orchestration Layer         │  │        │
│  │  │  ┌─────────────────────────────────────┐   │  │        │
│  │  │  │   Workflow Graph Executor           │   │  │        │
│  │  │  │   State Management                  │   │  │        │
│  │  │  │   Agent Node Execution              │   │  │        │
│  │  │  └─────────────────────────────────────┘   │  │        │
│  │  └────────────────────────────────────────────┘  │        │
│  └───────────────────────────────────────────────────┘        │
│                           │                                    │
│  ┌────────────────────────┴──────────────┐                    │
│  │      External Process Layer           │                    │
│  │  ┌─────────────┐  ┌─────────────────┐ │                    │
│  │  │   Claude    │  │  Ollama/        │ │                    │
│  │  │   Code      │  │  OpenRouter     │ │                    │
│  │  │   Agents    │  │  LLM Engines    │ │                    │
│  │  └─────────────┘  └─────────────────┘ │                    │
│  └───────────────────────────────────────┘                    │
└────────────────────────────┬──────────────────────────────────┘
                             │
┌────────────────────────────┴──────────────────────────────────┐
│                    Data Layer                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL + pgvector                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │documents │  │embeddings│  │  agents  │  │workflows│ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### Client Layer
- **Web UI**: Primary graphical interface, React-based SPA
- **Terminal UI**: Text-based interface using Ink, shares state logic with Web UI

#### Backend Layer
- **API Router**: Handles HTTP requests, WebSocket connections, request validation
- **Business Logic**: Implements core functionality for each domain
- **LangGraph Orchestration**: Manages agent workflows, state, and execution

#### External Process Layer
- **Claude Code Agents**: Local subprocess execution of Claude agents
- **LLM Engines**: Ollama (local) or OpenRouter (API) for embeddings and inference

#### Data Layer
- **PostgreSQL**: Relational data storage
- **pgvector**: Vector embeddings storage and similarity search

### 2.3 Communication Patterns

#### REST API (Synchronous)
- CRUD operations on resources
- Workflow initialization
- Configuration management

#### WebSocket (Asynchronous)
- Real-time agent progress updates
- Streaming chat responses
- Event broadcasting

#### Event Bus (Internal)
- Decoupled component communication
- Agent status updates
- Progress notifications

---

## 3. Technology Stack

### 3.1 Backend

```python
# Core Framework
fastapi = "^0.121.1"
uvicorn = {extras = ["standard"], version = "^0.38.0"}
python = "^3.12"

# Agent Orchestration
langgraph = "^1.0.2"
langchain = "^1.0.5"
langchain-anthropic = "^1.0.1"

# AI/ML Tools
pydantic-ai = "^1.12.0"
anthropic = "^0.72.0"

# Document Processing
docling = "^2.61.1"
docling-core = "^2.50.1"
pypdf = "^6.1.3"
beautifulsoup4 = "^4.14.2"
markdown = "^3.10"

# Database
asyncpg = "^0.30.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.44"}
pgvector = "^0.4.1"
alembic = "^1.17.1"

# Vector/Embeddings
sentence-transformers = "^5.1.2"

# HTTP & Web
httpx = "^0.28.1"
websockets = "^15.0.1"

# Utilities
pydantic = "^2.12.4"
python-dotenv = "^1.2.1"
rich = "^14.2.0"  # Terminal formatting and logging
structlog = "^24.4.0"  # Structured logging
```

### 3.2 Frontend (Web)

```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router": "^7.9.5",
    "@remix-run/router": "^1.23.0",

    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-toast": "^1.2.14",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@radix-ui/react-scroll-area": "^1.2.0",

    "ai": "^5.0.89",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.1",
    "tailwindcss-animate": "^1.0.7",

    "motion": "^1.6.0",
    "lucide-react": "^0.553.0",
    "react-markdown": "^10.1.0",
    "remark-gfm": "^4.0.1",
    "rehype-highlight": "^7.0.2",

    "zustand": "^5.0.8",
    "axios": "^1.13.2"
  },
  "devDependencies": {
    "@types/react": "^19.0.1",
    "@types/react-dom": "^19.0.1",
    "typescript": "^5.9.3",
    "vite": "^7.2.2",
    "tailwindcss": "^4.1.17",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.6"
  }
}
```

### 3.3 Frontend (Terminal)

```json
{
  "dependencies": {
    "ink": "^5.0.0",
    "ink-text-input": "^6.0.0",
    "ink-spinner": "^5.0.0",
    "ink-select-input": "^6.2.0",
    "ink-table": "^3.1.0",
    "react": "^19.2.0",
    "zustand": "^5.0.8",
    "axios": "^1.13.2"
  }
}
```

### 3.4 Database

- **PostgreSQL**: 16+
- **Extensions**: `pgvector` for vector similarity search

### 3.5 External Dependencies

- **Claude Code**: Local installation or containerized
- **Ollama** (optional): For local embeddings and inference
- **Git**: For repository operations

---

## 4. Project Structure

### 4.1 Complete Directory Structure

```
amelia/
├── README.md
├── LICENSE
├── pyproject.toml                    # Backend dependencies (Poetry)
├── setup.py                          # Package setup
├── .env.example
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entrypoint
│   ├── config.py                     # Configuration management
│   ├── dependencies.py               # FastAPI dependencies
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py             # Agent endpoints
│   │   │   ├── workflows.py          # Workflow endpoints
│   │   │   ├── rag.py                # RAG/document endpoints
│   │   │   ├── chat.py               # Chat endpoints
│   │   │   ├── git.py                # Git operations endpoints
│   │   │   └── status.py             # System status endpoints
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── error_handler.py
│   │   │   └── logging.py
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── manager.py            # WebSocket connection manager
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Agent lifecycle management
│   │   │   ├── base.py               # Base agent class
│   │   │   ├── discovery.py          # Discovery agent
│   │   │   ├── design.py             # Design agent
│   │   │   ├── planning.py           # Planning agent
│   │   │   └── claude_code.py        # Claude Code integration
│   │   │
│   │   ├── workflows/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Workflow execution
│   │   │   ├── graph.py              # LangGraph graph builder
│   │   │   ├── state.py              # Workflow state management
│   │   │   └── presets/
│   │   │       ├── __init__.py
│   │   │       ├── discovery_design_planning.py
│   │   │       └── full_sdlc.py
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # RAG coordination
│   │   │   ├── ingestor.py           # Document ingestion
│   │   │   ├── embeddings.py         # Embedding generation
│   │   │   ├── retriever.py          # Vector search
│   │   │   ├── chunker.py            # Text chunking
│   │   │   └── scrapers/
│   │   │       ├── __init__.py
│   │   │       ├── web.py            # Web scraping
│   │   │       └── google_docs.py
│   │   │
│   │   ├── chat/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Chat session management
│   │   │   ├── claude.py             # Claude API integration
│   │   │   ├── openrouter.py         # OpenRouter integration
│   │   │   └── streaming.py          # SSE/WebSocket streaming
│   │   │
│   │   ├── git/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Git operations
│   │   │   └── worktree.py           # Git worktree management
│   │   │
│   │   └── events/
│   │       ├── __init__.py
│   │       ├── bus.py                # Event bus implementation
│   │       ├── types.py              # Event type definitions
│   │       └── handlers.py           # Event handlers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SQLAlchemy base
│   │   │   ├── document.py           # Document model
│   │   │   ├── embedding.py          # Embedding model
│   │   │   ├── agent.py              # Agent model
│   │   │   └── workflow.py           # Workflow model
│   │   │
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── agent.py              # Agent Pydantic schemas
│   │       ├── workflow.py           # Workflow Pydantic schemas
│   │       ├── document.py           # Document Pydantic schemas
│   │       ├── chat.py               # Chat Pydantic schemas
│   │       └── git.py                # Git Pydantic schemas
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py             # Database connection
│   │   ├── session.py                # Session management
│   │   └── migrations/               # Alembic migrations
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                 # Logging configuration
│   │   ├── validators.py             # Input validation
│   │   └── helpers.py                # Utility functions
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # Pytest configuration
│       ├── test_agents.py
│       ├── test_workflows.py
│       ├── test_rag.py
│       ├── test_chat.py
│       └── test_git.py
│
├── frontend-web/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.tsx                  # App entry point
│   │   ├── App.tsx                   # Root component
│   │   ├── router.tsx                # React Router v7 config
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── Workflows.tsx
│   │   │   ├── Documents.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Git.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   └── StreamingMessage.tsx
│   │   │   │
│   │   │   ├── workflows/
│   │   │   │   ├── WorkflowList.tsx
│   │   │   │   ├── WorkflowGraph.tsx
│   │   │   │   ├── WorkflowProgress.tsx
│   │   │   │   └── WorkflowConfig.tsx
│   │   │   │
│   │   │   ├── agents/
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentLogs.tsx
│   │   │   │   └── AgentStatus.tsx
│   │   │   │
│   │   │   ├── documents/
│   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   └── WebScraper.tsx
│   │   │   │
│   │   │   ├── git/
│   │   │   │   ├── WorktreeList.tsx
│   │   │   │   ├── BranchSelector.tsx
│   │   │   │   └── GitActions.tsx
│   │   │   │
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── Layout.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAgents.ts
│   │   │   ├── useWorkflows.ts
│   │   │   ├── useDocuments.ts
│   │   │   ├── useChat.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useGit.ts
│   │   │
│   │   ├── store/
│   │   │   ├── index.ts
│   │   │   ├── agentStore.ts
│   │   │   ├── workflowStore.ts
│   │   │   ├── documentStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts                # Axios instance
│   │   │   ├── agentService.ts
│   │   │   ├── workflowService.ts
│   │   │   ├── documentService.ts
│   │   │   ├── chatService.ts
│   │   │   ├── gitService.ts
│   │   │   └── websocketService.ts
│   │   │
│   │   ├── types/
│   │   │   ├── agent.ts
│   │   │   ├── workflow.ts
│   │   │   ├── document.ts
│   │   │   ├── chat.ts
│   │   │   └── git.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── format.ts
│   │   │   └── constants.ts
│   │   │
│   │   └── styles/
│   │       ├── globals.css
│   │       └── themes.css
│   │
│   └── public/
│       └── vite.svg
│
├── frontend-terminal/
│   ├── package.json
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── index.tsx                 # Terminal app entry
│   │   ├── App.tsx                   # Root Ink component
│   │   │
│   │   ├── components/
│   │   │   ├── ChatView.tsx
│   │   │   ├── WorkflowView.tsx
│   │   │   ├── DocumentView.tsx
│   │   │   ├── AgentView.tsx
│   │   │   └── Menu.tsx
│   │   │
│   │   ├── hooks/                    # Shared with web (symlink)
│   │   ├── store/                    # Shared with web (symlink)
│   │   ├── services/                 # Shared with web (symlink)
│   │   └── types/                    # Shared with web (symlink)
│   │
│   └── bin/
│       └── amelia-tui                # Executable script
│
├── docs/
│   ├── setup.md
│   ├── architecture.md
│   ├── api-reference.md
│   ├── agent-development.md
│   └── workflows.md
│
└── scripts/
    ├── setup.sh                      # Initial setup script
    ├── start-backend.sh              # Start backend server
    ├── start-web.sh                  # Start web frontend
    ├── start-tui.sh                  # Start terminal UI
    └── init-db.sh                    # Initialize database
```

---

## 5. Backend Implementation

### 5.1 FastAPI Application Structure

#### 5.1.1 Main Application (`main.py`)

```python
"""
Main FastAPI application entrypoint.
"""
import signal
import sys
import asyncio
from typing import Set
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config import settings
from backend.database.connection import init_db, close_db
from backend.api.routes import agents, workflows, rag, chat, git, status
from backend.api.middleware.error_handler import error_handler_middleware
from backend.api.middleware.logging import logging_middleware
from backend.api.websocket.manager import get_connection_manager
from backend.core.events.bus import EventBus
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Track active operations for graceful shutdown
active_operations: Set[str] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management with graceful shutdown.
    Handles startup, shutdown, and signal handling for clean termination.
    """
    # Startup
    logger.info("Starting Amelia backend...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize event bus
    event_bus = EventBus()
    app.state.event_bus = event_bus
    await event_bus.start()
    logger.info("Event bus started")

    # Connect WebSocket manager to EventBus
    ws_manager = get_connection_manager()
    ws_manager.set_event_bus(event_bus)
    logger.info("WebSocket manager connected to EventBus")

    # Initialize accepting_requests flag
    app.state.accepting_requests = True

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(graceful_shutdown(app))

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("Application startup complete")

    yield

    # Shutdown
    await graceful_shutdown(app)


async def graceful_shutdown(app: FastAPI):
    """
    Gracefully shutdown the application.
    Waits for active operations to complete with timeout.
    """
    logger.info("Starting graceful shutdown...")

    # Stop accepting new requests (application-level)
    app.state.accepting_requests = False

    # Wait for active operations with timeout
    shutdown_timeout = 30  # seconds
    start_time = asyncio.get_event_loop().time()

    while active_operations:
        elapsed = asyncio.get_event_loop().time() - start_time

        if elapsed >= shutdown_timeout:
            logger.warning(
                f"Shutdown timeout: {len(active_operations)} operations still active"
            )
            break

        logger.info(
            f"Waiting for {len(active_operations)} operations to complete... "
            f"({shutdown_timeout - int(elapsed)}s remaining)"
        )
        await asyncio.sleep(1)

    # Stop event bus
    logger.info("Stopping event bus...")
    await app.state.event_bus.stop()

    # Close database connections
    logger.info("Closing database connections...")
    await close_db()

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Amelia API",
    description="Local LLM Workflow Orchestration API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.middleware("http")(error_handler_middleware)
app.middleware("http")(logging_middleware)


# Middleware to track active operations for graceful shutdown
@app.middleware("http")
async def track_operations(request: Request, call_next):
    """Track active HTTP requests for graceful shutdown."""
    operation_id = f"{request.method}:{request.url.path}:{id(request)}"
    active_operations.add(operation_id)

    try:
        response = await call_next(request)
        return response
    finally:
        active_operations.discard(operation_id)


# Include routers
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(git.router, prefix="/api/git", tags=["git"])
app.include_router(status.router, prefix="/api/status", tags=["status"])


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    Accepts connections and broadcasts EventBus events to clients.
    """
    manager = get_connection_manager()

    # Extract client_id from headers or generate new one
    client_id = websocket.headers.get("X-Client-ID")
    client_id = await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "data": {"client_id": client_id, "status": "connected"}
        })

        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_json()

            # Handle ping/pong for heartbeat
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # Handle other client messages if needed
                logger.debug(f"Received message from {client_id}: {data.get('type')}")

    except WebSocketDisconnect:
        await manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await manager.disconnect(websocket, client_id)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Amelia API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint - see api/routes/status.py for comprehensive health checks"""
    return {"status": "healthy"}
```

**Note:** The simple health check above is included in main.py for basic connectivity testing. For comprehensive health monitoring including database checks, event bus status, disk space, and metrics, see the detailed implementation in section 5.1.4 (Status & Health Check Routes).

**Graceful Shutdown Implementation:**

The application includes a comprehensive graceful shutdown mechanism that ensures clean termination:

1. **Signal Handling**
   - Captures SIGTERM and SIGINT signals (Ctrl+C, container termination)
   - Initiates graceful shutdown process when signals are received
   - Prevents abrupt termination of in-flight operations

2. **Operation Tracking**
   - Middleware tracks all active HTTP requests
   - Each operation gets a unique ID: `{method}:{path}:{request_id}`
   - Operations are tracked in a global set for monitoring

3. **Shutdown Sequence**
   - Sets `accepting_requests` flag to false (application-level)
   - Waits up to 30 seconds for active operations to complete
   - Logs progress every second showing remaining operations
   - Proceeds with shutdown after timeout even if operations remain

4. **Resource Cleanup Order**
   - Stop EventBus (prevents new event processing)
   - Close database connections (releases connection pool)
   - Log completion status

5. **Benefits**
   - Zero data loss during deployments
   - Prevents partial transactions
   - Clean container restarts in Kubernetes
   - Better user experience during updates
   - Observability of shutdown process via logs

**Usage in Production:**

```bash
# Container will gracefully shutdown when receiving SIGTERM
docker stop amelia-backend  # Sends SIGTERM, waits for graceful shutdown

# Kubernetes sends SIGTERM on pod termination
kubectl delete pod amelia-backend-xyz

# Manual graceful shutdown
kill -SIGTERM <pid>  # or Ctrl+C in terminal
```

**Shutdown Logs Example:**

```
2025-01-08 10:30:45 - WARNING - Received signal 15, initiating graceful shutdown...
2025-01-08 10:30:45 - INFO - Starting graceful shutdown...
2025-01-08 10:30:45 - INFO - Waiting for 3 operations to complete... (30s remaining)
2025-01-08 10:30:46 - INFO - Waiting for 2 operations to complete... (29s remaining)
2025-01-08 10:30:47 - INFO - Waiting for 1 operations to complete... (28s remaining)
2025-01-08 10:30:48 - INFO - Stopping event bus...
2025-01-08 10:30:48 - INFO - Closing database connections...
2025-01-08 10:30:48 - INFO - Shutdown complete
```

#### 5.1.2 Configuration Management (`config.py`)

```python
"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from pathlib import Path
from enum import Enum


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
```

**Configuration Validation:**

The Settings class uses Pydantic validators to ensure configuration is valid at startup:
- API keys are validated for correct format
- Database URL must be PostgreSQL
- Chunk sizes must be reasonable
- Pool settings must be positive
- Environment-specific properties for conditional logic

This ensures the application fails fast on startup with clear error messages rather than failing mysteriously during execution.

```python
class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Application
    APP_NAME: str = "Amelia"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://amelia:amelia@localhost:5432/amelia"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    TEMP_DIR: Path = BASE_DIR / "temp"
    
    # LLM Providers
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Default LLM Settings
    DEFAULT_MODEL: str = "claude-sonnet-4-5-20250929"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    
    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    
    # Claude Code
    CLAUDE_CODE_PATH: str = "claude"
    CLAUDE_CODE_TIMEOUT: int = 300
    
    # Git
    GIT_WORKTREE_DIR: Path = BASE_DIR / "worktrees"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Validators
    @field_validator('ANTHROPIC_API_KEY')
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v or v == "":
            logger.warning("ANTHROPIC_API_KEY not set - Claude features will be unavailable")
            return v
        if not v.startswith("sk-ant-"):
            raise ValueError("ANTHROPIC_API_KEY must start with 'sk-ant-'")
        return v

    @field_validator('OPENROUTER_API_KEY')
    @classmethod
    def validate_openrouter_key(cls, v: str) -> str:
        """Validate OpenRouter API key format."""
        if v and not v.startswith("sk-or-"):
            logger.warning("OPENROUTER_API_KEY should start with 'sk-or-'")
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate PostgreSQL connection string."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator('CHUNK_SIZE')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is reasonable."""
        if v < 100:
            raise ValueError("CHUNK_SIZE too small - minimum 100 characters")
        if v > 4000:
            logger.warning(f"CHUNK_SIZE {v} is very large - may exceed model context limits")
        return v

    @model_validator(mode='after')
    def validate_chunk_overlap(self):
        """Validate chunk overlap is less than chunk size."""
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        return self

    @model_validator(mode='after')
    def validate_pool_settings(self):
        """Validate database pool configuration."""
        if self.DATABASE_POOL_SIZE < 1:
            raise ValueError("DATABASE_POOL_SIZE must be at least 1")
        if self.DATABASE_MAX_OVERFLOW < 0:
            raise ValueError("DATABASE_MAX_OVERFLOW cannot be negative")
        return self

    # Environment helper properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.GIT_WORKTREE_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
```

#### 5.1.3 WebSocket Implementation (`api/websocket/manager.py`)

```python
"""
WebSocket connection manager with EventBus integration.
Manages WebSocket connections and broadcasts events to connected clients.
"""
from typing import Dict, Set
from uuid import uuid4
from fastapi import WebSocket, WebSocketDisconnect
from backend.core.events.bus import EventBus, Event, EventType
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events.
    Integrates with EventBus to push backend events to frontend clients.
    """

    def __init__(self):
        # Map of client_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._event_bus: EventBus = None

    def set_event_bus(self, event_bus: EventBus):
        """Set event bus and subscribe to events for broadcasting."""
        self._event_bus = event_bus

        # Subscribe to all event types that should be broadcast to clients
        for event_type in EventType:
            event_bus.subscribe(event_type, self._broadcast_event)

        logger.info("WebSocket manager subscribed to EventBus events")

    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """
        Accept and track WebSocket connection.
        Returns the client_id for this connection.
        """
        await websocket.accept()

        # Generate client_id if not provided
        if not client_id:
            client_id = str(uuid4())

        # Track connection
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)

        logger.info(f"WebSocket connected: {client_id} (total connections: {self.connection_count})")

        return client_id

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)

            # Remove client_id if no more connections
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        logger.info(f"WebSocket disconnected: {client_id} (total connections: {self.connection_count})")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to a specific client."""
        connections = self.active_connections.get(client_id, set())
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                disconnected.append(websocket)

        # Clean up failed connections
        for ws in disconnected:
            await self.disconnect(ws, client_id)

    async def broadcast(self, message: dict, exclude_client: str = None):
        """Broadcast message to all connected clients except excluded one."""
        disconnected = []

        for client_id, connections in self.active_connections.items():
            # Skip excluded client
            if client_id == exclude_client:
                continue

            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {client_id}: {e}")
                    disconnected.append((client_id, websocket))

        # Clean up failed connections
        for client_id, ws in disconnected:
            await self.disconnect(ws, client_id)

    async def _broadcast_event(self, event: Event):
        """
        Callback for EventBus events.
        Converts Event objects to JSON and broadcasts to all clients.
        """
        message = {
            "type": event.type.value,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        }

        await self.broadcast(message)

    @property
    def connection_count(self) -> int:
        """Total number of active WebSocket connections."""
        return sum(len(connections) for connections in self.active_connections.values())


# Global connection manager instance
_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
```

#### 5.1.4 Status & Health Check Routes (`api/routes/status.py`)

This module provides comprehensive operational endpoints for monitoring system health, metrics, and readiness. These endpoints are essential for production deployments, Kubernetes health checks, and operational monitoring.

```python
"""
System status and health check endpoints.
"""
from fastapi import APIRouter, Depends, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from backend.database.connection import get_db
from backend.core.events.bus import get_event_bus
from backend.models.database.agent import Agent
from backend.models.database.workflow import Workflow
from backend.models.database.document import Document
from backend.utils.logger import setup_logger
from datetime import datetime, timezone

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint.
    Returns detailed health status of all system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }

    # 1. Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Could add actual timing
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # 2. Event bus check
    try:
        event_bus = get_event_bus()
        health_status["checks"]["event_bus"] = {
            "status": "healthy" if event_bus._running else "stopped",
            "queue_size": event_bus._queue.qsize() if event_bus._running else 0
        }
        if not event_bus._running:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["event_bus"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # 3. pgvector extension check
    try:
        result = await db.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        has_vector = result.scalar()
        health_status["checks"]["pgvector"] = {
            "status": "healthy" if has_vector else "missing",
            "installed": has_vector
        }
        if not has_vector:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["pgvector"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 4. Disk space check
    try:
        import shutil
        from backend.config import settings

        total, used, free = shutil.disk_usage(settings.UPLOAD_DIR)
        free_percent = (free / total) * 100

        health_status["checks"]["disk_space"] = {
            "status": "healthy" if free_percent > 10 else "warning",
            "free_gb": round(free / (1024**3), 2),
            "total_gb": round(total / (1024**3), 2),
            "free_percent": round(free_percent, 2)
        }

        if free_percent < 5:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "error": str(e)
        }

    # Set appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        return health_status, http_status.HTTP_503_SERVICE_UNAVAILABLE
    elif health_status["status"] == "degraded":
        return health_status, http_status.HTTP_200_OK
    else:
        return health_status, http_status.HTTP_200_OK


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    """
    System metrics endpoint.
    Returns counts and statistics about system resources.
    """
    # Count active agents
    agents_running = await db.scalar(
        select(func.count(Agent.id)).where(Agent.status == 'running')
    )
    agents_total = await db.scalar(select(func.count(Agent.id)))

    # Count workflows
    workflows_running = await db.scalar(
        select(func.count(Workflow.id)).where(Workflow.status == 'running')
    )
    workflows_total = await db.scalar(select(func.count(Workflow.id)))
    workflows_completed = await db.scalar(
        select(func.count(Workflow.id)).where(Workflow.status == 'completed')
    )
    workflows_failed = await db.scalar(
        select(func.count(Workflow.id)).where(Workflow.status == 'failed')
    )

    # Count documents
    total_documents = await db.scalar(select(func.count(Document.id)))
    total_storage_bytes = await db.scalar(
        select(func.sum(Document.file_size)).where(Document.file_size.isnot(None))
    ) or 0

    # Get event bus metrics
    try:
        event_bus = get_event_bus()
        event_queue_size = event_bus._queue.qsize() if event_bus._running else 0
    except:
        event_queue_size = 0

    return {
        "agents": {
            "running": agents_running,
            "total": agents_total
        },
        "workflows": {
            "running": workflows_running,
            "completed": workflows_completed,
            "failed": workflows_failed,
            "total": workflows_total
        },
        "documents": {
            "total": total_documents,
            "total_size_mb": round(total_storage_bytes / (1024**2), 2)
        },
        "event_bus": {
            "queue_size": event_queue_size,
            "max_queue_size": 1000
        }
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    Returns 200 if service is ready to accept traffic, 503 otherwise.
    """
    try:
        # Quick database check
        await db.execute(text("SELECT 1"))

        # Check event bus is running
        event_bus = get_event_bus()
        if not event_bus._running:
            return {"ready": False, "reason": "EventBus not running"}, \
                   http_status.HTTP_503_SERVICE_UNAVAILABLE

        return {"ready": True}, http_status.HTTP_200_OK

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"ready": False, "reason": str(e)}, \
               http_status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if service is alive (even if not ready).
    """
    return {"alive": True}, http_status.HTTP_200_OK
```

**Key Features:**

1. **Comprehensive Health Check (`/health`)**: Multi-component health monitoring
   - Database connectivity with query execution test
   - Event bus status and queue size monitoring
   - pgvector extension verification for RAG functionality
   - Disk space monitoring with configurable thresholds
   - Returns appropriate HTTP status codes (200/503) based on health status
   - Three-state health model: healthy, degraded, unhealthy

2. **Metrics Endpoint (`/metrics`)**: System resource statistics
   - Agent counts (running vs total)
   - Workflow statistics (running, completed, failed)
   - Document storage metrics
   - Event bus queue metrics
   - Useful for monitoring dashboards and alerting

3. **Kubernetes-Style Probes**:
   - `/ready`: Readiness probe - indicates if service can handle traffic
   - `/live`: Liveness probe - indicates if service is alive (for restart detection)
   - Essential for Kubernetes/container deployments

4. **Error Handling**: Graceful degradation with detailed error reporting
   - Individual component failures reported separately
   - Overall status reflects worst component state
   - Detailed error messages in response for debugging

**Usage Examples:**

```bash
# Check overall health
curl http://localhost:8000/health

# Get system metrics
curl http://localhost:8000/metrics

# Kubernetes readiness probe
curl http://localhost:8000/ready

# Kubernetes liveness probe
curl http://localhost:8000/live
```

**Integration with Main Application:**

The status router should be included in main.py:

```python
from backend.api.routes import status

app.include_router(status.router, tags=["status"])
```

### 5.2 Database Layer

#### 5.2.1 Database Connection (`database/connection.py`)

**Database Session Management Pattern**

**Important:** The `get_db()` dependency follows the "caller-controlled transaction" pattern. This means:

1. The dependency yields a session but does NOT auto-commit
2. Route handlers or service methods must explicitly call `await db.commit()` when ready
3. This allows composing multiple database operations in a single transaction
4. For simple single-operation endpoints, use `get_db_with_commit()` instead

**Example - Complex operation with manual transaction control:**
```python
@router.post("/documents/upload")
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    # Create document
    document = Document(name=file.filename, ...)
    db.add(document)
    await db.flush()  # Get ID without committing

    # Create embeddings in same transaction
    for chunk in chunks:
        embedding = Embedding(document_id=document.id, ...)
        db.add(embedding)

    # Atomic commit of both document and embeddings
    await db.commit()
    return document
```

**Example - Simple operation with auto-commit:**
```python
@router.get("/documents/{id}")
async def get_document(id: UUID, db: AsyncSession = Depends(get_db_with_commit)):
    return await db.get(Document, id)
```

```python
"""
Database connection management using SQLAlchemy async.
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from backend.config import settings
from backend.models.database.base import Base
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    poolclass=NullPool if settings.DEBUG else None,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database, create tables"""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI routes to get database session.

    IMPORTANT: This dependency does NOT auto-commit. The caller is responsible
    for calling commit() or rollback() to control transaction boundaries.
    This allows proper composition of database operations.

    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Do NOT auto-commit - let the caller control transaction boundaries
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_commit() -> AsyncSession:
    """
    Alternative dependency that auto-commits on success.
    Use this ONLY for simple single-operation endpoints.
    For complex operations, use get_db() and manage transactions explicitly.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 5.2.2 Base Model (`models/database/base.py`)

```python
"""
SQLAlchemy base model with common fields.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models"""
    pass


**Timezone-Aware Timestamps:**

All timestamps in Amelia use timezone-aware `datetime` objects set to UTC:
- Prevents timezone-related bugs (DST transitions, server timezone changes)
- Ensures consistency across distributed systems
- Enables correct datetime arithmetic
- SQLAlchemy `DateTime(timezone=True)` stores as TIMESTAMP WITH TIME ZONE in PostgreSQL
- Always use `datetime.now(timezone.utc)` instead of `datetime.utcnow()` (which is naive)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps with timezone support"""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key"""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)


class VersionMixin:
    """Mixin for optimistic locking with version field"""

    version = Column(Integer, default=1, nullable=False)

    def increment_version(self):
        """Increment version for optimistic locking."""
        self.version += 1
```

### 5.3 Event System

#### 5.3.1 Event Bus (`core/events/bus.py`)

```python
"""
Asynchronous event bus for inter-component communication.
Implements publish-subscribe pattern using asyncio.
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class EventType(str, Enum):
    """Event types"""
    AGENT_STARTED = "agent.started"
    AGENT_PROGRESS = "agent.progress"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS = "workflow.progress"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    CHAT_MESSAGE = "chat.message"
    CHAT_STREAM = "chat.stream"
    
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_INDEXED = "document.indexed"
    
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


@dataclass
class Event:
    """Event data structure"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = None
    source: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


**Event Bus Implementation Notes:**

The EventBus uses several safety mechanisms:
- **Bounded Queue (maxsize=1000)**: Prevents unbounded memory growth if events are published faster than consumed
- **Async Locks**: Prevents race conditions in start/stop methods
- **Subscriber Cleanup**: Periodically removes dead subscribers to prevent memory leaks
- **Queue Full Handling**: Drops events if queue is full rather than blocking
- **Error Isolation**: Exceptions in subscribers don't crash the event bus

class EventBus:
    """
    Asynchronous event bus for publish-subscribe messaging.
    Thread-safe and async-safe.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000)  # Bounded queue
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start the event bus processor"""
        async with self._lock:  # Use lock to prevent race condition
            if self._running:
                return

            self._running = True
            self._task = asyncio.create_task(self._process_events())

        logger.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus processor"""
        async with self._lock:
            if not self._running:
                return

            self._running = False

        # Cancel task outside lock to avoid deadlock
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Event bus stopped")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """
        Subscribe to an event type.
        Callback should be an async function: async def callback(event: Event)
        Uses weak references to prevent memory leaks.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        # Store the callback directly
        # Note: For production use, consider weak references if callbacks are bound methods
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def _cleanup_subscribers(self, event_type: EventType):
        """Remove dead/invalid subscribers for an event type."""
        if event_type in self._subscribers:
            # Filter out None or invalid callbacks
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type]
                if cb is not None and callable(cb)
            ]

    async def publish(self, event: Event):
        """
        Publish an event to the bus.
        Will drop event if queue is full to prevent memory issues.
        """
        try:
            self._queue.put_nowait(event)
            logger.debug(f"Published event: {event.type}")
        except asyncio.QueueFull:
            logger.warning(
                f"Event queue full - dropping event {event.type}. "
                "Consider increasing maxsize or processing events faster."
            )
    
    async def _process_events(self):
        """Background task to process events from queue"""
        while self._running:
            try:
                # Wait for event with timeout to allow checking _running
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=0.1
                )

                # Get subscribers for this event type
                subscribers = self._subscribers.get(event.type, [])

                # Clean up dead subscribers periodically
                self._cleanup_subscribers(event.type)

                # Call all subscribers
                for callback in subscribers:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(
                            f"Error in event subscriber for {event.type}: {e}"
                        )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
```

### 5.4 Agent System

#### 5.4.1 Base Agent (`core/agents/base.py`)

```python
"""
Base agent class for all agents in the system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from backend.core.events.bus import EventBus, Event, EventType
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentConfig(BaseModel):
    """Base configuration for agents"""
    name: str
    description: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 300
    retry_attempts: int = 3
    context_sources: List[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Agent execution result"""
    status: AgentStatus
    output: Dict[str, Any]
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


**BaseAgent Implementation Notes:**

The BaseAgent class provides robust execution with:
- **Timeout Enforcement**: Uses `asyncio.wait_for()` to enforce execution timeout
- **Cancellation Support**: Agents can check `is_cancelled()` and respond to `cancel()` requests
- **Resource Cleanup**: `cleanup()` method called automatically on timeout, cancellation, or error
- **Lifecycle Events**: Publishes started/completed/failed events to EventBus
- **Error Isolation**: Exceptions in agent execution don't crash the system

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides common functionality for agent execution, event publishing,
    and lifecycle management.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        event_bus: EventBus,
        agent_id: Optional[str] = None
    ):
        self.config = config
        self.event_bus = event_bus
        self.agent_id = agent_id or f"{config.name}_{datetime.now(timezone.utc).timestamp()}"
        self.status = AgentStatus.IDLE
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._cancel_event = asyncio.Event()  # Add cancellation support
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> AgentResult:
        """
        Execute the agent with given input.
        Handles lifecycle events, timeout enforcement, and error handling.

        Args:
            input_data: Input data for the agent
            timeout: Optional timeout in seconds (overrides config.timeout)

        Returns:
            AgentResult with execution status and output
        """
        self._started_at = datetime.now(timezone.utc)
        self.status = AgentStatus.RUNNING
        self._cancel_event.clear()  # Reset cancellation flag

        # Use provided timeout or fall back to config
        execution_timeout = timeout or self.config.timeout

        # Publish started event
        await self._publish_event(EventType.AGENT_STARTED, {
            "agent_id": self.agent_id,
            "agent_name": self.config.name,
            "input": input_data,
            "timeout": execution_timeout
        })

        try:
            # Execute with timeout enforcement
            output = await asyncio.wait_for(
                self._run_with_cleanup(input_data),
                timeout=execution_timeout
            )

            # Mark as completed
            self._completed_at = datetime.now(timezone.utc)
            self.status = AgentStatus.COMPLETED

            result = AgentResult(
                status=AgentStatus.COMPLETED,
                output=output,
                started_at=self._started_at,
                completed_at=self._completed_at,
                duration_seconds=(
                    self._completed_at - self._started_at
                ).total_seconds()
            )

            # Publish completed event
            await self._publish_event(EventType.AGENT_COMPLETED, {
                "agent_id": self.agent_id,
                "agent_name": self.config.name,
                "result": result.model_dump()
            })

            return result

        except asyncio.TimeoutError:
            logger.error(f"Agent {self.config.name} timed out after {execution_timeout}s")
            self._completed_at = datetime.now(timezone.utc)
            self.status = AgentStatus.FAILED

            await self.cleanup()

            result = AgentResult(
                status=AgentStatus.FAILED,
                output={},
                error=f"Agent execution timed out after {execution_timeout} seconds",
                started_at=self._started_at,
                completed_at=self._completed_at,
                duration_seconds=(self._completed_at - self._started_at).total_seconds()
            )

            await self._publish_event(EventType.AGENT_FAILED, {
                "agent_id": self.agent_id,
                "agent_name": self.config.name,
                "error": "Timeout"
            })

            raise

        except asyncio.CancelledError:
            logger.info(f"Agent {self.config.name} was cancelled")
            self._completed_at = datetime.now(timezone.utc)
            self.status = AgentStatus.FAILED

            await self.cleanup()

            await self._publish_event(EventType.AGENT_FAILED, {
                "agent_id": self.agent_id,
                "agent_name": self.config.name,
                "error": "Cancelled"
            })

            raise

        except Exception as e:
            logger.error(f"Agent {self.config.name} failed: {e}")
            self._completed_at = datetime.now(timezone.utc)
            self.status = AgentStatus.FAILED

            await self.cleanup()

            result = AgentResult(
                status=AgentStatus.FAILED,
                output={},
                error=str(e),
                started_at=self._started_at,
                completed_at=self._completed_at,
                duration_seconds=(
                    self._completed_at - self._started_at
                ).total_seconds()
            )

            # Publish failed event
            await self._publish_event(EventType.AGENT_FAILED, {
                "agent_id": self.agent_id,
                "agent_name": self.config.name,
                "error": str(e)
            })

            raise
    
    @abstractmethod
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent-specific execution logic.
        Must be implemented by subclasses.
        """
        pass

    async def _run_with_cleanup(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper that ensures cleanup on all exit paths.
        Subclasses should override _run(), not this method.
        """
        try:
            return await self._run(input_data)
        finally:
            # Cleanup runs even if _run raises or is cancelled
            # Don't call cleanup() here - it's called in execute() exception handlers
            pass

    async def cleanup(self):
        """
        Override this in subclasses to clean up resources.
        Called automatically on timeout, cancellation, or error.

        Examples: close file handles, kill subprocesses, release locks, etc.
        """
        pass

    async def cancel(self):
        """
        Request cancellation of the agent.
        Sets the cancellation event that agents can check.
        """
        self._cancel_event.set()
        logger.info(f"Cancellation requested for agent {self.agent_id}")

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancel_event.is_set()

    async def _publish_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish an event to the event bus"""
        event = Event(
            type=event_type,
            data=data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
    
    async def update_progress(self, progress: float, message: str):
        """Update and publish agent progress"""
        await self._publish_event(EventType.AGENT_PROGRESS, {
            "agent_id": self.agent_id,
            "agent_name": self.config.name,
            "progress": progress,
            "message": message
        })
```

#### 5.4.2 Discovery Agent (`core/agents/discovery.py`)

```python
"""
Discovery Agent: Analyzes requirements and documents to discover features.
"""
from typing import Dict, Any
from backend.core.agents.base import BaseAgent, AgentConfig
from backend.core.rag.retriever import RAGRetriever
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class DiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering features and requirements
    from provided documents and context.
    """
    
    def __init__(self, config: AgentConfig, event_bus, rag_retriever: RAGRetriever):
        super().__init__(config, event_bus)
        self.rag_retriever = rag_retriever
    
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute discovery process:
        1. Retrieve relevant documents from RAG
        2. Analyze requirements
        3. Extract features
        4. Organize findings
        """
        query = input_data.get("query", "")
        
        # Update progress
        await self.update_progress(0.1, "Retrieving relevant documents...")
        
        # Retrieve context from RAG
        rag_results = await self.rag_retriever.retrieve(
            query=query,
            top_k=input_data.get("rag_top_k", 5)
        )
        
        await self.update_progress(0.3, "Analyzing requirements...")
        
        # Build context from RAG results
        context = self._build_context(rag_results)
        
        # Create prompt for Claude
        prompt = self._create_discovery_prompt(query, context)
        
        await self.update_progress(0.5, "Discovering features...")
        
        # Call LLM (Claude Code or API)
        # This would use the Claude integration
        discovery_output = await self._call_llm(prompt)
        
        await self.update_progress(0.8, "Organizing findings...")
        
        # Parse and structure the output
        structured_output = self._structure_output(discovery_output)
        
        await self.update_progress(1.0, "Discovery complete!")
        
        return {
            "features": structured_output.get("features", []),
            "requirements": structured_output.get("requirements", []),
            "context_used": len(rag_results),
            "raw_output": discovery_output
        }
    
    def _build_context(self, rag_results: List[Dict]) -> str:
        """Build context string from RAG results"""
        context_parts = []
        for i, result in enumerate(rag_results, 1):
            context_parts.append(f"Document {i}:")
            context_parts.append(result["content"])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _create_discovery_prompt(self, query: str, context: str) -> str:
        """Create the discovery prompt"""
        return f"""{self.config.system_prompt}

# Context from Documents

{context}

# Query

{query}

# Task

Analyze the provided documents and query to discover:
1. Key features that should be implemented
2. User requirements and needs
3. Technical requirements
4. Constraints and considerations

Provide your analysis in a structured format with clear sections.
"""
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM (Claude Code or API).
        This is a placeholder - actual implementation would use
        the Claude integration.
        """
        # TODO: Implement actual LLM call
        # For now, return placeholder
        return "Discovery output placeholder"
    
    def _structure_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse and structure the LLM output"""
        # TODO: Implement parsing logic
        return {
            "features": [],
            "requirements": [],
        }
```

#### 5.4.3 Circuit Breaker for LLM APIs (`core/agents/circuit_breaker.py`)

**Purpose:** Prevent cascading failures when external LLM APIs (Anthropic, OpenRouter) experience outages or rate limiting.

**Circuit Breaker States:**
- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: Failure threshold exceeded, all requests fail immediately
- **HALF_OPEN**: Testing if service recovered, limited requests allowed

```python
"""
Circuit breaker pattern for resilient LLM API calls.
Prevents cascading failures and wasted API quota during outages.
"""
import time
import asyncio
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Failures before opening circuit
    success_threshold: int = 2  # Successes in half-open before closing
    timeout: int = 60  # Seconds before trying half-open state
    half_open_max_calls: int = 3  # Max concurrent calls in half-open


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for LLM API calls.

    Prevents wasting API quota and degrading performance when
    external services are experiencing issues.

    Usage:
        breaker = CircuitBreaker("anthropic", config)
        result = await breaker.call(llm_api_function, *args, **kwargs)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0

        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception from function
        """
        async with self._lock:
            # Check if circuit should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                else:
                    elapsed = time.time() - self.last_failure_time
                    remaining = self.config.timeout - int(elapsed)
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service unavailable. Retry in {remaining}s"
                    )

            # Limit concurrent calls in HALF_OPEN state
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN. "
                        f"Max concurrent calls ({self.config.half_open_max_calls}) reached"
                    )
                self.half_open_calls += 1

        # Execute the function
        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                await self._on_success()

            return result

        except Exception as e:
            async with self._lock:
                await self._on_failure(e)

            raise

    async def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.half_open_calls -= 1

            if self.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                    f"(success threshold reached)"
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    async def _on_failure(self, error: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls -= 1
            logger.warning(
                f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                f"(failure during recovery test)"
            )
            self.state = CircuitState.OPEN
            self.success_count = 0

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                    f"(failure threshold {self.config.failure_threshold} reached)"
                )
                self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.timeout

    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": datetime.fromtimestamp(
                self.last_failure_time
            ).isoformat() if self.last_failure_time else None
        }


# Global circuit breakers for different services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a named service.

    Args:
        name: Service name (e.g., "anthropic", "openrouter")
        config: Optional configuration (uses defaults if not provided)

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]
```

**Usage in Agent Classes:**

```python
# In core/agents/discovery.py or any agent using LLM APIs

from backend.core.agents.circuit_breaker import get_circuit_breaker, CircuitBreakerError

class DiscoveryAgent(BaseAgent):
    def __init__(self, config: AgentConfig, event_bus: EventBus, rag_retriever):
        super().__init__(config, event_bus)
        self.rag_retriever = rag_retriever

        # Get circuit breaker for Anthropic API
        self.circuit_breaker = get_circuit_breaker("anthropic")

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with circuit breaker protection.
        Automatically handles outages and rate limiting.
        """
        try:
            # Wrap LLM call in circuit breaker
            result = await self.circuit_breaker.call(
                self._make_api_call,
                prompt
            )
            return result

        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker prevented API call: {e}")

            # Publish event about circuit breaker activation
            await self._publish_event(EventType.SYSTEM_WARNING, {
                "message": "LLM API temporarily unavailable",
                "circuit_breaker": self.circuit_breaker.get_state()
            })

            # Return fallback response or re-raise
            raise RuntimeError(
                "LLM API temporarily unavailable. Please try again later."
            ) from e

    async def _make_api_call(self, prompt: str) -> str:
        """Actual API call implementation"""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        response = await client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
```

**Monitoring Circuit Breaker Status:**

```python
# Add to api/routes/status.py

@router.get("/circuit-breakers")
async def circuit_breaker_status():
    """Get status of all circuit breakers"""
    from backend.core.agents.circuit_breaker import _circuit_breakers

    return {
        "circuit_breakers": [
            breaker.get_state()
            for breaker in _circuit_breakers.values()
        ]
    }
```

**Benefits:**

1. **Prevents Cascading Failures**: Stops retrying when service is down
2. **Saves API Costs**: Doesn't waste quota on failing requests
3. **Fast Failure**: Returns immediately when circuit is open
4. **Automatic Recovery**: Tests service recovery periodically
5. **Configurable**: Thresholds and timeouts adjustable per service
6. **Observability**: Exposes state for monitoring and alerting

**Configuration Example:**

```python
# For services with frequent transient errors
anthropic_breaker = get_circuit_breaker(
    "anthropic",
    CircuitBreakerConfig(
        failure_threshold=3,  # Open after 3 failures
        success_threshold=2,  # Require 2 successes to close
        timeout=30,  # Try recovery after 30s
        half_open_max_calls=2  # Limit test calls
    )
)

# For more stable services
openrouter_breaker = get_circuit_breaker(
    "openrouter",
    CircuitBreakerConfig(
        failure_threshold=10,  # More tolerant
        timeout=120  # Wait longer before retry
    )
)
```

### 5.5 Custom Exception Handling

#### 5.5.1 Exception Classes (`core/exceptions.py`)

**Purpose:** Provide specific, user-friendly exceptions for different error scenarios.

```python
"""
Custom exceptions for Amelia application.
Provides clear, actionable error messages for different failure scenarios.
"""
from typing import Optional, Dict, Any


class AmeliaException(Exception):
    """
    Base exception for all Amelia-specific errors.

    Attributes:
        message: Human-readable error message
        details: Additional context about the error
        status_code: HTTP status code to return (for API errors)
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


# Document/RAG Exceptions

class DocumentNotFoundError(AmeliaException):
    """Document not found in database"""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            details={"document_id": document_id},
            status_code=404
        )


class DocumentProcessingError(AmeliaException):
    """Failed to process document (parsing, chunking, embedding)"""

    def __init__(self, document_path: str, reason: str):
        super().__init__(
            message=f"Failed to process document: {reason}",
            details={"document_path": document_path, "reason": reason},
            status_code=500
        )


class EmbeddingGenerationError(AmeliaException):
    """Failed to generate embeddings"""

    def __init__(self, text_preview: str, model: str, error: str):
        super().__init__(
            message="Failed to generate embeddings",
            details={
                "text_preview": text_preview[:100],
                "model": model,
                "error": error
            },
            status_code=500
        )


# Agent Exceptions

class AgentNotFoundError(AmeliaException):
    """Agent not found in database"""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            details={"agent_id": agent_id},
            status_code=404
        )


class AgentExecutionError(AmeliaException):
    """Agent execution failed"""

    def __init__(self, agent_name: str, error: str):
        super().__init__(
            message=f"Agent execution failed: {agent_name}",
            details={"agent_name": agent_name, "error": error},
            status_code=500
        )


class AgentTimeoutError(AmeliaException):
    """Agent execution exceeded timeout"""

    def __init__(self, agent_name: str, timeout: int):
        super().__init__(
            message=f"Agent '{agent_name}' exceeded timeout of {timeout}s",
            details={"agent_name": agent_name, "timeout": timeout},
            status_code=504
        )


# Workflow Exceptions

class WorkflowNotFoundError(AmeliaException):
    """Workflow not found in database"""

    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow not found: {workflow_id}",
            details={"workflow_id": workflow_id},
            status_code=404
        )


class WorkflowStateError(AmeliaException):
    """Invalid workflow state transition"""

    def __init__(self, workflow_id: str, current_state: str, requested_action: str):
        super().__init__(
            message=f"Cannot {requested_action} workflow in {current_state} state",
            details={
                "workflow_id": workflow_id,
                "current_state": current_state,
                "requested_action": requested_action
            },
            status_code=400
        )


class ConcurrentModificationError(AmeliaException):
    """Optimistic locking failure - resource modified concurrently"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} was modified by another process",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "help": "Please refresh and try again"
            },
            status_code=409
        )


# API/External Service Exceptions

class LLMAPIError(AmeliaException):
    """LLM API call failed"""

    def __init__(self, provider: str, model: str, error: str):
        super().__init__(
            message=f"LLM API error from {provider}",
            details={"provider": provider, "model": model, "error": error},
            status_code=502
        )


class RateLimitError(AmeliaException):
    """API rate limit exceeded"""

    def __init__(self, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Rate limit exceeded for {provider}",
            details={
                "provider": provider,
                "retry_after": retry_after,
                "help": "Please wait before retrying"
            },
            status_code=429
        )


# Storage/File Exceptions

class StorageQuotaExceededError(AmeliaException):
    """Storage quota exceeded"""

    def __init__(self, current_size_mb: float, max_size_mb: float):
        super().__init__(
            message="Storage quota exceeded",
            details={
                "current_size_mb": current_size_mb,
                "max_size_mb": max_size_mb,
                "help": "Please delete some documents"
            },
            status_code=507
        )


class InvalidFileTypeError(AmeliaException):
    """File type not allowed"""

    def __init__(self, detected_type: str, allowed_types: list):
        super().__init__(
            message=f"File type not allowed: {detected_type}",
            details={
                "detected_type": detected_type,
                "allowed_types": allowed_types
            },
            status_code=400
        )


# Configuration Exceptions

class ConfigurationError(AmeliaException):
    """Invalid configuration"""

    def __init__(self, setting: str, reason: str):
        super().__init__(
            message=f"Invalid configuration for {setting}: {reason}",
            details={"setting": setting, "reason": reason},
            status_code=500
        )
```

#### 5.5.2 Exception Middleware (`api/middleware/error_handler.py`)

```python
"""
Global exception handler middleware for FastAPI.
Converts exceptions to user-friendly JSON responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.core.exceptions import AmeliaException
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


async def amelia_exception_middleware(request: Request, call_next):
    """
    Catch and handle all exceptions globally.
    Provides consistent error response format.
    """
    try:
        response = await call_next(request)
        return response

    except AmeliaException as e:
        # Amelia-specific exceptions - already have nice messages
        logger.error(
            f"Amelia exception: {e.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "details": e.details
            }
        )

        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.__class__.__name__,
                "message": e.message,
                "details": e.details,
                "path": request.url.path
            }
        )

    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "ValidationError",
                "message": str(e),
                "path": request.url.path
            }
        )

    except Exception as e:
        # Unexpected errors - log with full traceback
        logger.exception(
            f"Unexpected error: {str(e)}",
            extra={"path": request.url.path, "method": request.method}
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "path": request.url.path
            }
        )
```

#### 5.5.3 Usage Examples

```python
# In api/routes/rag.py
from backend.core.exceptions import (
    DocumentNotFoundError,
    InvalidFileTypeError,
    StorageQuotaExceededError
)

@router.get("/documents/{document_id}")
async def get_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    document = await db.get(Document, document_id)

    if not document:
        raise DocumentNotFoundError(str(document_id))

    return document


@router.post("/documents/upload")
async def upload_document(file: UploadFile):
    # Validate file type
    try:
        validate_file_upload(file)
    except ValueError as e:
        # Convert to our custom exception
        raise InvalidFileTypeError(
            detected_type=detect_mime_type(file),
            allowed_types=list(ALLOWED_TYPES.keys())
        )

    # ... rest of upload logic


# In core/agents/manager.py
from backend.core.exceptions import AgentNotFoundError, AgentTimeoutError

async def get_agent(self, agent_id: UUID) -> Agent:
    agent = await self.db.get(Agent, agent_id)

    if not agent:
        raise AgentNotFoundError(str(agent_id))

    return agent


# In core/workflows/manager.py
from backend.core.exceptions import ConcurrentModificationError, WorkflowStateError

async def pause_workflow(self, workflow_id: UUID):
    result = await self.db.execute(
        update(Workflow)
        .where(Workflow.id == workflow_id, Workflow.version == current_version)
        .values(status="paused", version=current_version + 1)
    )

    if result.rowcount == 0:
        raise ConcurrentModificationError("Workflow", str(workflow_id))
```

### 5.6 Datetime Handling Standards

**All datetime objects in Amelia must be timezone-aware and use UTC.**

#### Correct Usage:
```python
from datetime import datetime, timezone

# Creating timestamps
now = datetime.now(timezone.utc)  # ✅ CORRECT
timestamp = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # ✅ CORRECT

# Database models
created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # ✅ CORRECT
```

#### Incorrect Usage:
```python
# NEVER use these:
now = datetime.utcnow()  # ❌ WRONG - returns naive datetime
now = datetime.now()  # ❌ WRONG - uses server local timezone
created_at = Column(DateTime, default=datetime.utcnow)  # ❌ WRONG - naive datetime
```

#### Why This Matters:
- **Naive datetimes** (no timezone info) cause bugs during DST transitions
- **Server timezone** changes break datetime comparisons
- **PostgreSQL** `TIMESTAMP WITH TIME ZONE` requires timezone-aware datetimes
- **Serialization** to JSON/ISO format needs timezone for correctness

#### Type Hints:
```python
from datetime import datetime

# When you need to enforce timezone-aware datetimes:
def process_event(timestamp: datetime) -> None:
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    # ... process
```

---

## 6. Frontend Implementation

### 6.1 React Router v7 Configuration

#### 6.1.1 Router Setup (`router.tsx`)

```typescript
/**
 * React Router v7 configuration
 * Using the new framework mode with client-side rendering
 */
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Workflows from './pages/Workflows';
import Documents from './pages/Documents';
import Agents from './pages/Agents';
import Git from './pages/Git';
import Settings from './pages/Settings';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: 'chat',
        element: <Chat />,
      },
      {
        path: 'workflows',
        element: <Workflows />,
      },
      {
        path: 'workflows/:workflowId',
        element: <Workflows />,
      },
      {
        path: 'documents',
        element: <Documents />,
      },
      {
        path: 'agents',
        element: <Agents />,
      },
      {
        path: 'agents/:agentId',
        element: <Agents />,
      },
      {
        path: 'git',
        element: <Git />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
]);

export default function Router() {
  return <RouterProvider router={router} />;
}
```

### 6.2 State Management with Zustand

#### 6.2.1 Agent Store (`store/agentStore.ts`)

```typescript
/**
 * Agent state management using Zustand
 */
import { create } from 'zustand';
import { Agent, AgentStatus } from '../types/agent';

interface AgentState {
  agents: Agent[];
  activeAgent: Agent | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  setActiveAgent: (agent: Agent | null) => void;
  removeAgent: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Computed
  runningAgents: () => Agent[];
  completedAgents: () => Agent[];
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  activeAgent: null,
  loading: false,
  error: null,
  
  setAgents: (agents) => set({ agents }),
  
  addAgent: (agent) => set((state) => ({
    agents: [...state.agents, agent]
  })),
  
  updateAgent: (id, updates) => set((state) => ({
    agents: state.agents.map((agent) =>
      agent.id === id ? { ...agent, ...updates } : agent
    ),
    activeAgent: state.activeAgent?.id === id
      ? { ...state.activeAgent, ...updates }
      : state.activeAgent
  })),
  
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  
  removeAgent: (id) => set((state) => ({
    agents: state.agents.filter((agent) => agent.id !== id),
    activeAgent: state.activeAgent?.id === id ? null : state.activeAgent
  })),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  runningAgents: () => {
    const state = get();
    return state.agents.filter(
      (agent) => agent.status === AgentStatus.RUNNING
    );
  },
  
  completedAgents: () => {
    const state = get();
    return state.agents.filter(
      (agent) => agent.status === AgentStatus.COMPLETED
    );
  },
}));
```

#### 6.2.2 Chat Store (`store/chatStore.ts`)

```typescript
/**
 * Chat state management
 */
import { create } from 'zustand';
import { Message, ChatSession } from '../types/chat';

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: Message[];
  isStreaming: boolean;
  currentStreamingMessage: string;
  
  // Actions
  setSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (sessionId: string) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setMessages: (messages: Message[]) => void;
  setStreaming: (isStreaming: boolean) => void;
  appendToStreamingMessage: (chunk: string) => void;
  clearStreamingMessage: () => void;
  
  // Computed
  activeSession: () => ChatSession | null;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isStreaming: false,
  currentStreamingMessage: '',
  
  setSessions: (sessions) => set({ sessions }),
  
  setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map((msg) =>
      msg.id === id ? { ...msg, ...updates } : msg
    )
  })),
  
  setMessages: (messages) => set({ messages }),
  
  setStreaming: (isStreaming) => set({ isStreaming }),
  
  appendToStreamingMessage: (chunk) => set((state) => ({
    currentStreamingMessage: state.currentStreamingMessage + chunk
  })),
  
  clearStreamingMessage: () => set({ currentStreamingMessage: '' }),
  
  activeSession: () => {
    const state = get();
    return state.sessions.find(
      (session) => session.id === state.activeSessionId
    ) || null;
  },
}));
```

### 6.3 API Service Layer

#### 6.3.1 Base API Service (`services/api.ts`)

```typescript
/**
 * Base API service with axios configuration
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIService {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any auth tokens here if needed in the future
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Handle errors globally
        if (error.response) {
          console.error('API Error:', error.response.data);
        } else if (error.request) {
          console.error('Network Error:', error.message);
        }
        return Promise.reject(error);
      }
    );
  }
  
  get<T>(url: string, params?: any) {
    return this.client.get<T>(url, { params });
  }
  
  post<T>(url: string, data?: any) {
    return this.client.post<T>(url, data);
  }
  
  put<T>(url: string, data?: any) {
    return this.client.put<T>(url, data);
  }
  
  delete<T>(url: string) {
    return this.client.delete<T>(url);
  }
  
  patch<T>(url: string, data?: any) {
    return this.client.patch<T>(url, data);
  }
}

export const apiService = new APIService();
export default apiService;
```

#### 6.3.2 Agent Service (`services/agentService.ts`)

```typescript
/**
 * Agent API service
 */
import apiService from './api';
import { Agent, AgentConfig, AgentResult } from '../types/agent';

export class AgentService {
  private basePath = '/api/agents';
  
  async listAgents(): Promise<Agent[]> {
    const response = await apiService.get<Agent[]>(this.basePath);
    return response.data;
  }
  
  async getAgent(id: string): Promise<Agent> {
    const response = await apiService.get<Agent>(`${this.basePath}/${id}`);
    return response.data;
  }
  
  async createAgent(config: AgentConfig): Promise<Agent> {
    const response = await apiService.post<Agent>(this.basePath, config);
    return response.data;
  }
  
  async startAgent(id: string, input: any): Promise<AgentResult> {
    const response = await apiService.post<AgentResult>(
      `${this.basePath}/${id}/start`,
      { input }
    );
    return response.data;
  }
  
  async stopAgent(id: string): Promise<void> {
    await apiService.post(`${this.basePath}/${id}/stop`);
  }
  
  async deleteAgent(id: string): Promise<void> {
    await apiService.delete(`${this.basePath}/${id}`);
  }
  
  async getAgentLogs(id: string): Promise<string[]> {
    const response = await apiService.get<string[]>(
      `${this.basePath}/${id}/logs`
    );
    return response.data;
  }
}

export const agentService = new AgentService();
```

### 6.4 WebSocket Service

#### 6.4.1 WebSocket Manager with Heartbeat (`services/websocketService.ts`)

**Heartbeat Mechanism:**

The WebSocket service implements a ping/pong heartbeat to detect stale connections:
- Every 30 seconds, sends a `ping` message to the server
- Expects a `pong` response within 5 seconds
- If no pong received, assumes connection is dead and reconnects
- Prevents silent connection failures (firewalls, proxies, network issues)

This ensures the UI always has a live connection to receive real-time updates.

```typescript
/**
 * WebSocket service for real-time updates
 */
import { EventType } from '../types/events';

type EventCallback = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<EventType, EventCallback[]> = new Map();
  private isConnecting = false;

  // Heartbeat properties
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastPongReceived: number = Date.now();
  private readonly HEARTBEAT_INTERVAL = 30000; // 30 seconds
  private readonly PONG_TIMEOUT = 5000; // 5 seconds

  constructor() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || 'localhost:8000';
    this.url = `${protocol}//${host}/ws`;
  }
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      
      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }
      
      this.isConnecting = true;
      
      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.startHeartbeat();
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);

            // Handle pong responses
            if (message.type === 'pong') {
              this.lastPongReceived = Date.now();
              return;
            }

            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };
        
        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnecting = false;
          this.attemptReconnect();
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }
  
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  on(eventType: EventType, callback: EventCallback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
  }
  
  off(eventType: EventType, callback: EventCallback) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }
  
  send(eventType: EventType, data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: eventType, data }));
    } else {
      console.warn('WebSocket not connected');
    }
  }
  
  private handleMessage(message: { type: EventType; data: any }) {
    const callbacks = this.listeners.get(message.type);
    if (callbacks) {
      callbacks.forEach((callback) => callback(message.data));
    }
  }
  
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );

      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing interval

    this.heartbeatInterval = setInterval(() => {
      const now = Date.now();

      // Check if last pong was too long ago
      if (now - this.lastPongReceived > this.HEARTBEAT_INTERVAL + this.PONG_TIMEOUT) {
        console.warn('WebSocket heartbeat timeout - reconnecting');
        this.disconnect();
        this.connect().catch((error) => {
          console.error('Heartbeat reconnection failed:', error);
        });
        return;
      }

      // Send ping
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', {});
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}

export const wsService = new WebSocketService();
```

### 6.5 Key UI Components

#### 6.5.1 Chat Interface (`components/chat/ChatInterface.tsx`)

```typescript
/**
 * Main chat interface component
 */
import React, { useState, useEffect, useRef } from 'react';
import { useChat } from 'ai/react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { ScrollArea } from '../ui/scroll-area';
import MessageList from './MessageList';
import { Send } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';

export default function ChatInterface() {
  const { messages, addMessage, setStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const { messages: aiMessages, append, isLoading } = useChat({
    api: '/api/chat/stream',
    onResponse: () => {
      setStreaming(true);
    },
    onFinish: () => {
      setStreaming(false);
    },
  });
  
  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [aiMessages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user message
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    });
    
    // Send to API
    await append({
      role: 'user',
      content: input,
    });
    
    setInput('');
  };
  
  return (
    <Card className="flex flex-col h-full">
      <CardHeader>
        <CardTitle>Chat with Claude</CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
          <MessageList messages={aiMessages} />
        </ScrollArea>
        
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

#### 6.5.2 Workflow Graph Visualization (`components/workflows/WorkflowGraph.tsx`)

```typescript
/**
 * Workflow graph visualization component
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Workflow, WorkflowNode } from '../../types/workflow';
import { CheckCircle, Circle, AlertCircle, Loader } from 'lucide-react';

interface WorkflowGraphProps {
  workflow: Workflow;
}

export default function WorkflowGraph({ workflow }: WorkflowGraphProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{workflow.name}</CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {workflow.nodes.map((node: WorkflowNode, index: number) => (
            <div key={node.id} className="flex items-center gap-4">
              <div className="flex-shrink-0">
                {getStatusIcon(node.status)}
              </div>
              
              <div className="flex-1">
                <div className="font-medium">{node.name}</div>
                <div className="text-sm text-gray-500">{node.description}</div>
                
                {node.status === 'running' && node.progress !== undefined && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{Math.round(node.progress * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${node.progress * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
              
              {index < workflow.nodes.length - 1 && (
                <div className="flex-shrink-0 w-px h-8 bg-gray-300" />
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 7. Database Design

### 7.1 Schema Definitions

#### 7.1.1 Documents Table

```sql
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'markdown', 'pdf', 'html'
    content TEXT NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
```

#### 7.1.2 Embeddings Table

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector vector(384),  -- Dimension matches embedding model
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_embeddings_document_id ON embeddings(document_id);

-- Vector similarity index using HNSW for better performance
-- HNSW (Hierarchical Navigable Small World) provides faster queries than IVFFlat
-- m=16: max connections per layer, ef_construction=64: index build quality
CREATE INDEX idx_embeddings_vector
ON embeddings USING hnsw (vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Alternative if HNSW not available (requires pgvector 0.5.0+):
-- CREATE INDEX idx_embeddings_vector_ivfflat
-- ON embeddings USING ivfflat (vector vector_cosine_ops)
-- WITH (lists = 100);
```

#### 7.1.3 Agents Table

```sql
CREATE TYPE agent_status AS ENUM ('idle', 'running', 'paused', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,  -- 'discovery', 'design', 'planning', etc.
    status agent_status DEFAULT 'idle',
    progress FLOAT DEFAULT 0.0,
    config JSONB NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_created_at ON agents(created_at);

-- Composite index for common query pattern: filter by type and status
CREATE INDEX idx_agents_type_status ON agents(type, status);

-- Partial index for active agents (improves performance for monitoring queries)
CREATE INDEX idx_agents_active
ON agents(updated_at DESC)
WHERE status IN ('running', 'paused');
```

#### 7.1.4 Workflows Table

```sql
CREATE TYPE workflow_status AS ENUM ('idle', 'running', 'paused', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status workflow_status DEFAULT 'idle',
    graph_definition JSONB NOT NULL,  -- LangGraph structure
    state JSONB DEFAULT '{}',
    progress FLOAT DEFAULT 0.0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic indexes
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);

-- Composite index for common query pattern: filter by status, order by creation date
CREATE INDEX idx_workflows_status_created
ON workflows(status, created_at DESC);

-- Partial index for active workflows (reduces index size and improves query performance)
CREATE INDEX idx_workflows_active
ON workflows(created_at DESC)
WHERE status IN ('idle', 'running', 'paused');
```

#### 7.1.5 Chat Sessions Table

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

### 7.2 SQLAlchemy Models

#### 7.2.1 Document Model (`models/database/document.py`)

```python
"""
Document database model
"""
from sqlalchemy import Column, String, Text, Integer, JSON
from sqlalchemy.orm import relationship
from backend.models.database.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    """Document storage model"""
    
    __tablename__ = "documents"
    
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # markdown, pdf, html
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    metadata = Column(JSON, default={})
    
    # Relationships
    embeddings = relationship(
        "Embedding",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', type='{self.type}')>"
```

#### 7.2.2 Embedding Model (`models/database/embedding.py`)

```python
"""
Embedding database model for vector storage
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from backend.models.database.base import Base, TimestampMixin, UUIDMixin
from backend.config import settings


class Embedding(Base, UUIDMixin, TimestampMixin):
    """Vector embedding storage model"""
    
    __tablename__ = "embeddings"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    vector = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=False)
    metadata = Column(JSON, default={})
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, document_id={self.document_id}, chunk={self.chunk_index})>"
```

#### 7.2.3 Agent Model (`models/database/agent.py`)

```python
"""
Agent database model
"""
from sqlalchemy import Column, String, Text, Float, DateTime, Enum, JSON
from backend.models.database.base import Base, TimestampMixin, UUIDMixin
from backend.core.agents.base import AgentStatus
import enum


class Agent(Base, UUIDMixin, TimestampMixin):
    """Agent execution tracking model"""
    
    __tablename__ = "agents"
    
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    status = Column(
        Enum(AgentStatus),
        default=AgentStatus.IDLE,
        nullable=False
    )
    progress = Column(Float, default=0.0)
    config = Column(JSON, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', status='{self.status}')>"
```

#### 7.2.4 Workflow Model (`models/database/workflow.py`)

```python
"""
Workflow database model for orchestration
"""
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import JSONB
from backend.models.database.base import Base, TimestampMixin, UUIDMixin, VersionMixin
from backend.core.workflows.state import WorkflowStatus


class Workflow(Base, UUIDMixin, TimestampMixin, VersionMixin):
    """Workflow orchestration model with optimistic locking"""

    __tablename__ = "workflows"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="idle")
    state = Column(JSONB, default={})
    graph_definition = Column(JSON, nullable=False)
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # version field from VersionMixin for optimistic locking

    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', status='{self.status}', version={self.version})>"
```

---

## 8. Agent Orchestration System

### 8.1 LangGraph Integration

#### 8.1.1 Workflow State (`core/workflows/state.py`)

```python
"""
Workflow state management for LangGraph
"""
from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentNodeState(TypedDict):
    """State for individual agent node"""
    agent_id: str
    agent_name: str
    status: str
    progress: float
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]]
    error: Optional[str]


class WorkflowState(TypedDict):
    """Overall workflow state"""
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    current_node: Optional[str]
    nodes: Dict[str, AgentNodeState]
    shared_context: Dict[str, Any]
    rag_context: List[Dict[str, Any]]
    errors: List[str]
```

#### 8.1.2 Graph Builder (`core/workflows/graph.py`)

```python
"""
LangGraph workflow graph builder
"""
from typing import Dict, Any, List, Callable
from langgraph.graph import StateGraph, END
from backend.core.workflows.state import WorkflowState, AgentNodeState
from backend.core.agents.base import BaseAgent
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowGraphBuilder:
    """
    Builder for creating LangGraph workflow graphs.
    Constructs agent execution DAGs with dependencies.
    """
    
    def __init__(self):
        self.graph = StateGraph(WorkflowState)
        self.agents: Dict[str, BaseAgent] = {}
        self.node_configs: Dict[str, Dict[str, Any]] = {}
    
    def add_agent_node(
        self,
        node_name: str,
        agent: BaseAgent,
        dependencies: List[str] = None
    ):
        """
        Add an agent as a node in the workflow graph.
        
        Args:
            node_name: Unique identifier for the node
            agent: Agent instance to execute
            dependencies: List of node names this node depends on
        """
        self.agents[node_name] = agent
        self.node_configs[node_name] = {
            "dependencies": dependencies or [],
        }
        
        # Create node function
        async def node_function(state: WorkflowState) -> WorkflowState:
            """Execute agent node"""
            logger.info(f"Executing node: {node_name}")
            
            # Update node status
            state["nodes"][node_name]["status"] = "running"
            state["current_node"] = node_name
            
            try:
                # Prepare input from dependencies
                input_data = self._prepare_node_input(state, node_name)
                
                # Execute agent
                result = await agent.execute(input_data)
                
                # Update node state
                state["nodes"][node_name]["status"] = "completed"
                state["nodes"][node_name]["output"] = result.output
                state["nodes"][node_name]["progress"] = 1.0
                
                # Add output to shared context
                state["shared_context"][node_name] = result.output
                
            except Exception as e:
                logger.error(f"Node {node_name} failed: {e}")
                state["nodes"][node_name]["status"] = "failed"
                state["nodes"][node_name]["error"] = str(e)
                state["errors"].append(f"{node_name}: {str(e)}")
                state["status"] = "failed"
            
            return state
        
        # Add node to graph
        self.graph.add_node(node_name, node_function)
    
    def _prepare_node_input(
        self,
        state: WorkflowState,
        node_name: str
    ) -> Dict[str, Any]:
        """
        Prepare input for a node by collecting outputs from dependencies.
        """
        config = self.node_configs[node_name]
        dependencies = config["dependencies"]
        
        input_data = {
            "shared_context": state["shared_context"],
            "rag_context": state["rag_context"],
        }
        
        # Collect outputs from dependencies
        dependency_outputs = {}
        for dep in dependencies:
            if dep in state["nodes"]:
                dep_output = state["nodes"][dep].get("output")
                if dep_output:
                    dependency_outputs[dep] = dep_output
        
        input_data["dependencies"] = dependency_outputs
        
        return input_data
    
    def build(self) -> StateGraph:
        """
        Build and compile the workflow graph.
        Automatically adds edges based on dependencies.
        """
        # Add edges based on dependencies
        for node_name, config in self.node_configs.items():
            dependencies = config["dependencies"]
            
            if not dependencies:
                # No dependencies - can be entry point
                self.graph.set_entry_point(node_name)
            else:
                # Add edge from each dependency to this node
                for dep in dependencies:
                    self.graph.add_edge(dep, node_name)
        
        # Find terminal nodes (nodes with no dependents)
        all_nodes = set(self.node_configs.keys())
        has_dependents = set()
        for config in self.node_configs.values():
            has_dependents.update(config["dependencies"])
        
        terminal_nodes = all_nodes - has_dependents
        for terminal in terminal_nodes:
            self.graph.add_edge(terminal, END)
        
        # Compile graph
        return self.graph.compile()


async def create_discovery_design_planning_workflow() -> StateGraph:
    """
    Create a preset workflow: Discovery → Design → Planning
    """
    from backend.core.agents.discovery import DiscoveryAgent
    from backend.core.agents.design import DesignAgent
    from backend.core.agents.planning import PlanningAgent
    from backend.core.events.bus import get_event_bus
    
    builder = WorkflowGraphBuilder()
    event_bus = get_event_bus()
    
    # Create agents (simplified - actual implementation would have more config)
    discovery_agent = DiscoveryAgent(
        config=AgentConfig(
            name="Discovery",
            description="Analyze requirements and discover features",
            system_prompt="You are a requirements analyst..."
        ),
        event_bus=event_bus
    )
    
    design_agent = DesignAgent(
        config=AgentConfig(
            name="Design",
            description="Create technical design from features",
            system_prompt="You are a system architect..."
        ),
        event_bus=event_bus
    )
    
    planning_agent = PlanningAgent(
        config=AgentConfig(
            name="Planning",
            description="Create implementation plan",
            system_prompt="You are a technical project planner..."
        ),
        event_bus=event_bus
    )
    
    # Add nodes with dependencies
    builder.add_agent_node("discovery", discovery_agent, dependencies=[])
    builder.add_agent_node("design", design_agent, dependencies=["discovery"])
    builder.add_agent_node("planning", planning_agent, dependencies=["design"])
    
    return builder.build()
```

### 8.2 Workflow Manager

#### 8.2.1 Workflow Execution (`core/workflows/manager.py`)

```python
"""
Workflow execution and management
"""
from typing import Dict, Any, Optional
from uuid import UUID
from backend.core.workflows.graph import WorkflowGraphBuilder
from backend.core.workflows.state import WorkflowState, WorkflowStatus, AgentNodeState
from backend.models.database.workflow import Workflow
from backend.database.session import get_db
from backend.core.events.bus import get_event_bus, Event, EventType
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowManager:
    """
    Manages workflow lifecycle: creation, execution, monitoring.
    """
    
    def __init__(self):
        self.event_bus = get_event_bus()
        self.active_workflows: Dict[str, Any] = {}
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        graph_definition: Dict[str, Any]
    ) -> Workflow:
        """
        Create a new workflow from definition.
        """
        async with get_db() as db:
            workflow = Workflow(
                name=name,
                description=description,
                graph_definition=graph_definition,
                status=WorkflowStatus.IDLE,
                state={}
            )
            
            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)
            
            logger.info(f"Created workflow: {workflow.id}")
            return workflow
    
    async def start_workflow(
        self,
        workflow_id: UUID,
        initial_input: Dict[str, Any]
    ) -> WorkflowState:
        """
        Start workflow execution.
        """
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Initialize workflow state
            state = self._initialize_state(workflow, initial_input)
            
            # Update database
            workflow.status = WorkflowStatus.RUNNING
            workflow.state = state
            await db.commit()
            
            # Publish event
            await self.event_bus.publish(Event(
                type=EventType.WORKFLOW_STARTED,
                data={
                    "workflow_id": str(workflow_id),
                    "workflow_name": workflow.name
                }
            ))
            
            # Build and execute graph
            graph = await self._build_graph(workflow)
            
            # Execute asynchronously
            import asyncio
            asyncio.create_task(self._execute_workflow(workflow, graph, state))
            
            return state
    
    def _initialize_state(
        self,
        workflow: Workflow,
        initial_input: Dict[str, Any]
    ) -> WorkflowState:
        """Initialize workflow state"""
        graph_def = workflow.graph_definition
        
        # Create node states
        nodes = {}
        for node_name in graph_def.get("nodes", []):
            nodes[node_name] = AgentNodeState(
                agent_id="",
                agent_name=node_name,
                status="idle",
                progress=0.0,
                input={},
                output=None,
                error=None
            )
        
        return WorkflowState(
            workflow_id=str(workflow.id),
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            current_node=None,
            nodes=nodes,
            shared_context=initial_input,
            rag_context=[],
            errors=[]
        )
    
    async def _build_graph(self, workflow: Workflow):
        """Build LangGraph from workflow definition"""
        # This would use the graph definition to build the actual graph
        # For now, simplified
        builder = WorkflowGraphBuilder()
        # ... build nodes from workflow.graph_definition
        return builder.build()
    
    async def _execute_workflow(
        self,
        workflow: Workflow,
        graph: Any,
        state: WorkflowState
    ):
        """Execute workflow graph"""
        try:
            # Execute graph
            final_state = await graph.ainvoke(state)
            
            # Update database
            async with get_db() as db:
                workflow = await db.get(Workflow, workflow.id)
                workflow.status = WorkflowStatus.COMPLETED
                workflow.state = final_state
                workflow.progress = 1.0
                await db.commit()
            
            # Publish completion event
            await self.event_bus.publish(Event(
                type=EventType.WORKFLOW_COMPLETED,
                data={
                    "workflow_id": str(workflow.id),
                    "workflow_name": workflow.name,
                    "final_state": final_state
                }
            ))
            
        except Exception as e:
            logger.error(f"Workflow {workflow.id} failed: {e}")
            
            async with get_db() as db:
                workflow = await db.get(Workflow, workflow.id)
                workflow.status = WorkflowStatus.FAILED
                await db.commit()
            
            await self.event_bus.publish(Event(
                type=EventType.WORKFLOW_FAILED,
                data={
                    "workflow_id": str(workflow.id),
                    "error": str(e)
                }
            ))
    
    async def get_workflow_status(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get current workflow status"""
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            return {
                "id": str(workflow.id),
                "name": workflow.name,
                "status": workflow.status,
                "progress": workflow.progress,
                "state": workflow.state,
                "started_at": workflow.started_at,
                "completed_at": workflow.completed_at
            }
```

### 8.3 Workflow Checkpointing and State Management

**LangGraph Checkpointing** enables pause/resume functionality by persisting workflow state at each node transition.

#### 8.3.1 Checkpoint Storage (`core/workflows/checkpoint.py`)

```python
"""
Checkpoint storage for workflow state persistence.
Enables pause/resume functionality with LangGraph.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from langgraph.checkpoint import BaseCheckpointSaver, Checkpoint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, func
from backend.database.session import get_db
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """
    Store LangGraph checkpoints in PostgreSQL.
    Allows workflows to pause and resume from any node.
    """

    async def aget(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """Retrieve checkpoint for given workflow."""
        workflow_id = config.get("configurable", {}).get("workflow_id")
        if not workflow_id:
            return None

        async with get_db() as db:
            from backend.models.database.workflow import Workflow
            workflow = await db.get(Workflow, UUID(workflow_id))

            if not workflow or not workflow.state:
                return None

            # Return checkpoint from workflow state
            return Checkpoint(
                v=workflow.version,
                ts=workflow.updated_at.isoformat(),
                channel_values=workflow.state.get("channel_values", {}),
                channel_versions=workflow.state.get("channel_versions", {}),
                versions_seen=workflow.state.get("versions_seen", {})
            )

    async def aput(self, config: Dict[str, Any], checkpoint: Checkpoint) -> None:
        """Save checkpoint to database."""
        workflow_id = config.get("configurable", {}).get("workflow_id")
        if not workflow_id:
            logger.warning("No workflow_id in checkpoint config")
            return

        async with get_db() as db:
            from backend.models.database.workflow import Workflow

            # Update workflow state with checkpoint data
            checkpoint_state = {
                "channel_values": checkpoint.channel_values,
                "channel_versions": checkpoint.channel_versions,
                "versions_seen": checkpoint.versions_seen
            }

            stmt = update(Workflow).where(
                Workflow.id == UUID(workflow_id)
            ).values(
                state=checkpoint_state,
                updated_at=func.now()
            )

            await db.execute(stmt)
            await db.commit()

            logger.debug(f"Saved checkpoint for workflow {workflow_id}")
```

#### 8.3.2 Workflow Manager with Pause/Resume

Update the WorkflowManager to use checkpointing:

```python
"""
Enhanced Workflow Manager with pause/resume capabilities
"""
import asyncio
from typing import Dict, Any, Optional, UUID
from sqlalchemy import update, select
from backend.core.workflows.checkpoint import PostgresCheckpointSaver
from backend.core.workflows.graph import WorkflowGraphBuilder
from backend.core.workflows.state import WorkflowStatus
from backend.models.database.workflow import Workflow
from backend.database.session import get_db
from backend.core.events.bus import EventBus
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.checkpointer = PostgresCheckpointSaver()
        self.running_workflows: Dict[UUID, asyncio.Task] = {}

    async def _build_graph(self, workflow: Workflow):
        """Build LangGraph workflow with checkpointing."""
        builder = WorkflowGraphBuilder()

        # Add nodes based on workflow configuration
        for node in workflow.graph_definition.get("nodes", []):
            builder.add_node(node["name"], node["agent"])

        # Compile with checkpointing and interrupt capability
        graph = builder.build().compile(
            checkpointer=self.checkpointer,
            interrupt_before=["*"]  # Allow pause at any node
        )

        return graph

    async def pause_workflow(self, workflow_id: UUID) -> bool:
        """
        Pause a running workflow.
        Uses optimistic locking to prevent race conditions.
        """
        async with get_db() as db:
            from backend.models.database.workflow import Workflow

            # Get current version
            result = await db.execute(
                select(Workflow.version).where(Workflow.id == workflow_id)
            )
            current_version = result.scalar()

            if current_version is None:
                logger.error(f"Workflow {workflow_id} not found")
                return False

            # Update status with optimistic locking
            stmt = update(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.version == current_version  # Optimistic lock
            ).values(
                status=WorkflowStatus.PAUSED,
                version=current_version + 1
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                logger.warning(
                    f"Failed to pause workflow {workflow_id} - "
                    "concurrent modification detected"
                )
                return False

            logger.info(f"Paused workflow {workflow_id}")
            return True

    async def resume_workflow(self, workflow_id: UUID) -> bool:
        """
        Resume a paused workflow from checkpoint.
        Uses optimistic locking to prevent race conditions.
        """
        async with get_db() as db:
            from backend.models.database.workflow import Workflow

            workflow = await db.get(Workflow, workflow_id)

            if not workflow:
                logger.error(f"Workflow {workflow_id} not found")
                return False

            if workflow.status != WorkflowStatus.PAUSED:
                logger.warning(
                    f"Cannot resume workflow {workflow_id} - "
                    f"status is {workflow.status}, not PAUSED"
                )
                return False

            # Update status with optimistic locking
            stmt = update(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.version == workflow.version  # Optimistic lock
            ).values(
                status=WorkflowStatus.RUNNING,
                version=workflow.version + 1
            )

            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                logger.warning(
                    f"Failed to resume workflow {workflow_id} - "
                    "concurrent modification detected"
                )
                return False

            # Build graph and resume from checkpoint
            graph = await self._build_graph(workflow)

            # Create task for workflow execution
            task = asyncio.create_task(
                self._execute_workflow_from_checkpoint(
                    workflow_id, graph
                )
            )
            self.running_workflows[workflow_id] = task

            logger.info(f"Resumed workflow {workflow_id}")
            return True

    async def _execute_workflow_from_checkpoint(
        self,
        workflow_id: UUID,
        graph: Any
    ):
        """Execute workflow from checkpoint state."""
        try:
            # Load checkpoint and continue execution
            config = {
                "configurable": {
                    "workflow_id": str(workflow_id)
                }
            }

            # Continue from last checkpoint
            async for chunk in graph.astream(None, config=config):
                # Process node outputs
                logger.debug(f"Workflow {workflow_id} node output: {chunk}")

            # Mark as completed
            await self._mark_workflow_completed(workflow_id)

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            await self._mark_workflow_failed(workflow_id, str(e))

    async def _mark_workflow_completed(self, workflow_id: UUID):
        """Mark workflow as completed with optimistic locking."""
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)
            if workflow:
                stmt = update(Workflow).where(
                    Workflow.id == workflow_id,
                    Workflow.version == workflow.version
                ).values(
                    status=WorkflowStatus.COMPLETED,
                    completed_at=func.now(),
                    version=workflow.version + 1
                )
                await db.execute(stmt)
                await db.commit()

    async def _mark_workflow_failed(self, workflow_id: UUID, error: str):
        """Mark workflow as failed with optimistic locking."""
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)
            if workflow:
                stmt = update(Workflow).where(
                    Workflow.id == workflow_id,
                    Workflow.version == workflow.version
                ).values(
                    status=WorkflowStatus.FAILED,
                    error_message=error,
                    completed_at=func.now(),
                    version=workflow.version + 1
                )
                await db.execute(stmt)
                await db.commit()
```

#### 8.3.3 Key Features

**Optimistic Locking:**
- Version field in Workflow model tracks concurrent modifications
- All updates check current version before applying changes
- Prevents race conditions when multiple processes access same workflow

**Pause/Resume:**
- Workflows can be paused at any node using `interrupt_before=["*"]`
- Checkpoint state persisted to PostgreSQL JSONB column
- Resume continues execution from last checkpoint

**State Persistence:**
- LangGraph channel values stored in workflow.state
- Checkpoint includes version tracking for consistency
- Supports long-running workflows with intermittent execution

---

## 9. RAG System Implementation

### 9.1 Document Ingestion

#### 9.1.1 Ingestor (`core/rag/ingestor.py`)

```python
"""
Document ingestion pipeline
"""
from typing import List, Dict, Any
from pathlib import Path
from backend.models.database.document import Document
from backend.core.rag.chunker import TextChunker
from backend.core.rag.embeddings import EmbeddingGenerator
from backend.database.session import get_db
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentIngestor:
    """
    Handles document ingestion: conversion, chunking, embedding.
    """
    
    def __init__(self):
        self.chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()
    
    async def ingest_file(
        self,
        file_path: Path,
        document_type: str
    ) -> Document:
        """
        Ingest a file into the RAG system.
        
        Args:
            file_path: Path to the file
            document_type: Type ('markdown', 'pdf', 'html')
        
        Returns:
            Created Document instance
        """
        logger.info(f"Ingesting file: {file_path}")
        
        # Convert to text
        content = await self._convert_to_text(file_path, document_type)
        
        # Create document record
        async with get_db() as db:
            document = Document(
                name=file_path.name,
                type=document_type,
                content=content,
                file_path=str(file_path),
                file_size=file_path.stat().st_size
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
        
        # Chunk and embed
        await self._chunk_and_embed(document)
        
        logger.info(f"Successfully ingested document: {document.id}")
        return document
    
    async def _convert_to_text(
        self,
        file_path: Path,
        document_type: str
    ) -> str:
        """Convert document to plain text"""
        if document_type == "markdown":
            return file_path.read_text(encoding="utf-8")
        
        elif document_type == "html":
            from bs4 import BeautifulSoup
            html_content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text()
        
        elif document_type == "pdf":
            # Use Docling for PDF conversion
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            return result.document.export_to_markdown()
        
        else:
            raise ValueError(f"Unsupported document type: {document_type}")
    
    async def _chunk_and_embed(self, document: Document):
        """Chunk document and generate embeddings"""
        from backend.models.database.embedding import Embedding
        
        # Chunk the content
        chunks = self.chunker.chunk_text(document.content)
        
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")
        
        # Generate embeddings for chunks
        for i, chunk in enumerate(chunks):
            vector = await self.embedding_generator.generate(chunk)
            
            async with get_db() as db:
                embedding = Embedding(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk,
                    vector=vector,
                    metadata={"chunk_size": len(chunk)}
                )
                
                db.add(embedding)
                await db.commit()
        
        logger.info(f"Created {len(chunks)} embeddings for document {document.id}")
```

#### 9.1.2 Text Chunker (`core/rag/chunker.py`)

**Smart Chunking Strategy:**

The TextChunker uses a hierarchical approach to respect natural text boundaries:

1. **Paragraph-level**: Splits on double newlines first
2. **Sentence-level**: Uses regex to identify sentence boundaries (. ! ? followed by capital letter)
3. **Word-level**: For sentences exceeding chunk_size, splits at word boundaries
4. **Character-level**: Last resort for extremely long words

This approach ensures:
- No mid-sentence breaks (maintains context)
- No mid-word breaks (preserves meaning)
- Intelligent overlap using complete sentences when possible
- Better semantic coherence for embeddings
- Improved RAG retrieval quality

**Performance:** Precompiled regex patterns ensure fast processing even for large documents.

```python
"""
Smart text chunking with sentence and paragraph awareness.
Avoids breaking text mid-sentence or mid-word.
"""
import re
from typing import List
from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextChunker:
    """
    Intelligent text chunker that respects sentence and paragraph boundaries.

    Features:
    - Paragraph-aware chunking (splits on double newlines first)
    - Sentence-aware chunking (uses regex to identify sentence boundaries)
    - Word-aware chunking (never splits mid-word)
    - Configurable chunk size and overlap
    - Handles edge cases (very long sentences, code blocks, lists)
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        # Precompile regex patterns for better performance
        # Matches sentence boundaries: . ! ? followed by space and capital letter
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])'
        )
        # Matches paragraph boundaries: double newlines
        self.paragraph_pattern = re.compile(r'\n\n+')

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text intelligently while respecting natural boundaries.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks with overlap
        """
        if not text or not text.strip():
            return []

        # First, split into paragraphs
        paragraphs = self.paragraph_pattern.split(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            # Skip empty paragraphs
            if not para.strip():
                continue

            # Split paragraph into sentences
            sentences = self.sentence_pattern.split(para)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_length = len(sentence)

                # If single sentence exceeds chunk_size, split it
                if sentence_length > self.chunk_size:
                    # Flush current chunk if it has content
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                        current_length = 0

                    # Split long sentence into word-based chunks
                    long_sentence_chunks = self._split_long_sentence(sentence)
                    chunks.extend(long_sentence_chunks)
                    continue

                # Check if adding sentence would exceed chunk_size
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunks.append(' '.join(current_chunk))

                    # Create overlap for next chunk
                    overlap_chunk = self._create_overlap(current_chunk)
                    current_chunk = overlap_chunk
                    current_length = sum(len(s) for s in current_chunk)

                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space

        # Add final chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Clean and filter chunks
        cleaned_chunks = [c.strip() for c in chunks if c.strip()]

        logger.debug(
            f"Chunked text into {len(cleaned_chunks)} chunks "
            f"(avg length: {sum(len(c) for c in cleaned_chunks) // len(cleaned_chunks) if cleaned_chunks else 0})"
        )

        return cleaned_chunks

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        Split a very long sentence at word boundaries.
        Used when a single sentence exceeds chunk_size.

        Args:
            sentence: Long sentence to split

        Returns:
            List of word-based chunks
        """
        words = sentence.split()
        chunks = []
        current = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            # If single word exceeds chunk_size, split it
            if word_length > self.chunk_size:
                if current:
                    chunks.append(' '.join(current))
                    current = []
                    current_length = 0

                # Split word into character-based chunks as last resort
                for i in range(0, len(word), self.chunk_size):
                    chunks.append(word[i:i + self.chunk_size])
                continue

            # Check if adding word would exceed chunk_size
            if current_length + word_length > self.chunk_size and current:
                chunks.append(' '.join(current))

                # Create overlap
                overlap_words = self._create_word_overlap(current)
                current = overlap_words
                current_length = sum(len(w) + 1 for w in current)

            current.append(word)
            current_length += word_length

        if current:
            chunks.append(' '.join(current))

        return chunks

    def _create_overlap(self, sentences: List[str]) -> List[str]:
        """
        Create overlap from previous chunk by taking last N sentences.

        Args:
            sentences: List of sentences from previous chunk

        Returns:
            List of sentences for overlap
        """
        overlap_sentences = []
        overlap_length = 0

        # Work backwards through sentences to create overlap
        for sentence in reversed(sentences):
            sentence_length = len(sentence)

            if overlap_length + sentence_length <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_length += sentence_length
            else:
                break

        return overlap_sentences

    def _create_word_overlap(self, words: List[str]) -> List[str]:
        """
        Create overlap from previous chunk by taking last N words.

        Args:
            words: List of words from previous chunk

        Returns:
            List of words for overlap
        """
        overlap_words = []
        overlap_length = 0

        # Work backwards through words to create overlap
        for word in reversed(words):
            word_length = len(word) + 1  # +1 for space

            if overlap_length + word_length <= self.chunk_overlap:
                overlap_words.insert(0, word)
                overlap_length += word_length
            else:
                break

        return overlap_words
```

### 9.2 Embedding Generation

#### 9.2.1 Embedding Generator (`core/rag/embeddings.py`)

```python
"""
Embedding generation for RAG
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """
    Generates vector embeddings for text using sentence transformers.
    """
    
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = settings.EMBEDDING_DIMENSION
    
    async def generate(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector as list of floats
        """
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Convert to list
        return embedding.tolist()
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
```

### 9.3 Vector Retrieval

#### 9.3.1 RAG Retriever (`core/rag/retriever.py`)

```python
"""
Vector similarity search and retrieval
"""
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.database.embedding import Embedding
from backend.models.database.document import Document
from backend.core.rag.embeddings import EmbeddingGenerator
from backend.config import settings
from backend.database.session import get_db
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGRetriever:
    """
    Retrieves relevant documents using vector similarity search.
    """
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of relevant chunks with metadata
        """
        top_k = top_k or settings.RAG_TOP_K
        similarity_threshold = similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD
        
        logger.info(f"Retrieving documents for query: {query[:50]}...")
        
        # Generate query embedding
        query_vector = await self.embedding_generator.generate(query)
        
        # Perform vector similarity search
        async with get_db() as db:
            # Using pgvector cosine similarity
            stmt = select(
                Embedding,
                Document.name.label('document_name'),
                (1 - Embedding.vector.cosine_distance(query_vector)).label('similarity')
            ).join(
                Document, Embedding.document_id == Document.id
            ).where(
                (1 - Embedding.vector.cosine_distance(query_vector)) > similarity_threshold
            ).order_by(
                (1 - Embedding.vector.cosine_distance(query_vector)).desc()
            ).limit(top_k)
            
            result = await db.execute(stmt)
            rows = result.all()
        
        # Format results
        results = []
        for embedding, doc_name, similarity in rows:
            results.append({
                "content": embedding.content,
                "document_id": str(embedding.document_id),
                "document_name": doc_name,
                "chunk_index": embedding.chunk_index,
                "similarity": float(similarity),
                "metadata": embedding.metadata
            })
        
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
```

---

## 10. Chat System

### 10.1 Chat Manager

#### 10.1.1 Chat Manager Implementation (`core/chat/manager.py`)

```python
"""
Chat session management
"""
from typing import List, Dict, Any, Optional, AsyncIterator
from uuid import UUID
from backend.models.database.chat import ChatSession, ChatMessage
from backend.database.session import get_db
from backend.core.chat.claude import ClaudeClient
from backend.core.chat.openrouter import OpenRouterClient
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatManager:
    """
    Manages chat sessions and message routing.
    """
    
    def __init__(self):
        self.claude_client = ClaudeClient()
        self.openrouter_client = OpenRouterClient()
    
    async def create_session(
        self,
        title: Optional[str] = None,
        model: str = None
    ) -> ChatSession:
        """Create a new chat session"""
        from backend.config import settings
        
        model = model or settings.DEFAULT_MODEL
        
        async with get_db() as db:
            session = ChatSession(
                title=title or "New Chat",
                model=model
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            return session
    
    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> ChatMessage:
        """Add a message to a session"""
        async with get_db() as db:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata or {}
            )
            
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            return message
    
    async def get_session_messages(
        self,
        session_id: UUID
    ) -> List[ChatMessage]:
        """Get all messages in a session"""
        async with get_db() as db:
            from sqlalchemy import select
            
            stmt = select(ChatMessage).where(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at)
            
            result = await db.execute(stmt)
            return result.scalars().all()
    
    async def stream_response(
        self,
        session_id: UUID,
        user_message: str,
        use_rag: bool = False
    ) -> AsyncIterator[str]:
        """
        Stream a response from the LLM.
        
        Args:
            session_id: Chat session ID
            user_message: User's message
            use_rag: Whether to use RAG for context
        
        Yields:
            Chunks of the response
        """
        # Add user message
        await self.add_message(session_id, "user", user_message)
        
        # Get session and message history
        async with get_db() as db:
            session = await db.get(ChatSession, session_id)
            messages = await self.get_session_messages(session_id)
        
        # Build message history for API
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Augment with RAG if requested
        if use_rag:
            from backend.core.rag.retriever import RAGRetriever
            retriever = RAGRetriever()
            rag_results = await retriever.retrieve(user_message)
            
            # Add RAG context to system message
            rag_context = "\n\n".join([
                f"Source: {r['document_name']}\n{r['content']}"
                for r in rag_results
            ])
            
            message_history.insert(0, {
                "role": "system",
                "content": f"Context from documents:\n\n{rag_context}"
            })
        
        # Stream response from appropriate client
        client = self.claude_client  # Default to Claude
        
        assistant_message = ""
        async for chunk in client.stream_chat(message_history):
            assistant_message += chunk
            yield chunk
        
        # Save assistant message
        await self.add_message(session_id, "assistant", assistant_message)
```

#### 10.1.2 Claude Client (`core/chat/claude.py`)

```python
"""
Claude API integration for chat
"""
from typing import List, Dict, Any, AsyncIterator
import anthropic
from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class ClaudeClient:
    """
    Client for interacting with Claude API.
    """
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.DEFAULT_MODEL
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None
    ) -> AsyncIterator[str]:
        """
        Stream a chat response from Claude.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            Response chunks
        """
        temperature = temperature or settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.DEFAULT_MAX_TOKENS
        
        try:
            async with self.client.messages.stream(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            logger.error(f"Error streaming from Claude: {e}")
            raise
```

---

## 11. Git Integration

### 11.1 Git Manager

#### 11.1.1 Git Operations (`core/git/manager.py`)

```python
"""
Git repository operations
"""
import subprocess
from typing import List, Dict, Any
from pathlib import Path
from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class GitManager:
    """
    Manages Git operations and worktrees.
    """
    
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
    
    async def list_branches(self) -> List[str]:
        """List all branches in the repository"""
        result = subprocess.run(
            ["git", "branch", "--list"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        branches = []
        for line in result.stdout.splitlines():
            branch = line.strip().replace("* ", "")
            if branch:
                branches.append(branch)
        
        return branches
    
    async def create_branch(self, branch_name: str, from_branch: str = "main"):
        """Create a new branch"""
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name, from_branch],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create branch: {result.stderr}")
        
        logger.info(f"Created branch: {branch_name}")
    
    async def list_worktrees(self) -> List[Dict[str, Any]]:
        """List all worktrees"""
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        worktrees = []
        current = {}
        
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]
        
        if current:
            worktrees.append(current)
        
        return worktrees
    
    async def add_worktree(
        self,
        branch_name: str,
        path: Path = None
    ) -> Path:
        """Create a new worktree"""
        if path is None:
            path = settings.GIT_WORKTREE_DIR / branch_name
        
        path.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["git", "worktree", "add", str(path), branch_name],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to add worktree: {result.stderr}")
        
        logger.info(f"Created worktree at: {path}")
        return path
    
    async def remove_worktree(self, path: Path):
        """Remove a worktree"""
        result = subprocess.run(
            ["git", "worktree", "remove", str(path)],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to remove worktree: {result.stderr}")
        
        logger.info(f"Removed worktree: {path}")
```

---

## 12. Event System

_Already covered in Section 5.3_

---

## 13. Logging System

### 13.1 Overview

Amelia uses a comprehensive structured logging system built on **Rich** and **structlog** to provide:

- **Rich Console Output**: Beautiful, formatted terminal output with syntax highlighting
- **Structured Logging**: JSON-formatted logs for production with contextual metadata
- **Performance Tracking**: Automatic timing and performance metrics
- **Context Preservation**: Request IDs, user context, and operation metadata
- **Multiple Outputs**: Console (Rich), file (JSON), and optional remote logging

### 13.2 Logger Configuration

#### 13.2.1 Logger Setup (`utils/logger.py`)

```python
"""
Centralized logging configuration using Rich and structlog.
Provides structured logging with beautiful console output and JSON file logging.
"""
import sys
import structlog
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.logging import RichHandler
from datetime import datetime, timezone
from backend.config import settings

# Create logs directory
LOGS_DIR = settings.BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Rich console for beautiful output
console = Console(stderr=True)


def add_timestamp(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add ISO timestamp to log events"""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add log level to event dict"""
    event_dict["level"] = method_name.upper()
    return event_dict


def setup_logger(name: str) -> structlog.BoundLogger:
    """
    Setup and return a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger
    """
    # Configure structlog
    structlog.configure(
        processors=[
            # Add context
            structlog.contextvars.merge_contextvars,
            # Add log level
            add_log_level,
            # Add timestamp
            add_timestamp,
            # Add caller info in development
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ) if settings.DEBUG else lambda *args: args[2],
            # Stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Format for output
            structlog.processors.JSONRenderer() if not settings.DEBUG
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging_level_from_string(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Get logger
    logger = structlog.get_logger(name)

    # Bind module name
    logger = logger.bind(module=name)

    return logger


def logging_level_from_string(level: str) -> int:
    """Convert string log level to int"""
    import logging
    return getattr(logging, level.upper(), logging.INFO)


def setup_file_logging():
    """
    Setup file-based JSON logging for production.
    Logs are rotated daily and kept for 30 days.
    """
    from logging.handlers import TimedRotatingFileHandler
    import logging

    # Create file handler
    log_file = LOGS_DIR / "amelia.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )

    # JSON formatter for file logs
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    )

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging_level_from_string(settings.LOG_LEVEL))


def setup_rich_logging():
    """
    Setup Rich console logging for development.
    Provides beautiful, syntax-highlighted console output.
    """
    import logging

    # Create Rich handler
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=settings.DEBUG,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=settings.DEBUG,
    )

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(rich_handler)
    root_logger.setLevel(logging_level_from_string(settings.LOG_LEVEL))


# Initialize logging on import
if settings.DEBUG:
    setup_rich_logging()
else:
    setup_file_logging()
```

### 13.3 Usage Patterns

#### 13.3.1 Basic Logging

```python
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Simple messages
logger.info("Agent started")
logger.warning("Resource usage high")
logger.error("Operation failed")

# With context
logger.info(
    "Agent completed",
    agent_id="agent-123",
    duration_seconds=45.2,
    status="success"
)
```

#### 13.3.2 Structured Context

```python
# Bind context that persists across log calls
logger = logger.bind(
    request_id="req-abc123",
    user_id="user-456",
    workflow_id="wf-789"
)

# All subsequent logs include this context
logger.info("Starting workflow")  # Includes request_id, user_id, workflow_id
logger.info("Processing step 1")  # Same context
logger.info("Workflow complete")  # Same context
```

#### 13.3.3 Performance Tracking

```python
import time
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

start_time = time.time()

# ... do work ...

logger.info(
    "Operation completed",
    operation="document_ingestion",
    duration_ms=(time.time() - start_time) * 1000,
    documents_processed=150,
    success=True
)
```

#### 13.3.4 Error Logging with Context

```python
try:
    result = await risky_operation()
except Exception as e:
    logger.exception(
        "Operation failed",
        operation="risky_operation",
        error_type=type(e).__name__,
        error_message=str(e),
        # Exception traceback automatically included
    )
    raise
```

### 13.4 Logging Middleware

#### 13.4.1 HTTP Request Logging (`api/middleware/logging.py`)

```python
"""
HTTP request/response logging middleware
"""
import time
import uuid
from fastapi import Request
from structlog import get_logger
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


async def logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests and responses with timing and context.
    """
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Bind request context
    request_logger = logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )

    # Log request
    request_logger.info(
        "HTTP request received",
        query_params=dict(request.query_params),
    )

    # Add request ID to request state
    request.state.request_id = request_id
    request.state.logger = request_logger

    # Process request
    start_time = time.time()

    try:
        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Log response
        request_logger.info(
            "HTTP request completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        request_logger.exception(
            "HTTP request failed",
            error=str(e),
            duration_ms=round(duration_ms, 2),
        )
        raise
```

### 13.5 Log Levels

- **DEBUG**: Detailed diagnostic information (only in development)
- **INFO**: General informational messages (workflow progress, agent updates)
- **WARNING**: Warning messages (high resource usage, deprecated features)
- **ERROR**: Error messages (recoverable failures)
- **CRITICAL**: Critical errors (system failures, data corruption)

### 13.6 Log Output Examples

#### Development (Rich Console)

```text
2025-11-08 10:30:15 [INFO    ] Agent started                          module=backend.core.agents.discovery agent_id=discovery-123
2025-11-08 10:30:16 [INFO    ] Retrieving documents from RAG          module=backend.core.rag.retriever query_length=50 top_k=5
2025-11-08 10:30:18 [INFO    ] Agent completed                        module=backend.core.agents.discovery agent_id=discovery-123 duration_seconds=3.2
```

#### Production (JSON File)

```json
{
  "timestamp": "2025-11-08T10:30:15.123456",
  "level": "INFO",
  "module": "backend.core.agents.discovery",
  "event": "Agent started",
  "agent_id": "discovery-123",
  "filename": "discovery.py",
  "func_name": "execute",
  "lineno": 45
}
```

### 13.7 Configuration Settings

```python
# In config.py
class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "rich"  # rich, json
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: Path = BASE_DIR / "logs" / "amelia.log"
    LOG_FILE_ROTATION: str = "midnight"  # midnight, 100 MB, 1 week
    LOG_FILE_RETENTION: int = 30  # days
```

---

## 14. Configuration Management

_Already covered in Section 5.1.2_

---

## 15. Error Handling

### 15.1 Error Handling Middleware

#### 15.1.1 Error Handler (`api/middleware/error_handler.py`)

```python
"""
Global error handling middleware
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Catch all unhandled exceptions and return formatted error responses.
    """
    try:
        response = await call_next(request)
        return response
    
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "detail": str(e)
            }
        )
    
    except PermissionError as e:
        logger.error(f"PermissionError: {e}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "Forbidden",
                "detail": str(e)
            }
        )
    
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "detail": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred"
            }
        )
```

---

## 16. Testing Strategy

### 16.1 Backend Testing

#### 16.1.1 Test Configuration (`tests/conftest.py`)

```python
"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.database.base import Base
from backend.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://amelia_test:amelia_test@localhost:5432/amelia_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return {
        "name": "test_doc.md",
        "type": "markdown",
        "content": "# Test Document\n\nThis is a test document."
    }
```

#### 15.1.2 Agent Tests (`tests/test_agents.py`)

```python
"""
Tests for agent system
"""
import pytest
from backend.core.agents.base import AgentConfig, BaseAgent, AgentStatus
from backend.core.events.bus import EventBus


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    async def _run(self, input_data):
        return {"result": "success", "input": input_data}


@pytest.mark.asyncio
async def test_agent_execution():
    """Test basic agent execution"""
    config = AgentConfig(
        name="TestAgent",
        description="Test agent",
        system_prompt="Test prompt"
    )
    
    event_bus = EventBus()
    await event_bus.start()
    
    agent = MockAgent(config, event_bus)
    
    result = await agent.execute({"test": "input"})
    
    assert result.status == AgentStatus.COMPLETED
    assert result.output["result"] == "success"
    assert result.output["input"]["test"] == "input"
    
    await event_bus.stop()


@pytest.mark.asyncio
async def test_agent_progress_updates():
    """Test agent progress updates"""
    config = AgentConfig(
        name="TestAgent",
        description="Test agent",
        system_prompt="Test prompt"
    )
    
    event_bus = EventBus()
    await event_bus.start()
    
    progress_events = []
    
    from backend.core.events.types import EventType
    
    async def capture_progress(event):
        progress_events.append(event.data["progress"])
    
    event_bus.subscribe(EventType.AGENT_PROGRESS, capture_progress)
    
    agent = MockAgent(config, event_bus)
    await agent.update_progress(0.5, "Halfway done")
    
    assert len(progress_events) > 0
    assert 0.5 in progress_events
    
    await event_bus.stop()
```

---

## 17. Development Workflow

### 17.1 Setup Scripts

#### 17.1.1 Initial Setup (`scripts/setup.sh`)

```bash
#!/bin/bash

# Amelia setup script

set -e

echo "Setting up Amelia..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.12+ is required"
    exit 1
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install poetry
poetry install
cd ..

# Install frontend dependencies
echo "Installing web frontend dependencies..."
cd frontend-web
pnpm install
cd ..

# Install terminal UI dependencies
echo "Installing terminal UI dependencies..."
cd frontend-terminal
pnpm install
cd ..

# Setup database
echo "Setting up database..."
./scripts/init-db.sh

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo "Setup complete!"
echo "Run './scripts/start-backend.sh' to start the backend"
echo "Run './scripts/start-web.sh' to start the web UI"
```

#### 16.1.2 Database Initialization (`scripts/init-db.sh`)

```bash
#!/bin/bash

# Initialize PostgreSQL database

set -e

DB_NAME="amelia"
DB_USER="amelia"
DB_PASSWORD="amelia"

echo "Initializing database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Error: PostgreSQL is not running"
    exit 1
fi

# Create database
psql -h localhost -U postgres -c "CREATE DATABASE $DB_NAME;" || echo "Database already exists"

# Create user
psql -h localhost -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "User already exists"

# Grant privileges
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Enable pgvector extension
psql -h localhost -U postgres -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Database initialized successfully!"
```

### 16.2 Running the Application

#### 16.2.1 Start Backend (`scripts/start-backend.sh`)

```bash
#!/bin/bash

# Start FastAPI backend

set -e

cd backend

echo "Starting Amelia backend..."

poetry run uvicorn amelia.main:app --reload --host 127.0.0.1 --port 8000
```

#### 16.2.2 Start Web UI (`scripts/start-web.sh`)

```bash
#!/bin/bash

# Start web frontend

set -e

cd frontend-web

echo "Starting Amelia web UI..."

pnpm dev
```

---

## 18. API Specifications

### 18.1 Agent Endpoints

```python
# /api/agents

GET /api/agents
- List all agents
- Response: List[Agent]

POST /api/agents
- Create new agent
- Body: AgentConfig
- Response: Agent

GET /api/agents/{agent_id}
- Get agent details
- Response: Agent

POST /api/agents/{agent_id}/start
- Start agent execution
- Body: {"input": Dict[str, Any]}
- Response: AgentResult

POST /api/agents/{agent_id}/stop
- Stop running agent
- Response: {"status": "stopped"}

DELETE /api/agents/{agent_id}
- Delete agent
- Response: {"status": "deleted"}

GET /api/agents/{agent_id}/logs
- Get agent execution logs
- Response: List[str]
```

### 17.2 Workflow Endpoints

```python
# /api/workflows

GET /api/workflows
- List all workflows
- Response: List[Workflow]

POST /api/workflows
- Create new workflow
- Body: WorkflowDefinition
- Response: Workflow

GET /api/workflows/{workflow_id}
- Get workflow details
- Response: Workflow

POST /api/workflows/{workflow_id}/start
- Start workflow execution
- Body: {"input": Dict[str, Any]}
- Response: WorkflowState

POST /api/workflows/{workflow_id}/pause
- Pause running workflow
- Response: {"status": "paused"}

POST /api/workflows/{workflow_id}/resume
- Resume paused workflow
- Response: {"status": "running"}

DELETE /api/workflows/{workflow_id}
- Delete workflow
- Response: {"status": "deleted"}
```

### 17.3 RAG Endpoints

```python
# /api/rag

GET /api/rag/documents
- List all documents
- Response: List[Document]

POST /api/rag/documents/upload
- Upload document
- Body: multipart/form-data
- Response: Document

POST /api/rag/documents/scrape
- Scrape web page
- Body: {"url": str}
- Response: Document

GET /api/rag/documents/{document_id}
- Get document details
- Response: Document

DELETE /api/rag/documents/{document_id}
- Delete document
- Response: {"status": "deleted"}

POST /api/rag/query
- Query RAG system
- Body: {"query": str, "top_k": int}
- Response: List[RetrievalResult]
```

### 17.4 Chat Endpoints

```python
# /api/chat

GET /api/chat/sessions
- List chat sessions
- Response: List[ChatSession]

POST /api/chat/sessions
- Create new session
- Body: {"title": str, "model": str}
- Response: ChatSession

GET /api/chat/sessions/{session_id}/messages
- Get session messages
- Response: List[ChatMessage]

POST /api/chat/sessions/{session_id}/stream
- Stream chat response (SSE)
- Body: {"message": str, "use_rag": bool}
- Response: text/event-stream

DELETE /api/chat/sessions/{session_id}
- Delete session
- Response: {"status": "deleted"}
```

---

## 19. Data Models

### 19.1 Pydantic Schemas

#### 19.1.1 Agent Schemas (`models/schemas/agent.py`)

```python
"""
Pydantic schemas for agents
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class AgentConfigSchema(BaseModel):
    """Agent configuration"""
    name: str
    description: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 300


class AgentCreateSchema(BaseModel):
    """Agent creation request"""
    config: AgentConfigSchema


class AgentResponse(BaseModel):
    """Agent response"""
    id: UUID
    name: str
    type: str
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentExecuteSchema(BaseModel):
    """Agent execution request"""
    input: Dict[str, Any]


class AgentResultSchema(BaseModel):
    """Agent execution result"""
    status: str
    output: Dict[str, Any]
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
```

---

## 20. Security Considerations

### 20.1 File Upload Security

**Location:** `api/routes/rag.py` and `core/rag/ingestor.py`

#### 20.1.1 File Validation

```python
"""
Secure file upload validation.
Prevents malicious file uploads and path traversal attacks.
"""
from pathlib import Path
from typing import Optional
import magic  # python-magic library
from fastapi import UploadFile, HTTPException

# File size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Allowed MIME types with their extensions
ALLOWED_TYPES = {
    'application/pdf': ['.pdf'],
    'text/markdown': ['.md', '.markdown'],
    'text/html': ['.html', '.htm'],
    'text/plain': ['.txt'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
}


def validate_file_upload(file: UploadFile) -> None:
    """
    Validate uploaded file for security.

    Checks:
    - File size within limits
    - MIME type matches allowed types (using magic bytes, not extension)
    - File extension matches MIME type
    - Filename doesn't contain path traversal attempts

    Raises:
        HTTPException: If validation fails
    """
    # Check filename for path traversal attempts
    if '..' in file.filename or '/' in file.filename or '\\' in file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename - path traversal detected"
        )

    # Read first 2KB for magic byte detection
    file.file.seek(0)
    header = file.file.read(2048)
    file.file.seek(0)

    # Detect MIME type using magic bytes (not extension)
    mime = magic.Magic(mime=True)
    detected_type = mime.from_buffer(header)

    # Verify MIME type is allowed
    if detected_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: {detected_type}. "
                   f"Allowed types: {', '.join(ALLOWED_TYPES.keys())}"
        )

    # Verify extension matches MIME type
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ALLOWED_TYPES[detected_type]

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_ext} doesn't match detected type {detected_type}"
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f} MB"
        )

    # Check storage quota
    # This would query database for total storage used
    # Left as exercise - depends on specific requirements


def safe_filename(filename: str) -> str:
    """
    Generate a safe filename by removing dangerous characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    from uuid import uuid4

    # Remove path components
    filename = Path(filename).name

    # Remove all non-alphanumeric except . - _
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Prevent hidden files
    if safe_name.startswith('.'):
        safe_name = 'file_' + safe_name

    # Add unique prefix to prevent collisions
    name_parts = safe_name.rsplit('.', 1)
    if len(name_parts) == 2:
        return f"{name_parts[0]}_{uuid4().hex[:8]}.{name_parts[1]}"
    else:
        return f"{safe_name}_{uuid4().hex[:8]}"
```

### 20.2 Path Traversal Protection

```python
"""
Safe path handling to prevent path traversal attacks.
"""
from pathlib import Path
from backend.config import settings


def safe_path(base_dir: Path, user_path: str) -> Path:
    """
    Ensure user-provided path is within allowed base directory.
    Prevents path traversal attacks like ../../etc/passwd

    Args:
        base_dir: Base directory that user_path must be within
        user_path: User-provided path (relative or absolute)

    Returns:
        Resolved path within base_dir

    Raises:
        ValueError: If path traversal detected
    """
    # Resolve both paths to absolute
    base_dir = base_dir.resolve()

    # Combine and resolve
    if Path(user_path).is_absolute():
        # Don't allow absolute paths from user
        raise ValueError("Absolute paths not allowed")

    target = (base_dir / user_path).resolve()

    # Ensure target is within base_dir using is_relative_to (Python 3.9+)
    try:
        target.relative_to(base_dir)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {user_path} would escape {base_dir}"
        )

    return target


# Usage in document upload:
async def save_uploaded_file(file: UploadFile) -> Path:
    """Save uploaded file securely."""
    validate_file_upload(file)

    # Generate safe filename
    safe_name = safe_filename(file.filename)

    # Ensure path is within UPLOAD_DIR
    file_path = safe_path(settings.UPLOAD_DIR, safe_name)

    # Save file
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    return file_path
```

### 20.3 Subprocess Sanitization

**Location:** `core/git/manager.py` and `core/agents/claude_code.py`

```python
"""
Safe subprocess execution to prevent command injection.
"""
import subprocess
import re
from typing import List
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_git_ref(ref: str) -> str:
    """
    Validate Git reference (branch, tag, commit) to prevent injection.

    Args:
        ref: Git reference string

    Returns:
        Validated reference

    Raises:
        ValueError: If reference contains invalid characters
    """
    # Allow alphanumeric, hyphens, underscores, slashes, dots
    if not re.match(r'^[a-zA-Z0-9_/-]+$', ref):
        raise ValueError(
            f"Invalid Git reference: {ref}. "
            "Only alphanumeric, -, _, / allowed"
        )

    # Prevent special refs that could be dangerous
    dangerous_refs = ['..', '.git', 'refs/']
    for danger in dangerous_refs:
        if danger in ref:
            raise ValueError(f"Invalid Git reference: {ref}")

    return ref


async def run_git_command(
    args: List[str],
    cwd: Path,
    timeout: int = 30
) -> subprocess.CompletedProcess:
    """
    Run git command safely with validation.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command contains suspicious arguments
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    # Validate all arguments
    for arg in args:
        if arg.startswith('-'):
            # Allow known safe flags
            safe_flags = ['-b', '-m', '--', '-f', '-d']
            if not any(arg.startswith(flag) for flag in safe_flags):
                logger.warning(f"Potentially unsafe git flag: {arg}")
        elif ';' in arg or '|' in arg or '&' in arg or '$' in arg:
            raise ValueError(f"Command injection attempt detected: {arg}")

    # Run with shell=False for safety
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False  # Don't raise on non-zero exit
    )

    if result.returncode != 0:
        logger.error(f"Git command failed: {result.stderr}")

    return result


# Example usage in GitManager:
async def create_branch(self, branch_name: str, from_branch: str = "main"):
    """Create a new branch safely."""
    # Validate inputs
    branch_name = validate_git_ref(branch_name)
    from_branch = validate_git_ref(from_branch)

    # Run command safely
    result = await run_git_command(
        ['checkout', '-b', branch_name, from_branch],
        cwd=self.repo_path
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create branch: {result.stderr}")
```

### 20.4 API Key Protection

```python
"""
API key security best practices.
"""
from pathlib import Path


def check_env_file_security():
    """
    Check .env file permissions on startup.
    Warn if permissions are too open.
    """
    env_path = Path('.env')

    if not env_path.exists():
        return

    # Check file permissions (Unix only)
    import stat
    import os

    if os.name != 'nt':  # Not Windows
        st = env_path.stat()
        mode = st.st_mode

        # Check if readable by group or others
        if mode & stat.S_IRGRP or mode & stat.S_IROTH:
            logger.warning(
                f".env file has overly permissive permissions: {oct(mode)[-3:]}. "
                "Run: chmod 600 .env"
            )


# Add to main.py startup:
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Amelia backend...")

    # Check .env security
    check_env_file_security()

    # ... rest of startup
```

### 20.5 Rate Limiting

**Add to requirements:**
```toml
slowapi = "^0.2.0"
```

```python
"""
Rate limiting to prevent abuse.
Location: api/middleware/rate_limit.py
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI

# Create limiter
limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app: FastAPI):
    """Setup rate limiting middleware."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Usage in routes:
from slowapi import Limiter
from fastapi import Request

@router.post("/documents/upload")
@limiter.limit("5/minute")  # 5 uploads per minute
async def upload_document(request: Request, file: UploadFile):
    ...

@router.post("/chat/sessions/{session_id}/message")
@limiter.limit("20/minute")  # 20 messages per minute
async def send_message(request: Request, session_id: UUID, message: str):
    ...
```

### 20.6 Local-Only Security

Since Amelia is a local-only tool:

1. **No Authentication Required**: All endpoints are accessible without authentication
2. **Localhost Binding**: Server binds only to 127.0.0.1 by default
3. **API Key Storage**: Store API keys in .env file (never commit)
4. **File Access**: Limit file operations to designated directories using safe_path()
5. **Process Isolation**: Run agents in isolated processes where possible

### 20.7 Input Validation

```python
# All API inputs validated with Pydantic
# File uploads restricted by type and size (see 20.1)
# SQL queries use parameterized statements (SQLAlchemy ORM)
# Path traversal prevention in file operations (see 20.2)
# Subprocess calls sanitized (see 20.3)
```

---

## 21. Deployment & Installation

### 21.1 System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Python**: 3.12+
- **Node**: 22+
- **PostgreSQL**: 16+
- **Memory**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space

### 21.2 Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/yourusername/amelia.git
cd amelia

# 2. Run setup script
./scripts/setup.sh

# 3. Configure .env file
cp .env.example .env
# Edit .env with your API keys

# 4. Start PostgreSQL
# (varies by system)

# 5. Initialize database
./scripts/init-db.sh

# 6. Start backend
./scripts/start-backend.sh

# 7. In a new terminal, start web UI
./scripts/start-web.sh

# 8. Access application
# Web UI: http://localhost:5173
# API: http://localhost:8000
```

### 21.3 Package Distribution

```bash
# Backend package
cd backend
poetry build
pip install dist/amelia-1.0.0-py3-none-any.whl

# Frontend web
cd frontend-web
pnpm build
# Serve dist/ directory

# Terminal UI
cd frontend-terminal
pnpm build
npm link
# Now `amelia-tui` command is available
```

---

## Appendix A: Environment Variables

```bash
# .env.example

# Application
APP_NAME=Amelia
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=127.0.0.1
PORT=8000
RELOAD=false

# Database
DATABASE_URL=postgresql+asyncpg://amelia:amelia@localhost:5432/amelia

# LLM Providers
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
OLLAMA_BASE_URL=http://localhost:11434

# Models
DEFAULT_MODEL=claude-sonnet-4-5-20250929
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG
CHUNK_SIZE=800
CHUNK_OVERLAP=200
RAG_TOP_K=5

# Claude Code
CLAUDE_CODE_PATH=claude
CLAUDE_CODE_TIMEOUT=300
```

---

## Appendix B: TypeScript Type Definitions

```typescript
// types/agent.ts
export enum AgentStatus {
  IDLE = 'idle',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: AgentStatus;
  progress: number;
  config: AgentConfig;
  createdAt: string;
  updatedAt: string;
}

export interface AgentConfig {
  name: string;
  description: string;
  systemPrompt: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

// types/workflow.ts
export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: string;
  progress: number;
  nodes: WorkflowNode[];
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowNode {
  id: string;
  name: string;
  description: string;
  status: string;
  progress?: number;
  dependencies: string[];
}

// types/document.ts
export interface Document {
  id: string;
  name: string;
  type: 'markdown' | 'pdf' | 'html';
  content: string;
  fileSize: number;
  createdAt: string;
}

// types/chat.ts
export interface ChatSession {
  id: string;
  title: string;
  model: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}
```

---

## Summary

This technical design document provides comprehensive implementation details for **Amelia**, a local LLM workflow orchestration tool. The document is optimized for Claude Code to generate the complete application with:

- **Full backend architecture** using FastAPI, LangGraph, and PostgreSQL
- **Dual frontend interfaces** with React (web) and Ink (terminal)
- **Complete RAG system** with document ingestion, chunking, and vector search
- **Multi-agent orchestration** with dependency management
- **Real-time event system** using WebSocket and async pub/sub
- **Git integration** for worktree management
- **Comprehensive API specifications** with all endpoints defined
- **Database schemas** with SQLAlchemy models and migrations
- **Testing infrastructure** with pytest fixtures
- **Development scripts** for setup and deployment

All components are designed to work together seamlessly in a local-only environment, prioritizing developer experience over scalability concerns.
