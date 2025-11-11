# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amelia is a local-first RAG (Retrieval-Augmented Generation) MCP server that enables semantic search over local documentation, web content, and audio files. The project is currently in **Phase 0: Planning Complete** with no source code yet written.

**Status:** Ready to build following the phased implementation approach outlined in the TDD.

## Technology Stack

### Core Technologies
- **MCP Server:** FastMCP v2 (Model Context Protocol)
- **Database:** PostgreSQL 17+ with pgvector extension
- **Embeddings:** Snowflake Arctic Embed L (1024 dims) - **FIXED, not configurable**
- **Python:** 3.12+
- **Audio:** Whisper Turbo (via Docling ASR) + FFmpeg
- **Web Crawling:** Crawl4AI + Playwright

### Key Dependencies
```
fastmcp==2.13.0.2
psycopg[binary]==3.2.1
pgvector==0.2.5
sentence-transformers==4.1.0
crawl4ai==0.7.6
playwright==1.48.0
docling[vlm]>=2.61.2
```

## Architecture Constraints

### Immutable Decisions

**Embedding Model:**
- Model is FIXED to `snowflake-arctic-embed-l-v2.0` (1024 dimensions)
- Embeddings table enforces `vector(1024)` constraint in PostgreSQL
- Do NOT create configuration for switching embedding models
- Any model change requires full database migration (out of scope for v1.0)

**Database Schema:**
- The canonical source of truth is `init.sql` in the repository root
- Always reference `init.sql` when implementing database operations
- Schema includes: documents, chunks, embeddings, bm25_index, crawl_queue, crawled_urls, jobs

**Multi-Language BM25:**
- Language detection is CRITICAL for search quality
- Whisper detects language during transcription
- Language MUST be stored in `chunks.metadata->>'language'` field
- BM25 trigger uses this language field for correct stemming (e.g., 'spanish', 'english')
- Failure to propagate language breaks non-English search

## Development Commands

### Database Setup

```bash
# Start PostgreSQL with pgvector (Docker)
docker run -d \
  --name amelia-postgres \
  -e POSTGRES_DB=amelia \
  -e POSTGRES_USER=amelia \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  ankane/pgvector:latest

# Initialize database schema
psql amelia < init.sql

# Or via wrapper script (when implemented)
python -m amelia.migrate
```

### Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Verify FFmpeg (required for audio)
ffmpeg -version
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=amelia

# Run specific test file
pytest tests/test_chunking.py -v

# Run integration tests
pytest tests/test_pipeline.py -v
```

### Running the MCP Server

```bash
# Start server (stdio mode for Claude Code)
python -m amelia

# Environment variables in .env:
# - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
# - EMBEDDING_DEVICE (cpu or cuda)
# - WEB_CRAWL_MAX_DEPTH, WEB_CRAWL_BATCH_SIZE, etc.
```

## Code Architecture

### Project Structure

```
amelia/
├── amelia/
│   ├── __main__.py          # Entry point
│   ├── server.py            # MCP server
│   ├── config.py            # Config management
│   ├── models.py            # Data models
│   ├── database.py          # DB connection & queries
│   ├── ingestion/           # Document processing
│   │   ├── parsers.py
│   │   ├── chunking.py
│   │   └── pipeline.py
│   ├── audio/               # Audio transcription
│   │   ├── transcriber.py   # Whisper integration
│   │   ├── metadata.py
│   │   └── chunker.py
│   ├── crawler/             # Web crawling
│   │   ├── web_crawler.py
│   │   ├── url_detector.py
│   │   └── deduplicator.py
│   ├── embeddings/
│   │   ├── generator.py     # Always uses snowflake-arctic-embed-l-v2.0
│   │   └── cache.py
│   ├── search/
│   │   ├── vector.py
│   │   ├── bm25.py
│   │   ├── hybrid.py
│   │   └── strategies.py
│   └── tools/               # MCP tools
│       ├── ingest.py
│       ├── crawl.py
│       └── search.py
├── tests/
├── init.sql                 # CANONICAL database schema
├── requirements.txt
└── docs/
    ├── prd.md              # Product requirements
    └── tdd.md              # Technical design (comprehensive reference)
```

### Key Components

**Job Coordinator:**
- Manages long-running operations (ingest, crawl, transcribe)
- Handles retry logic with exponential backoff
- Persists state to `jobs` table for crash recovery
- Implements backpressure (max concurrent jobs by type)

**Document Versioning:**
- Uses SHA256 content hashing for change detection
- Increments version on content changes
- Skips re-embedding if content unchanged
- Critical for efficient incremental updates

**Web Crawler:**
- Worker pool with per-domain rate limiting
- Retry with exponential backoff (query-based, no in-memory state)
- Circuit breaker via SQL queries (skip domains with >= 10 recent failures)
- Deduplication via `crawled_urls` table

**Audio Pipeline:**
- Whisper ASR via Docling for transcription
- FFmpeg for format validation and metadata
- Language detection flows to `chunks.metadata->>'language'`
- Timestamp-aware chunking preserves temporal markers

## Implementation Guidelines

### When Writing Code

**Database Operations:**
- Always check `init.sql` for canonical schema
- Use parameterized queries (prevent SQL injection)
- Leverage CASCADE deletes (defined in schema)
- Respect UNIQUE constraints (source_path + collection, source_url + collection)

**Chunking Strategy:**
1. Hierarchical markdown (respect headers: #, ##, ###)
2. Timestamp-aware for audio transcripts
3. Fixed-size with overlap (fallback)
4. Max chunk size: 1000 chars, overlap: 200 chars

**Embedding Generation:**
- Model is hardcoded to `snowflake-arctic-embed-l-v2.0`
- Batch size configurable via `EMBEDDING_BATCH_SIZE` (default: 32)
- GPU support via `EMBEDDING_DEVICE=cuda`
- Cache embeddings for unchanged chunks

**Error Handling:**
- Use structured logging (JSON format with trace IDs)
- Persist failures to `jobs` table with `error_message`
- Implement retry logic for transient failures
- Circuit breakers for repeated failures

### Code Patterns

**Content Hash Computation:**
```python
import hashlib

def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash for change detection."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

**Language Propagation (Audio):**
```python
# CRITICAL: Store language in metadata for BM25 trigger
metadata = {
    'language': pg_language,  # e.g., 'spanish', 'english'
    'source_language_code': detected_language  # ISO code
}
# BM25 trigger reads metadata->>'language' for stemming
```

**Incremental Updates:**
```python
# Check if document exists and content changed
existing = await db.fetchone(
    "SELECT content_hash, version FROM documents WHERE source_path = %s",
    (path,)
)
if existing and existing['content_hash'] == new_hash:
    # Skip re-embedding
    return {"action": "skipped", "reason": "content_unchanged"}
else:
    # Increment version and re-embed
    await update_document_version(...)
```

## Testing Strategy

### Phase Gates (From TDD)

**Phase 1 → Phase 2 Gate:**
- Contract tests for MCP tools with recorded fixtures
- Database bootstrap via `docker-compose up` + smoke test
- P95 vector search < 500ms on 10K-chunk corpus
- Structured JSON logs with trace IDs

**Phase 2 → Phase 3 Gate:**
- Retrieval eval harness showing ≥20% NDCG lift
- Hybrid + re-ranker paths covered by integration tests
- Benchmark report on chunking quality vs runtime
- Embedding latency alerting hooks

**Phase 3 → Phase 4 Gate:**
- End-to-end soak tests (>3 hour workload)
- Chaos tests for backpressure and retry policies
- Data retention policy documentation
- Telemetry dashboards (crawl throughput, queue depth, failures)

### Test Coverage Requirements

- **Unit tests:** >85% coverage
- **Integration tests:** All MCP tools
- **E2E tests:** Full ingestion → search workflow
- **Performance tests:** Latency benchmarks on sample corpus

## Common Patterns

### MCP Tool Implementation

All tools follow this pattern:
1. Validate input parameters
2. Create job record in `jobs` table
3. Execute operation (with progress updates)
4. Handle errors with retry logic
5. Return structured result

### Async Operations

Use asyncio for:
- Database operations (via asyncpg)
- Web crawling (parallel batching)
- Embedding generation (batched)
- MCP tool invocations

### Configuration

Environment variables via `.env`:
- Database connection (POSTGRES_*)
- Embedding runtime (EMBEDDING_DEVICE)
- Crawl settings (WEB_CRAWL_*)
- Audio settings (AUDIO_WHISPER_MODEL, AUDIO_LANGUAGE)

## Important References

- **Canonical Schema:** `init.sql` (root directory)
- **Technical Design:** `docs/tdd.md` (comprehensive system design)
- **Product Requirements:** `docs/prd.md` (user stories and features)
- **Roadmap:** See TDD Phase 1-4 with gates

## Security & Privacy

**Local-First Principles:**
- Local files never leave machine
- Audio transcription processed locally (Whisper runs on-device)
- Web crawling fetches only public documentation
- Vector DB stored locally
- No telemetry or analytics

**Data Protection:**
- Never index folders with secrets (.env, credentials)
- Respect `.gitignore` patterns during ingestion
- Use exclude_patterns for sensitive web content
- Separate collections by sensitivity level

## Performance Targets

- **Vector search:** <100ms (P95)
- **Hybrid search:** <200ms (P95)
- **Document ingestion:** ~100 docs/min (markdown)
- **Audio transcription:** ~5-10x real-time
- **Web crawling:** ~20-40 pages/min
- **Idle RAM:** <200MB
- **Active RAM:** <800MB (indexing), <2GB (transcription)

## Common Gotchas

1. **Embedding model is immutable** - Don't create config to switch models
2. **Language metadata is critical** - Missing language breaks BM25 for non-English
3. **Content hashing enables incremental updates** - Always compute SHA256 hash
4. **HNSW index requires tuning** - Use m=16, ef_construction=64
5. **Retry logic is query-based** - No in-memory state for crawl retries
6. **FFmpeg is required** - Audio transcription fails without it
7. **Playwright browsers must be installed** - Run `playwright install chromium`
