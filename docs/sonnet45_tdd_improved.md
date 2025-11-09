# Amelia: Technical Design Document (IMPROVED)
## Local LLM Workflow Orchestration Command Center

**Document Version:** 2.0 (Improved)
**Target Audience:** LLM Code Generation (Claude Code)
**Last Updated:** 2025-11-08
**Deployment Model:** Local-only, self-contained
**Improvement Status:** ✅ Integrated competitive agent review findings

---

## 🚨 CRITICAL IMPROVEMENTS NOTICE

This TDD has been enhanced with critical fixes and architectural improvements identified through competitive agent review. Key changes include:

- **Event Bus**: Fixed memory leaks, added queue limits, circuit breakers
- **Database**: Fixed connection pool exhaustion, added retry logic
- **Workflows**: Added state locking, checkpointing, timeout enforcement
- **Claude Code**: Complete implementation with process management
- **Vector Index**: Optimized configuration, added caching
- **Observability**: Added metrics, distributed tracing, health checks
- **Resilience**: Circuit breakers, rate limiting, graceful shutdown
- **Testing**: Comprehensive test coverage for async operations

See **Section 22: Critical Fixes & Improvements** for complete implementation details.

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
22. **[Critical Fixes & Improvements](#22-critical-fixes--improvements)** ⭐ NEW
23. **[Observability & Monitoring](#23-observability--monitoring)** ⭐ NEW
24. **[Resilience Patterns](#24-resilience-patterns)** ⭐ NEW
25. **[Implementation Roadmap](#25-implementation-roadmap)** ⭐ NEW

---

## 1. Executive Summary

### 1.1 Purpose

Amelia is a local-first developer tool that orchestrates LLM agents (primarily Claude) for software development lifecycle tasks. It provides both a web UI and terminal UI for managing agents, workflows, RAG document management, and chat interactions with LLMs.

**Key Improvement**: This version includes production-ready error handling, resource management, and operational excellence patterns.

### 1.2 Key Characteristics

- **Local-only execution**: No cloud dependencies, all processing happens locally
- **Developer-centric**: Designed for engineers during active development
- **Multi-agent orchestration**: Uses LangGraph for complex workflow management with checkpointing
- **RAG-enabled**: Document ingestion and retrieval for context-aware agents
- **Dual interface**: Web UI and Terminal UI with shared backend
- **Production-ready**: Circuit breakers, observability, graceful degradation ⭐ NEW
- **Resilient**: State persistence, retry logic, timeout enforcement ⭐ NEW

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
│  │  │  /api/v1/agents  /api/v1/workflows         │  │  ⭐ NEW│
│  │  │  /api/v1/rag     /api/v1/chat              │  │        │
│  │  │  /api/v1/git     /api/v1/status            │  │        │
│  │  │  /health /metrics                          │  │  ⭐ NEW│
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
│  │  │  ┌──────────────────────────────────────┐ │  │  ⭐ NEW│
│  │  │  │  Resilience Layer                    │ │  │        │
│  │  │  │  Circuit Breakers | Rate Limiters    │ │  │        │
│  │  │  │  Resource Manager | Token Budgets    │ │  │        │
│  │  │  └──────────────────────────────────────┘ │  │        │
│  │  └────────────────┬───────────────────────────┘  │        │
│  │                   │                               │        │
│  │  ┌────────────────┴───────────────────────────┐  │        │
│  │  │      LangGraph Orchestration Layer         │  │        │
│  │  │  ┌─────────────────────────────────────┐   │  │        │
│  │  │  │   Workflow Graph Executor           │   │  │        │
│  │  │  │   State Management + Checkpointing  │   │  │  ⭐ NEW│
│  │  │  │   Agent Node Execution              │   │  │        │
│  │  │  │   Optimistic Locking | Versioning   │   │  │  ⭐ NEW│
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
│  │  │   +Monitor  │  │  +Circuit Brake │ │              ⭐ NEW│
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
│  │  │          │  │ +HNSW idx│  │ +version │  │+checkpts│ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  │  ⭐ Optimized indexes | Connection pooling | Health     │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Key Architectural Improvements ⭐ NEW

#### Resilience Layer
- **Circuit Breakers**: Protect against cascading failures (LLM APIs, DB, external services)
- **Rate Limiting**: Token budgets and request rate controls
- **Resource Manager**: Limits on concurrent operations, memory, CPU
- **Graceful Degradation**: Fallback strategies and partial functionality

#### State Management
- **Optimistic Locking**: Version-based concurrency control
- **Checkpointing**: LangGraph PostgreSQL checkpointer for workflow resume
- **State Persistence**: Incremental state saves, not just on completion

#### Observability
- **Distributed Tracing**: Correlation IDs through all async operations
- **Metrics Collection**: Prometheus instrumentation
- **Health Checks**: Dependency monitoring with degradation detection
- **Structured Logging**: Request context preservation

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
tiktoken = "^0.8.0"  # ⭐ NEW - Token-aware chunking

# HTTP & Web
httpx = "^0.28.1"
websockets = "^15.0.1"

# Utilities
pydantic = "^2.12.4"
python-dotenv = "^1.2.1"
rich = "^14.2.0"  # Terminal formatting and logging
structlog = "^24.4.0"  # Structured logging

# Resilience & Monitoring ⭐ NEW
tenacity = "^9.0.0"  # Retry logic
circuitbreaker = "^2.0.0"  # Circuit breaker pattern
prometheus-client = "^0.21.0"  # Metrics
prometheus-fastapi-instrumentator = "^7.0.0"
slowapi = "^0.1.9"  # Rate limiting
psutil = "^6.1.0"  # Resource monitoring
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
    "postcss": "^8.5.6",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.6.3",
    "vitest": "^2.1.0"
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

[Previous structure remains the same, with additions noted below]

```
amelia/
├── backend/
│   ├── core/
│   │   ├── resilience/         # ⭐ NEW
│   │   │   ├── __init__.py
│   │   │   ├── circuit_breaker.py
│   │   │   ├── rate_limiter.py
│   │   │   ├── resource_manager.py
│   │   │   └── token_budget.py
│   │   │
│   │   ├── monitoring/         # ⭐ NEW
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py
│   │   │   ├── health.py
│   │   │   └── tracing.py
│   │   │
│   │   └── [existing core modules...]
│   │
│   └── [rest of backend structure...]
│
└── [rest of project structure...]
```

---

## 5. Backend Implementation

[Sections 5.1-5.2 remain largely the same with critical fixes integrated]

### 5.3 Event System (IMPROVED) ⭐

#### 5.3.1 Event Bus with Resilience (`core/events/bus.py`)

```python
"""
Asynchronous event bus for inter-component communication.
Implements publish-subscribe pattern with:
- Bounded queue (prevents memory leaks)
- Subscriber timeouts (prevents blocking)
- Circuit breakers (isolates failing subscribers)
- Graceful shutdown (drains queue properly)
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
import time
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    correlation_id: Optional[str] = None  # ⭐ NEW


@dataclass
class SubscriberHealth:
    """Track subscriber health for circuit breaker"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    circuit_open: bool = False


class EventBus:
    """
    Asynchronous event bus with resilience patterns.

    Improvements:
    - Bounded queue prevents OOM
    - Subscriber timeouts prevent blocking
    - Circuit breakers isolate failures
    - Graceful shutdown drains queue
    """

    def __init__(
        self,
        max_queue_size: int = 10000,
        subscriber_timeout: float = 5.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60
    ):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)  # ⭐ BOUNDED
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # ⭐ NEW: Circuit breaker support
        self._subscriber_timeout = subscriber_timeout
        self._subscriber_health: Dict[int, SubscriberHealth] = {}
        self._circuit_threshold = circuit_breaker_threshold
        self._circuit_timeout = circuit_breaker_timeout

        # ⭐ NEW: Metrics
        self._events_published = 0
        self._events_processed = 0
        self._events_dropped = 0

    async def start(self):
        """Start the event bus processor"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("Event bus started", max_queue_size=self._queue.maxsize)

    async def stop(self):
        """
        Stop the event bus processor gracefully.
        ⭐ IMPROVED: Drains remaining events before stopping.
        """
        if not self._running:
            return

        self._running = False

        # ⭐ Drain remaining events
        logger.info("Draining event queue", remaining=self._queue.qsize())
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                await self._dispatch_event(event)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error("Error draining event", error=str(e))

        # Cancel task
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(
            "Event bus stopped",
            published=self._events_published,
            processed=self._events_processed,
            dropped=self._events_dropped
        )

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}", callback=callback.__name__)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event: Event):
        """
        Publish an event to the bus.
        ⭐ IMPROVED: Handles backpressure with timeout.
        """
        try:
            # ⭐ Timeout prevents indefinite blocking
            await asyncio.wait_for(
                self._queue.put(event),
                timeout=5.0
            )
            self._events_published += 1
            logger.debug(f"Published event: {event.type}", correlation_id=event.correlation_id)
        except asyncio.TimeoutError:
            self._events_dropped += 1
            logger.error(
                "Event queue full, dropping event",
                event_type=event.type,
                queue_size=self._queue.qsize()
            )
            raise EventBusOverloadError("Event queue is full")

    async def _process_events(self):
        """
        Background task to process events from queue.
        ⭐ IMPROVED: Better timeout handling, no busy loop.
        """
        while self._running:
            try:
                # ⭐ Longer timeout, no busy loop
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )

                await self._dispatch_event(event)
                self._events_processed += 1

            except asyncio.TimeoutError:
                continue  # Check _running flag
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _dispatch_event(self, event: Event):
        """Dispatch event to subscribers with resilience"""
        subscribers = self._subscribers.get(event.type, [])

        for callback in subscribers:
            subscriber_id = id(callback)

            # ⭐ Check circuit breaker
            if self._is_circuit_open(subscriber_id):
                logger.warning(
                    f"Circuit breaker open for subscriber",
                    callback=callback.__name__,
                    event_type=event.type
                )
                continue

            try:
                # ⭐ Timeout enforcement
                await asyncio.wait_for(
                    self._invoke_callback(callback, event),
                    timeout=self._subscriber_timeout
                )
                self._record_success(subscriber_id)

            except asyncio.TimeoutError:
                logger.error(
                    f"Subscriber timeout",
                    callback=callback.__name__,
                    event_type=event.type,
                    timeout=self._subscriber_timeout
                )
                self._record_failure(subscriber_id)

            except Exception as e:
                logger.error(
                    f"Subscriber error",
                    callback=callback.__name__,
                    error=str(e),
                    event_type=event.type
                )
                self._record_failure(subscriber_id)

    async def _invoke_callback(self, callback: Callable, event: Event):
        """Invoke callback (sync or async)"""
        if asyncio.iscoroutinefunction(callback):
            await callback(event)
        else:
            callback(event)

    def _is_circuit_open(self, subscriber_id: int) -> bool:
        """Check if circuit breaker is open for subscriber"""
        health = self._subscriber_health.get(subscriber_id)
        if not health or not health.circuit_open:
            return False

        # Check if circuit should be half-open
        if health.last_failure_time:
            elapsed = (datetime.utcnow() - health.last_failure_time).total_seconds()
            if elapsed > self._circuit_timeout:
                health.circuit_open = False
                health.failures = 0
                logger.info(f"Circuit breaker half-open", subscriber_id=subscriber_id)
                return False

        return True

    def _record_success(self, subscriber_id: int):
        """Record successful callback invocation"""
        if subscriber_id not in self._subscriber_health:
            return

        health = self._subscriber_health[subscriber_id]
        health.successes += 1

        # Reset circuit if enough successes
        if health.circuit_open and health.successes >= 2:
            health.circuit_open = False
            health.failures = 0
            logger.info(f"Circuit breaker closed", subscriber_id=subscriber_id)

    def _record_failure(self, subscriber_id: int):
        """Record failed callback invocation"""
        if subscriber_id not in self._subscriber_health:
            self._subscriber_health[subscriber_id] = SubscriberHealth()

        health = self._subscriber_health[subscriber_id]
        health.failures += 1
        health.last_failure_time = datetime.utcnow()
        health.successes = 0  # Reset success count

        # Open circuit if threshold exceeded
        if health.failures >= self._circuit_threshold:
            health.circuit_open = True
            logger.error(
                f"Circuit breaker opened",
                subscriber_id=subscriber_id,
                failures=health.failures
            )


class EventBusOverloadError(Exception):
    """Raised when event bus queue is full"""
    pass


# Global event bus instance (singleton pattern)
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
```

---

## 22. Critical Fixes & Improvements ⭐ NEW

This section contains all critical fixes identified by competitive agent review.

### 22.1 Database Connection Management (CRITICAL FIX)

**Problem**: Connection pool exhaustion, no retry logic, auto-commit on reads.

**Solution** (`database/connection.py`):

```python
"""
Database connection management with resilience.

Improvements:
- Proper connection pooling (no NullPool)
- Connection health checks (pre_ping)
- Retry logic with exponential backoff
- Explicit transaction control
- Connection recycling
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
import asyncpg
import asyncio
from backend.config import settings
from backend.models.database.base import Base
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# ⭐ IMPROVED: Always use proper pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    poolclass=QueuePool,  # ⭐ Never use NullPool
    pool_timeout=30.0,    # ⭐ Add timeout
    pool_recycle=3600,    # ⭐ Recycle connections hourly
    pool_pre_ping=True,   # ⭐ Validate connections before use
    connect_args={
        "timeout": 10,
        "command_timeout": 60,
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """
    Initialize database, create tables.
    ⭐ IMPORTANT: Do NOT use create_all() in production!
    Use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # ⭐ Only for development/testing
        if settings.DEBUG:
            await conn.run_sync(Base.metadata.create_all)
            logger.warning("Using create_all() - not recommended for production")
        else:
            logger.info("Skipping create_all() - use Alembic migrations in production")

    logger.info("Database initialized successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI routes to get database session.

    ⭐ IMPROVED:
    - Retry logic for connection failures
    - No auto-commit (explicit transaction control)
    - Proper cleanup

    Usage: db: AsyncSession = Depends(get_db)
    """
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            async with AsyncSessionLocal() as session:
                yield session
                # ⭐ No auto-commit - routes control transactions
                return
        except asyncpg.PostgresConnectionError as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Database connection failed after {max_retries} retries", error=str(e))
                raise DatabaseConnectionError(f"Failed to connect after {max_retries} attempts")

            # ⭐ Exponential backoff
            wait_time = 2 ** retry_count
            logger.warning(f"Database connection failed, retrying in {wait_time}s", attempt=retry_count)
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error("Database session error", error=str(e))
            raise


async def check_db_health() -> bool:
    """
    Check database health.
    ⭐ NEW: Used by health check endpoint.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


class DatabaseConnectionError(Exception):
    """Raised when database connection fails after retries"""
    pass
```

### 22.2 Workflow State Management (CRITICAL FIX)

**Problem**: Race conditions, no state locking, no checkpointing, fire-and-forget tasks.

**Solution** (`core/workflows/manager.py` - Updated):

```python
"""
Workflow execution and management with resilience.

Improvements:
- Optimistic locking with version field
- LangGraph checkpointing for resume capability
- Task tracking (no fire-and-forget)
- Timeout enforcement
- Retry logic
"""
from typing import Dict, Any, Optional, UUID as UUIDType
from uuid import UUID
from datetime import datetime
import asyncio
from sqlalchemy import update, select
from langgraph.checkpoint.postgres import PostgresSaver

from backend.core.workflows.graph import WorkflowGraphBuilder
from backend.core.workflows.state import WorkflowState, WorkflowStatus, AgentNodeState
from backend.models.database.workflow import Workflow
from backend.database.session import get_db
from backend.core.events.bus import get_event_bus, Event, EventType
from backend.utils.logger import setup_logger
from backend.config import settings

logger = setup_logger(__name__)


class WorkflowManager:
    """
    Manages workflow lifecycle with resilience patterns.

    ⭐ Key improvements:
    - Optimistic locking prevents race conditions
    - Checkpointing enables resume after crashes
    - Task tracking prevents resource leaks
    - Timeout enforcement prevents runaway workflows
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self.active_workflows: Dict[str, asyncio.Task] = {}  # ⭐ Track tasks!
        self._workflow_locks: Dict[str, asyncio.Lock] = {}

        # ⭐ LangGraph checkpointer for persistence
        self.checkpointer = PostgresSaver(connection_string=str(settings.DATABASE_URL))

    async def create_workflow(
        self,
        name: str,
        description: str,
        graph_definition: Dict[str, Any]
    ) -> Workflow:
        """Create a new workflow from definition"""
        async with get_db() as db:
            workflow = Workflow(
                name=name,
                description=description,
                graph_definition=graph_definition,
                status=WorkflowStatus.IDLE,
                state={},
                version=0,  # ⭐ Optimistic locking
                max_runtime_seconds=3600,  # ⭐ Default timeout
                retry_count=0,
                max_retries=3
            )

            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)

            logger.info(f"Created workflow: {workflow.id}")
            return workflow

    def _get_workflow_lock(self, workflow_id: UUIDType) -> asyncio.Lock:
        """Get or create lock for workflow"""
        wf_id_str = str(workflow_id)
        if wf_id_str not in self._workflow_locks:
            self._workflow_locks[wf_id_str] = asyncio.Lock()
        return self._workflow_locks[wf_id_str]

    async def start_workflow(
        self,
        workflow_id: UUID,
        initial_input: Dict[str, Any]
    ) -> WorkflowState:
        """
        Start workflow execution with locking and checkpointing.
        ⭐ IMPROVED: Prevents concurrent execution, tracks tasks.
        """
        # ⭐ Acquire lock to prevent concurrent starts
        lock = self._get_workflow_lock(workflow_id)
        async with lock:
            async with get_db() as db:
                workflow = await db.get(Workflow, workflow_id)
                if not workflow:
                    raise ValueError(f"Workflow {workflow_id} not found")

                if workflow.status == WorkflowStatus.RUNNING:
                    raise ValueError(f"Workflow {workflow_id} is already running")

                # Initialize state
                state = self._initialize_state(workflow, initial_input)

                # ⭐ Update with optimistic locking
                workflow.status = WorkflowStatus.RUNNING
                workflow.state = state
                workflow.started_at = datetime.utcnow()
                workflow.version += 1
                await db.commit()

                expected_version = workflow.version

        # Publish event
        await self.event_bus.publish(Event(
            type=EventType.WORKFLOW_STARTED,
            data={
                "workflow_id": str(workflow_id),
                "workflow_name": workflow.name
            }
        ))

        # Build graph with checkpointing
        graph = await self._build_graph(workflow)

        # ⭐ Create TRACKED background task
        task = asyncio.create_task(
            self._execute_workflow_safe(workflow_id, graph, state, expected_version)
        )
        self.active_workflows[str(workflow_id)] = task

        logger.info(
            "Started workflow",
            workflow_id=str(workflow_id),
            version=expected_version
        )

        return state

    async def _execute_workflow_safe(
        self,
        workflow_id: UUID,
        graph: Any,
        state: WorkflowState,
        expected_version: int
    ):
        """
        Execute workflow with timeout, retry, and error handling.
        ⭐ IMPROVED: Proper async patterns, resource cleanup.
        """
        try:
            # ⭐ Get workflow config for timeout
            async with get_db() as db:
                workflow = await db.get(Workflow, workflow_id)
                max_runtime = workflow.max_runtime_seconds

            # ⭐ Execute with timeout
            final_state = await asyncio.wait_for(
                graph.ainvoke(
                    state,
                    config={
                        "configurable": {"thread_id": str(workflow_id)},
                        "checkpointer": self.checkpointer  # ⭐ Enable checkpointing
                    }
                ),
                timeout=max_runtime
            )

            # ⭐ Update with optimistic locking
            async with get_db() as db:
                stmt = (
                    update(Workflow)
                    .where(
                        Workflow.id == workflow_id,
                        Workflow.version == expected_version
                    )
                    .values(
                        status=WorkflowStatus.COMPLETED,
                        state=final_state,
                        completed_at=datetime.utcnow(),
                        progress=1.0,
                        version=expected_version + 1
                    )
                )
                result = await db.execute(stmt)
                if result.rowcount == 0:
                    raise ConcurrentModificationError(
                        f"Workflow {workflow_id} was modified concurrently"
                    )
                await db.commit()

            # Publish completion event
            await self.event_bus.publish(Event(
                type=EventType.WORKFLOW_COMPLETED,
                data={
                    "workflow_id": str(workflow_id),
                    "final_state": final_state
                }
            ))

            logger.info("Workflow completed", workflow_id=str(workflow_id))

        except asyncio.TimeoutError:
            logger.error(f"Workflow {workflow_id} timeout after {max_runtime}s")
            await self._mark_workflow_failed(
                workflow_id,
                f"Timeout after {max_runtime}s",
                expected_version
            )

        except ConcurrentModificationError as e:
            logger.error(f"Workflow {workflow_id} concurrent modification", error=str(e))
            # Don't update status - another process won the race

        except Exception as e:
            logger.exception(f"Workflow {workflow_id} failed", error=str(e))
            await self._handle_workflow_failure(workflow_id, e, expected_version)

        finally:
            # ⭐ Clean up task tracking
            self.active_workflows.pop(str(workflow_id), None)

            # ⭐ Release lock
            lock = self._get_workflow_lock(workflow_id)
            if lock.locked():
                lock.release()

    async def _mark_workflow_failed(
        self,
        workflow_id: UUID,
        error_message: str,
        expected_version: int
    ):
        """Mark workflow as failed with optimistic locking"""
        async with get_db() as db:
            stmt = (
                update(Workflow)
                .where(
                    Workflow.id == workflow_id,
                    Workflow.version == expected_version
                )
                .values(
                    status=WorkflowStatus.FAILED,
                    error_message=error_message,
                    completed_at=datetime.utcnow(),
                    version=expected_version + 1
                )
            )
            await db.execute(stmt)
            await db.commit()

        await self.event_bus.publish(Event(
            type=EventType.WORKFLOW_FAILED,
            data={
                "workflow_id": str(workflow_id),
                "error": error_message
            }
        ))

    async def _handle_workflow_failure(
        self,
        workflow_id: UUID,
        error: Exception,
        expected_version: int
    ):
        """Handle workflow failure with retry logic"""
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)

            # ⭐ Check if should retry
            if workflow.retry_count < workflow.max_retries:
                workflow.retry_count += 1
                workflow.status = WorkflowStatus.IDLE
                workflow.version += 1
                await db.commit()

                logger.warning(
                    f"Workflow {workflow_id} will retry",
                    attempt=workflow.retry_count,
                    max_retries=workflow.max_retries
                )

                # ⭐ Schedule retry with exponential backoff
                wait_time = 2 ** workflow.retry_count
                await asyncio.sleep(wait_time)

                # Retry workflow
                await self.start_workflow(workflow_id, workflow.state.get("shared_context", {}))
            else:
                # ⭐ Max retries exceeded
                await self._mark_workflow_failed(
                    workflow_id,
                    f"Failed after {workflow.max_retries} retries: {str(error)}",
                    expected_version
                )

    async def resume_workflow(self, workflow_id: UUID):
        """
        Resume a paused or failed workflow from checkpoint.
        ⭐ NEW: Checkpoint-based resume capability.
        """
        async with get_db() as db:
            workflow = await db.get(Workflow, workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            if workflow.status not in [WorkflowStatus.PAUSED, WorkflowStatus.FAILED]:
                raise ValueError(f"Cannot resume workflow in status: {workflow.status}")

        # Build graph
        graph = await self._build_graph(workflow)

        # ⭐ Resume from checkpoint
        config = {
            "configurable": {"thread_id": str(workflow_id)},
            "checkpointer": self.checkpointer
        }

        # The state will be loaded from checkpoint automatically
        final_state = await graph.ainvoke(None, config=config)

        logger.info("Workflow resumed from checkpoint", workflow_id=str(workflow_id))
        return final_state

    [... rest of methods remain similar ...]


class ConcurrentModificationError(Exception):
    """Raised when optimistic locking detects concurrent modification"""
    pass
```

### 22.3 Claude Code Process Management (CRITICAL IMPLEMENTATION)

**Problem**: Core LLM integration was placeholder code. Process management missing.

**Solution** (`core/agents/claude_code.py` - NEW):

```python
"""
Claude Code subprocess integration with resource management.

This module provides safe, monitored execution of Claude Code agents
with proper process lifecycle management, resource limits, and timeout
enforcement.
"""
import asyncio
import psutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, List
from dataclasses import dataclass
from datetime import datetime

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ClaudeCodeResult:
    """Result from Claude Code execution"""
    output: str
    exit_code: int
    duration_seconds: float
    resource_usage: Dict[str, Any]
    error: Optional[str] = None


class ClaudeCodeProcess:
    """
    Managed Claude Code subprocess with resource limits and monitoring.

    Features:
    - Process timeout enforcement
    - Memory and CPU monitoring
    - Resource limits
    - Proper cleanup
    - Output streaming
    """

    def __init__(
        self,
        working_dir: Path,
        timeout_seconds: int = 300,
        memory_limit_mb: int = 4096,
        cpu_limit_percent: int = 80
    ):
        self.working_dir = working_dir
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self.process: Optional[asyncio.subprocess.Process] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None

    async def execute(
        self,
        prompt: str,
        context_files: List[Path] = None,
        stream: bool = True
    ) -> ClaudeCodeResult:
        """
        Execute Claude Code with resource monitoring.

        Args:
            prompt: The prompt to send to Claude Code
            context_files: Optional files to include as context
            stream: Whether to stream output (for logging)

        Returns:
            ClaudeCodeResult with output and metadata
        """
        self._start_time = datetime.utcnow()

        # Build command
        cmd = self._build_command(context_files)

        logger.info(
            "Starting Claude Code process",
            working_dir=str(self.working_dir),
            timeout=self.timeout_seconds
        )

        try:
            # Create process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=self._build_env(),
                limit=1024 * 1024  # 1MB buffer
            )

            # Start resource monitoring
            self._monitor_task = asyncio.create_task(self._monitor_resources())

            # Send prompt
            self.process.stdin.write(prompt.encode('utf-8'))
            await self.process.stdin.drain()
            self.process.stdin.close()

            # Collect output
            output_lines = []
            async for line in self._read_output_with_timeout():
                output_lines.append(line)
                if stream:
                    logger.debug("Claude Code output", line=line)

            # Wait for completion with timeout
            await asyncio.wait_for(
                self.process.wait(),
                timeout=self.timeout_seconds
            )

            # Get resource usage
            duration = (datetime.utcnow() - self._start_time).total_seconds()
            resource_usage = await self._get_resource_usage()

            # Check exit code
            if self.process.returncode != 0:
                stderr = await self.process.stderr.read()
                error_msg = stderr.decode('utf-8', errors='replace')
                logger.error(
                    "Claude Code failed",
                    exit_code=self.process.returncode,
                    error=error_msg
                )
                raise ProcessExecutionError(
                    f"Claude Code exited with code {self.process.returncode}: {error_msg}"
                )

            return ClaudeCodeResult(
                output='\n'.join(output_lines),
                exit_code=self.process.returncode,
                duration_seconds=duration,
                resource_usage=resource_usage
            )

        except asyncio.TimeoutError:
            logger.error(f"Claude Code timeout after {self.timeout_seconds}s")
            await self.terminate()
            raise TimeoutError(f"Process exceeded {self.timeout_seconds}s timeout")

        except Exception as e:
            logger.exception("Claude Code execution failed", error=str(e))
            await self.terminate()
            raise

        finally:
            # Clean up monitoring
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

    def _build_command(self, context_files: List[Path] = None) -> List[str]:
        """Build Claude Code command with arguments"""
        cmd = [
            settings.CLAUDE_CODE_PATH,
            "--no-cache",
            "--output-format", "json"
        ]

        # Add context files
        for file in (context_files or []):
            if not file.exists():
                logger.warning(f"Context file not found: {file}")
                continue
            cmd.extend(["--file", str(file)])

        return cmd

    def _build_env(self) -> Dict[str, str]:
        """Build environment variables for subprocess"""
        import os
        env = os.environ.copy()

        # Add API key if configured
        if settings.ANTHROPIC_API_KEY:
            env["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

        return env

    async def _read_output_with_timeout(self) -> AsyncIterator[str]:
        """Stream output from process with timeout"""
        if not self.process or not self.process.stdout:
            return

        while True:
            try:
                # Read with timeout to allow monitoring
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=5.0
                )

                if not line:
                    break

                yield line.decode('utf-8', errors='replace').strip()

            except asyncio.TimeoutError:
                # Check if process is still alive
                if self.process.returncode is not None:
                    break
                continue

    async def _monitor_resources(self):
        """
        Monitor and enforce resource limits.
        Terminates process if limits are exceeded.
        """
        if not self.process:
            return

        try:
            # Get psutil Process object
            proc = psutil.Process(self.process.pid)

            while True:
                await asyncio.sleep(1.0)

                try:
                    # Check memory
                    mem_mb = proc.memory_info().rss / 1024 / 1024
                    if mem_mb > self.memory_limit_mb:
                        logger.error(
                            "Process exceeded memory limit",
                            pid=proc.pid,
                            memory_mb=round(mem_mb, 2),
                            limit_mb=self.memory_limit_mb
                        )
                        await self.terminate()
                        return

                    # Check CPU (averaged over 1 second)
                    cpu_percent = proc.cpu_percent(interval=1.0)
                    if cpu_percent > self.cpu_limit_percent:
                        logger.warning(
                            "Process high CPU usage",
                            pid=proc.pid,
                            cpu_percent=round(cpu_percent, 2),
                            limit_percent=self.cpu_limit_percent
                        )

                except psutil.NoSuchProcess:
                    # Process terminated
                    return

        except asyncio.CancelledError:
            # Monitoring cancelled, normal shutdown
            pass

    async def _get_resource_usage(self) -> Dict[str, Any]:
        """Get final resource usage statistics"""
        if not self.process:
            return {}

        try:
            proc = psutil.Process(self.process.pid)
            return {
                "memory_peak_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": round(proc.cpu_percent(), 2),
                "num_threads": proc.num_threads()
            }
        except psutil.NoSuchProcess:
            return {}

    async def terminate(self):
        """Gracefully terminate the process"""
        if not self.process:
            return

        try:
            logger.warning(f"Terminating Claude Code process {self.process.pid}")

            # Try graceful termination first
            self.process.terminate()

            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if termination didn't work
                logger.warning(f"Force killing Claude Code process {self.process.pid}")
                self.process.kill()
                await self.process.wait()

        except ProcessLookupError:
            # Process already dead
            pass


class ProcessExecutionError(Exception):
    """Raised when Claude Code process fails"""
    pass
```

[Continue in next message due to length...]