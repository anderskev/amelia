# Amelia - Local RAG MCP Server

**Version:** 1.0 | **Last Updated:** 2025-11-10

This Technical Design Doc is my personal learning playbook for Amelia: a local MCP server that helps me explore RAG, LangChain/LangGraph, Crawl4AI, Whisper, and MCP tooling in one cohesive project. It is scoped for a single developer workflow (me), prioritizing rapid experimentation over production polish. For the problem statement and long-term vision, see `docs/prd.md`; for the motivation and future orchestration ideas, see `docs/blog_posts/0001_why_build_amelia.md`.

---

## What is Amelia?

Amelia is a local-first document search tool that:
- Indexes your local docs (PDFs, DOCX, TXT, MD, HTML)
- Transcribes and indexes audio files (MP3, WAV, M4A, FLAC)
- Crawls and indexes web documentation (URLs, sitemaps, llms.txt)
- Lets Claude Code search everything using natural language
- Uses advanced RAG strategies for accurate retrieval
- Runs entirely on your machine (privacy-friendly)

**Key Learning Areas:**
- MCP server integration (plug right into Claude Code)
- Advanced RAG: contextual embeddings, hybrid search, re-ranking
- Audio transcription via Whisper ASR (Automatic Speech Recognition)
- Web crawling via Crawl4AI with browser automation
- PostgreSQL + pgvector for vector storage
- Configurable strategies based on query type

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
│              (talks to Amelia via MCP)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ stdio (JSON-RPC)
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Amelia MCP Server                      │
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Job Coordinator                         │ │
│  │  - Manages job queues (ingest/crawl/transcribe)  │ │
│  │  - Handles retries & backpressure                │ │
│  │  - Tracks job status & failures                  │ │
│  └───────────────────┬───────────────────────────────┘ │
│                      │                                  │
│  ┌──────────────────┐│ ┌─────────────────────────────┐ │
│  │  Doc Processor   ││ │     Web Crawler             │ │
│  │  (local files)   ││ │  (Crawl4AI + Playwright)    │ │
│  └────────┬─────────┘│ │  - Worker pool management   │ │
│           │          │ │  - Per-domain rate limiting │ │
│  ┌────────▼─────────┐│ │  - Retry with backoff       │ │
│  │ Audio Processor  ││ └────────┬────────────────────┘ │
│  │ (Whisper+FFmpeg) ││          │                       │
│  └────────┬─────────┘│          │                       │
│           │          │          │                       │
│           └──────────┴──────────┘                       │
│                      │                                  │
│  ┌───────────────────▼───────────────────────────────┐ │
│  │         RAG Strategy Engine                       │ │
│  │  - Auto-select best strategy for query            │ │
│  │  - Combine results from multiple strategies       │ │
│  └────┬─────────────────────┬──────────────────────┘   │
│       │                     │                           │
│  ┌────▼───────┐  ┌─────────▼──────┐  ┌─────────────┐  │
│  │  Vector    │  │  Hybrid Search │  │  Re-ranker  │  │
│  │  Search    │  │ (Vector+BM25)  │  │ (Optional)  │  │
│  └────────────┘  └────────────────┘  └─────────────┘  │
│                                                          │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│          PostgreSQL + pgvector                           │
│  (stores documents, chunks, embeddings from all sources) │
└──────────────────────────────────────────────────────────┘
```

**Data Flow:**

*Ingestion (Local):*
```
Local Files → Parse → Compute SHA256 Hash → Check Content Hash →
If Changed: Chunk → Embed → Store (Increment Version) → Update last_modified
If Unchanged: Skip Re-embedding (Use Existing)
```

*Ingestion (Web):*
```
URL → Detect Type (sitemap/llms.txt/page) → Crawl4AI →
Extract Content → Compute SHA256 Hash → Check Content Hash →
If Changed: Chunk → Embed → Store (Increment Version) → Update crawled_at
If Unchanged: Skip Re-embedding (Use Existing)
```

*Ingestion (Audio):*
```
Audio File → FFmpeg (format check) → Whisper ASR (transcribe + detect language) →
Markdown + Timestamps + Language Code → Compute SHA256 Hash → Check Content Hash →
If Changed: Chunk → Store Language in chunks.metadata → Embed →
BM25 Trigger (uses language for correct tokenization) → Store (Increment Version) → Update last_modified
If Unchanged: Skip Re-embedding (Use Existing)
```

*Search:*
```
Query → Strategy Selection → Multi-strategy Retrieval →
Ranking → Format Results → Return to Claude
```

---

## Core Components

### 1. MCP Server Layer
**What it does:** Handles communication with Claude Code

**Key parts:**
- Protocol handler (JSON-RPC over stdio)
- Tool registry (exposes search/ingest tools)
- Request router
- Error handling

### 2. Job Coordinator

**Learning Objectives**
- Practice building asyncio-based job queues with persisted retry state.
- Capture job telemetry I can inspect manually (CLI or MCP status command) to understand backlogs.

**Minimum Build**
- Single queue manager covering ingest + crawl + transcription jobs backed by a PostgreSQL `jobs` table that stores `retry_count`, `next_run_at`, `backoff_delay`, and `status` fields.
- Background worker that enforces a simple exponential backoff (1s, 2s, 4s, 8s, 16s, 32s; max 3 attempts) and resurrects in-flight jobs on restart by scanning `status in ('running','scheduled')`.
- `amelia jobs status` (or equivalent MCP tool) that prints pending/running/failed jobs with timestamps so I can manually triage.

**Stretch Experiments**
- Configurable backpressure caps per job type (e.g., crawl=3, transcription=2, ingestion=5) and a chaos-test script that randomly fails Crawl4AI/Whisper runs to validate retries.
- Remote/worker-process prototype to offload heavy transcription jobs without redesigning the coordinator.
- Structured tracing that correlates job IDs with LangChain/LangSmith runs for easier debugging.


### 3. Document Processing Pipeline

**Learning Objectives**
- Explore how parsing, hashing, and chunking feed a pgvector/BM25-backed RAG system.
- Practice incremental updates so local docs can be re-indexed quickly while I iterate.

**Minimum Build**
- Parsers for MD/TXT/PDF (plus lightweight HTML) that normalize text and metadata into the `documents` table.
- SHA256 content hash + version manager that decides whether to skip, update, or recreate chunks; store `content_hash`, `version`, `last_modified`.
- Hierarchical chunker (H1→H3 headers, then 1000-char chunks w/200-char overlap) producing `Chunk.metadata` with headers + language for BM25 triggers.
- Embedding generator using Snowflake Arctic Embed (1024-d) that writes to `embeddings` and triggers BM25 index population.

**Stretch Experiments**
- Selective re-embedding only for modified sections by diffing chunk hashes.
- Notebook visualizer comparing chunk boundaries vs. semantic cohesion to tune overlap.
- Repo/worktree watcher that auto-runs ingest when files change so Claude always has current docs.

### 4. Web Crawling Pipeline

**Learning Objectives**
- Compare Crawl4AI vs. lightweight fetchers and learn how to manage recursion/dedup inside LangChain workflows.
- Practice respectful crawling (depth limits, rate limiting) for personal doc harvesting.

**Minimum Build**
- Crawl4AI-powered fetcher that accepts a seed list, enforces depth ≤3, and saves normalized HTML → markdown content.
- `crawl_queue` + `crawled_urls` tables for per-collection dedup plus manual include/exclude glob filters.
- Simple aiohttp-based fallback fetcher for static pages so I can contrast performance.

**Stretch Experiments**
- Auto-discover seeds via `llms.txt`/sitemaps and generate crawl plans automatically.
- Adaptive per-domain rate limiter + circuit breaker metrics surfaced via the job-status CLI.
- Store DOM snapshots or screenshots for debugging Crawl4AI behavior.

### 5. Audio Processing Pipeline

**Learning Objectives**
- Integrate Whisper (CPU-first) and keep timestamp metadata intact for RAG chunks.
- Understand multilingual impacts on BM25 configs by piping detected language through metadata.

**Minimum Build**
- Format detector + FFmpeg normalization for mp3/wav/m4a/flac files dropped into ingest paths.
- Whisper `base` model invocation (via CLI or python binding) that emits `[time:start-end]` annotations and detected language.
- Transcript chunker that respects timestamp boundaries, stores duration + language on `documents/chunks`, and routes text through the existing embedding + BM25 pipeline.

**Stretch Experiments**
- Speaker diarization + labeling for multi-speaker calls.
- GPU inference toggle + benchmarking notes comparing CPU vs. GPU throughput.
- Folder-watcher script that auto-transcribes new meeting recordings into the default collection.

### 6. Vector Storage (PostgreSQL + pgvector)
**What it does:** Stores and searches document vectors

**Why PostgreSQL?**
- Mature, reliable
- pgvector extension for native vector ops
- Rich querying (metadata filters, joins)
- Local deployment, no cloud required

**Schema:**
- `documents` - metadata about each file/URL/audio
- `chunks` - document pieces with content
- `embeddings` - vector representations (uniform dimension enforced by pgvector)
- `bm25_index` - keyword search index (auto-populated via triggers)
- `crawl_queue` - URLs to crawl with depth/retry tracking
- `crawled_urls` - Deduplication tracking
- `jobs` - Job coordinator state persistence

### 7. RAG Strategy Engine

**Learning Objectives**
- Wire LangChain retrievers (pgvector + BM25) together and observe how query routing impacts answer quality.
- Experiment with rerankers and contextual embeddings in a controlled, local setup.

**Minimum Build**
- Vector retriever using pgvector HNSW and BM25 retriever using PostgreSQL `tsvector` plus simple metadata filters.
- Reciprocal Rank Fusion merge path plus an optional cross-encoder reranker (bge or MiniLM) behind a flag so I can baseline impact/cost.
- Structured logging of query decisions (which strategies fired, latency, chunk IDs) to feed manual evaluations.

**Stretch Experiments**
- LangGraph workflow that chains `crawl → ingest → search` when a query lacks coverage.
- Lightweight eval harness that records my manual relevance notes (NDCG-ish) for future tuning.
- Multi-collection fusion strategy that boosts personal notes vs. public docs differently.

**Implementation Notes**
- The LangChain Expression Language (LCEL) chain in `amelia/langchain/pipeline.py` remains the orchestrator: `router → vector + bm25 → merge → optional reranker → formatter`.
- LangChain tracing IDs flow into structured logs so I can correlate with Job Coordinator telemetry while experimenting.

---

### 8. LangChain Modules
**Purpose:** Centralize all LangChain components (retrievers, rerankers, query planners) that power the production Strategy Engine.

**Modules:**
- `amelia/langchain/pipeline.py` – builds the default LCEL chain wired into `search_documents`.
- `amelia/langchain/retrievers.py` – wraps our pgvector + BM25 backends as LangChain retrievers with filter awareness.
- `amelia/langchain/rerankers.py` – pluggable cross-encoders (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`).
- `amelia/langchain/tool_router.py` – optional node that can call MCP tools (e.g., trigger a crawl) when the query is better served by ingestion.

**Observability:**
- LangChain tracing IDs are propagated into our structured logs and tied to `jobs` / `search_requests` tables.
- Configurable via `LANGCHAIN_TRACING_V2` so you can surface runs in LangSmith or keep them local.

**Testing:**
- Unit tests assert each retriever returns deterministic sets for a seeded corpus.
- Integration tests run the full chain and compare outputs against golden answers.

---

## Data Models

```python
@dataclass
class Document:
    id: UUID
    source_type: str  # "local", "web", or "audio"
    source_path: Optional[str]  # for local files/audio
    source_url: Optional[str]  # for web pages
    domain: Optional[str]  # for web sources
    file_type: str  # .pdf, .md, .mp3, etc.
    title: Optional[str]
    author: Optional[str]
    collection: str  # organize docs into collections
    metadata: Dict[str, Any]
    indexed_at: datetime
    crawled_at: Optional[datetime]  # for web sources
    # Versioning fields
    content_hash: str  # SHA256 hash of content for change detection
    version: int  # Incremented on content changes
    last_modified: datetime  # Last modification timestamp
    # Audio-specific fields
    audio_duration: Optional[float]  # seconds
    language_detected: Optional[str]  # ISO language code
    transcript_model: Optional[str]  # e.g., "whisper-turbo"

@dataclass
class Chunk:
    id: UUID
    document_id: UUID
    chunk_index: int  # position in document
    content: str
    char_count: int
    word_count: int
    headers: Optional[str]  # extracted section headers
    metadata: Dict[str, Any]  # Contains 'language' field for BM25 using PostgreSQL regconfig names (e.g., 'english', 'spanish', 'french')
    # Audio-specific fields (optional)
    start_timestamp: Optional[float]  # seconds
    end_timestamp: Optional[float]  # seconds
    speaker_id: Optional[str]  # Reserved for Phase 2 speaker diarization (not yet implemented)

@dataclass
class Embedding:
    id: UUID
    chunk_id: UUID
    embedding: List[float]  # Vector dimension fixed to 1024 for snowflake-arctic-embed
    model_name: str  # Always 'snowflake-arctic-embed-l-v2.0'
    # All rows must have the same dimension (pgvector constraint)
```

**Database Schema:** (canonical version lives in `init.sql`)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(10) NOT NULL,
    source_path TEXT,
    source_url TEXT,
    domain VARCHAR(255),
    file_type VARCHAR(10),
    title TEXT,
    collection VARCHAR(255) NOT NULL DEFAULT 'default',
    metadata JSONB,
    indexed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    crawled_at TIMESTAMP WITH TIME ZONE,
    content_hash VARCHAR(64) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    audio_duration DOUBLE PRECISION,
    language_detected VARCHAR(10),
    transcript_model VARCHAR(50),
    UNIQUE (source_path, collection),
    UNIQUE (source_url, collection)
);

CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER,
    word_count INTEGER,
    headers TEXT,
    metadata JSONB,
    start_timestamp DOUBLE PRECISION,
    end_timestamp DOUBLE PRECISION,
    speaker_id VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding vector(1024) NOT NULL,
    model_name VARCHAR(255) NOT NULL DEFAULT 'snowflake-arctic-embed-l-v2.0'
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE TABLE IF NOT EXISTS bm25_index (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    tsvector_content tsvector NOT NULL
);

CREATE OR REPLACE FUNCTION update_bm25_index() RETURNS TRIGGER AS $$
DECLARE
    lang_config regconfig;
BEGIN
    BEGIN
        lang_config := (NEW.metadata->>'language')::regconfig;
        IF lang_config IS NULL THEN
            lang_config := 'english'::regconfig;
        END IF;
    EXCEPTION WHEN others THEN
        lang_config := 'english'::regconfig;
    END;

    INSERT INTO bm25_index (chunk_id, tsvector_content)
    VALUES (NEW.id, to_tsvector(lang_config, NEW.content))
    ON CONFLICT (chunk_id)
        DO UPDATE SET tsvector_content = to_tsvector(lang_config, NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chunks_bm25_trigger
AFTER INSERT OR UPDATE OF content, metadata ON chunks
FOR EACH ROW EXECUTE FUNCTION update_bm25_index();

CREATE INDEX IF NOT EXISTS idx_bm25_tsvector ON bm25_index USING GIN(tsvector_content);

CREATE TABLE IF NOT EXISTS crawl_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    collection VARCHAR(255) NOT NULL DEFAULT 'default',
    depth INTEGER NOT NULL DEFAULT 0,
    max_depth INTEGER NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    parent_url TEXT,
    seed_url TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue(status);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_collection ON crawl_queue(collection);

CREATE TABLE IF NOT EXISTS crawled_urls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    collection VARCHAR(255) NOT NULL DEFAULT 'default',
    crawled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status_code INTEGER,
    UNIQUE (url, collection)
);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(20) NOT NULL,
    collection VARCHAR(255) NOT NULL DEFAULT 'default',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    total_items INTEGER,
    processed_items INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    backoff_delay INTEGER
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_collection ON jobs(collection);
```

---

## MCP Tools

Amelia exposes 6 tools to Claude Code:

### 1. `ingest_documents`
Add local documents and audio files to the search index.

```python
{
    "paths": ["/path/to/docs"],
    "recursive": true,
    "file_patterns": ["*.pdf", "*.md", "*.txt", "*.mp3", "*.wav"],
    "collection": "default",
    "transcription_language": "auto"  # optional: 'en', 'es', 'fr', or 'auto'
}
```

### 2. `crawl_website`
Crawl web documentation into a collection.

```python
{
    "url": "https://docs.example.com",
    "collection": "default",
    "max_depth": 3,
    "max_pages": 1000,
    "follow_links": true,
    "exclude_patterns": ["/legacy/", "/archive/"],
    "include_patterns": ["/docs/"],
    "batch_size": 5,
    "js_enabled": true,
    "respect_robots_txt": true
}
```

### 3. `search_documents`
Search indexed documents (local, web, and audio).

```python
{
    "query": "How to implement RAG?",
    "n_results": 5,
    "collection": "default",
    "strategy": "auto",  # auto, vector, hybrid, contextual
    "filters": {
        "source_type": "audio",  # or "local", "web"
        "domain": "docs.example.com",
        "file_type": "mp3",
        "language": "en"  # for audio sources
    }
}
```

### 4. `list_sources`
List all indexed documents.

```python
{
    "collection": "default",
    "source_type": "all",  # all, local, web
    "limit": 100
}
```

### 5. `remove_source`
Remove a document from the index.

```python
{
    "source_path": "/path/to/doc.pdf",  # for local
    "source_url": "https://docs.example.com/page",  # for web
    "collection": "default"
}
```

### 6. `get_statistics`
Get stats about indexed documents.

```python
{
    "collection": "default"
}
```

---

## Key Technical Decisions

### Why PostgreSQL + pgvector instead of ChromaDB?

**Pros:**
- More mature and battle-tested
- Rich query capabilities (joins, filters, aggregations)
- ACID compliance
- Better for production workloads
- Easier to scale if needed

**Cons:**
- Slightly more setup
- Requires separate service

**Decision:** PostgreSQL for reliability and query power.

### Embedding Model: snowflake-arctic-embed-l-v2.0

**Why this model?**
- 1024 dimensions with strong retrieval benchmarks
- Fully local weights (Hugging Face) so no external API dependency
- Good balance of multilingual coverage and latency on consumer GPUs/CPUs
- Matches our learning goal of experimenting with newer open embedding stacks

**Configuration:**
- Hard-coded default in `amelia.embeddings.generator` (no switching logic)
- Embeddings table defined as `vector(1024)` to match Snowflake Arctic Embed output
- Environment only controls runtime device/batch size (`EMBEDDING_DEVICE`, `EMBEDDING_BATCH_SIZE`)

**Change policy:**
- Treat the embedding model as immutable for Amelia 1.0
- Any future swap requires a one-off migration guide, but not part of this TDD

### Chunking Strategy: Hierarchical Markdown

**Why?**
- Respects document structure
- Preserves semantic boundaries
- Better than arbitrary character splitting
- Works well for technical docs

**Approach:**
1. Split by `#` headers first
2. Then by `##` headers
3. Then by `###` headers
4. If still too large, split by character count with overlap

**Config:**
- Max chunk size: 1000 chars
- Overlap: 200 chars (10%)

### Vector Index: HNSW

**Why HNSW?**
- Fast approximate nearest neighbor search
- Good balance of speed vs accuracy
- Works well for 100K+ vectors

**Parameters:**
- `m = 16` - connections per layer (balance speed/accuracy)
- `ef_construction = 64` - construction quality

**Alternative:** IVFFlat for 1M+ vectors

### Hybrid Search: Reciprocal Rank Fusion (RRF)

**Why RRF?**
- Simple and effective
- No need to tune weights
- Combines different ranking scales naturally

**Formula:**
```python
score = sum(1 / (k + rank_i))
```

Where `k = 60` (standard RRF constant).

### Multi-Language BM25 Indexing

**Why dynamic language detection?**
- BM25 relies on text search configurations for stemming and stop words
- Wrong language config silently degrades search quality
- Example: Spanish word "corriendo" with English stemming won't match "correr"

**Approach:**
- Whisper detects language during audio transcription (90+ languages)
- Language stored in `chunks.metadata->>'language'` field
- BM25 trigger dynamically selects text search config per chunk
- Falls back to 'english' if language unknown or invalid

**Supported PostgreSQL configs:**
- english, spanish, french, german, portuguese, italian, russian
- dutch, swedish, norwegian, danish, finnish
- See PostgreSQL docs for full list of text search configurations

---

## Implementation Guide

### Prerequisites

- Python 3.12+
- PostgreSQL 17+ with pgvector extension
- FFmpeg (required for audio transcription)
- Docker (optional, for easy setup)

**System Requirements:**
- **FFmpeg Installation:**
  - macOS: `brew install ffmpeg`
  - Linux (Debian/Ubuntu): `apt-get install ffmpeg`
  - Linux (RedHat/CentOS): `yum install ffmpeg`
  - Windows: `choco install ffmpeg` or download from ffmpeg.org
- **RAM:** 2-8GB depending on Whisper model size
- **GPU (Optional):** For 10-50x faster transcription
- **Storage:** ~1-5GB for Whisper models (downloaded automatically)

### Step 1: Database Setup

**Option A: Docker (easiest)**
```bash
docker run -d \
  --name amelia-postgres \
  -e POSTGRES_DB=amelia \
  -e POSTGRES_USER=amelia \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  ankane/pgvector:latest
```

**Option B: Manual install**
```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or: apt-get install postgresql  # Linux

# Install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # may need sudo

# Create database
createdb amelia
psql amelia -c "CREATE EXTENSION vector;"
```

### Step 2: Install Amelia

```bash
# Clone repo
git clone https://github.com/your-org/amelia.git
cd amelia

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Optional/learning extras (enabled by default for local dev)
pip install langchain langchain-community

# Install Playwright browsers (for web crawling)
playwright install chromium

# Verify FFmpeg is installed
ffmpeg -version

# Or install as package
pip install -e .
```

### Step 3: Configuration

Create `.env` file:
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=amelia
POSTGRES_USER=amelia
POSTGRES_PASSWORD=your_password

# Embedding runtime (model fixed to snowflake-arctic-embed-l-v2.0)
EMBEDDING_DEVICE=cpu  # or 'cuda' if you have GPU

# Search settings
DEFAULT_N_RESULTS=5
ENABLE_HYBRID_SEARCH=true
ENABLE_RERANKING=false  # slower, enable for higher accuracy

# Ingestion
DEFAULT_CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Web Crawling
WEB_CRAWL_MAX_DEPTH=3
WEB_CRAWL_MAX_PAGES=1000
WEB_CRAWL_BATCH_SIZE=5
WEB_CRAWL_TIMEOUT=30
WEB_CRAWL_JS_ENABLED=true
WEB_CRAWL_RESPECT_ROBOTS=true

# Audio Transcription
AUDIO_WHISPER_MODEL=turbo  # turbo, base, medium, large
AUDIO_LANGUAGE=auto  # auto-detect or specify: en, es, fr, etc.
AUDIO_INCLUDE_TIMESTAMPS=true
AUDIO_GPU_ENABLED=false  # set to true if GPU available
```

### Step 4: Initialize Database

```bash
# Run migrations (uses the canonical schema in init.sql)
python -m amelia.migrate  # wrapper around psql init.sql
```

Or manually execute the script:
```bash
psql amelia < init.sql  # init.sql sits in the repo root
```

### Step 5: Run Amelia

```bash
# Start MCP server
python -m amelia
```

The server will:
1. Load embedding model
2. Connect to PostgreSQL
3. Start listening on stdio for MCP requests

### Step 6: Configure Claude Code

Add to Claude Code's MCP config (`~/.config/claude-code/mcp.json`):

```json
{
  "mcpServers": {
    "amelia": {
      "command": "python",
      "args": ["-m", "amelia"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PASSWORD": "your_password"
      }
    }
  }
}
```

### Step 7: Test It

In Claude Code:
```
User: Index my documentation folder

Claude Code will call: ingest_documents with your path

User: Index my meeting recordings

Claude Code will call: ingest_documents with audio folder path
Amelia transcribes all MP3/WAV files automatically

User: Crawl the FastAPI documentation

Claude Code will call: crawl_website with FastAPI docs URL

User: How do I implement RAG?

Claude Code will call: search_documents and return relevant chunks
from local files, web sources, and audio transcripts

User: Find where we discussed the authentication refactor in standup meetings

Claude Code will call: search_documents with filters for audio sources
Returns relevant chunks with timestamps: [time: 12:30-14:15]
```

---

## Project Structure

```
amelia/
├── amelia/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── server.py            # MCP server
│   ├── config.py            # Config management
│   ├── models.py            # Data models
│   ├── database.py          # DB connection & queries
│   ├── ingestion/
│   │   ├── parsers.py       # PDF, DOCX, etc. parsers
│   │   ├── chunking.py      # Chunking strategies
│   │   └── pipeline.py      # Ingestion orchestration
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── transcriber.py   # Whisper ASR integration
│   │   ├── metadata.py      # Audio metadata extraction
│   │   ├── validator.py     # Format validation
│   │   └── chunker.py       # Timestamp-aware chunking
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── web_crawler.py   # Main crawler logic
│   │   ├── url_detector.py  # Sitemap/llms.txt detection
│   │   ├── deduplicator.py  # URL deduplication
│   │   ├── extractor.py     # Content extraction
│   │   └── batch.py         # Parallel crawling
│   ├── embeddings/
│   │   ├── generator.py     # Embedding generation
│   │   └── cache.py         # Embedding cache
│   ├── search/
│   │   ├── vector.py        # Vector search
│   │   ├── bm25.py          # Keyword search
│   │   ├── hybrid.py        # Hybrid search
│   │   ├── reranker.py      # Cross-encoder re-ranking
│   │   └── strategies.py    # Strategy selection
│   └── tools/
│       ├── ingest.py        # ingest_documents tool
│       ├── crawl.py         # crawl_website tool
│       ├── search.py        # search_documents tool
│       └── sources.py       # list/remove sources
├── tests/
│   ├── test_chunking.py
│   ├── test_audio.py
│   ├── test_crawler.py
│   ├── test_search.py
│   └── test_tools.py
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Configuration

### Environment Variables

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=amelia
POSTGRES_USER=amelia
POSTGRES_PASSWORD=<password>

# Embedding runtime
# Model fixed to snowflake-arctic-embed-l-v2.0 (1024 dims)
EMBEDDING_DEVICE=cpu  # or 'cuda' for GPU acceleration
EMBEDDING_BATCH_SIZE=32

# Search
DEFAULT_N_RESULTS=5
MAX_N_RESULTS=50
ENABLE_HYBRID_SEARCH=true
ENABLE_RERANKING=false  # expensive, off by default

# Ingestion
DEFAULT_CHUNK_SIZE=1000
CHUNK_OVERLAP=200
CHUNKING_STRATEGY=hierarchical
MAX_FILE_SIZE_MB=100

# Logging
LOG_LEVEL=INFO

# LangChain telemetry
LANGCHAIN_TRACING_V2=0
LANGCHAIN_PROJECT=amelia-local
```

### config.yaml (optional)

```yaml
database:
  host: ${POSTGRES_HOST}
  port: ${POSTGRES_PORT}
  database: ${POSTGRES_DB}
  user: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}

embedding:
  model_name: snowflake-arctic-embed-l-v2.0
  device: ${EMBEDDING_DEVICE}
  batch_size: 32

search:
  default_n_results: 5
  strategies:
    hybrid_search:
      enabled: true
      alpha: 0.5  # balance vector vs BM25
    reranking:
      enabled: false
      model: cross-encoder/ms-marco-MiniLM-L-6-v2

langchain:
  chain_factory: amelia.langchain.pipeline:create_chain
  reranker_model: cross-encoder/ms-marco-MiniLM-L-6-v2
  tracing:
    enabled: ${LANGCHAIN_TRACING_V2}
    project: ${LANGCHAIN_PROJECT}

ingestion:
  chunk_size: 1000
  chunk_overlap: 200
  chunking_strategy: hierarchical
  supported_extensions:
    - .pdf
    - .docx
    - .txt
    - .md
    - .html
    - .mp3
    - .wav
    - .m4a
    - .flac

web_crawling:
  max_depth: 3
  max_pages: 1000
  batch_size: 5
  timeout: 30
  js_enabled: true
  respect_robots_txt: true
  follow_external_links: false
  user_agent: "Amelia-Bot/1.0"
  exclude_patterns:
    - /login
    - /admin
    - /api

audio:
  whisper_model: turbo  # turbo, base, medium, large
  language: auto  # auto-detect or specify: en, es, fr, etc.
  include_timestamps: true
  gpu_enabled: false
  chunk_by_timestamp: true  # Respect timestamp boundaries when chunking
```

---

## Testing Strategy

Goal: keep a lean suite that proves the core algorithms still work after edits. CI and coverage gates are nice-to-have, not required.

**Unit-ish checks (kept small on purpose)**
- `test_chunking.py`: hierarchical chunk boundaries stay intact for basic markdown samples.
- `test_crawler.py`: URL type detection, deduping, and depth limits behave with fake fixtures.
- `test_audio.py`: Whisper stub produces timestamped text; metadata + chunking preserve language + timing info.

**Integration sanity**
- `test_pipeline.py`: ingest a scratch file then confirm `search_documents` returns the chunk.
- Optional `test_mcp_e2e.py`: smoke the MCP server locally when I change transport/tool wiring (manual run only).

**How to run when needed**
```bash
pytest tests/test_chunking.py tests/test_crawler.py tests/test_audio.py -v
pytest tests/test_pipeline.py -v  # after major ingestion/search changes
```

---

## Code Examples

### Document Versioning and Incremental Updates

#### Computing Content Hash

```python
import hashlib

def compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of document content for change detection.

    Args:
        content: Document text content

    Returns:
        64-character hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# Usage
content = "This is my document content..."
hash_value = compute_content_hash(content)
print(f"Content hash: {hash_value}")
```

#### Checking for Document Changes

```python
async def ingest_with_versioning(
    document_path: str,
    collection: str,
    db_connection
) -> dict:
    """
    Ingest document with automatic change detection and versioning.

    If document exists and content unchanged: Skip re-embedding
    If document exists and content changed: Increment version, re-embed
    If document is new: Create with version 1

    Returns:
        Status dict with action taken (created/updated/skipped)
    """
    # Parse document
    content = parse_document(document_path)

    # Compute content hash
    new_hash = compute_content_hash(content)

    # Check if document exists
    query = """
        SELECT id, content_hash, version
        FROM documents
        WHERE source_path = %s AND collection = %s
    """
    existing_doc = await db_connection.fetchone(
        query,
        (document_path, collection)
    )

    if existing_doc:
        doc_id, old_hash, current_version = existing_doc

        if old_hash == new_hash:
            # Content unchanged - skip re-embedding
            return {
                "action": "skipped",
                "reason": "content_unchanged",
                "document_id": doc_id,
                "version": current_version
            }
        else:
            # Content changed - increment version and re-embed
            new_version = current_version + 1

            # Delete old chunks and embeddings (CASCADE handles this)
            await db_connection.execute(
                "DELETE FROM chunks WHERE document_id = %s",
                (doc_id,)
            )

            # Update document with new hash and version
            await db_connection.execute("""
                UPDATE documents
                SET content_hash = %s,
                    version = %s,
                    last_modified = NOW()
                WHERE id = %s
            """, (new_hash, new_version, doc_id))

            # Re-chunk and re-embed
            chunks = chunk_document(content)
            await store_chunks_and_embeddings(doc_id, chunks, db_connection)

            return {
                "action": "updated",
                "document_id": doc_id,
                "version": new_version,
                "previous_version": current_version
            }
    else:
        # New document - create with version 1
        doc_id = await create_document(
            path=document_path,
            collection=collection,
            content_hash=new_hash,
            version=1,
            db_connection=db_connection
        )

        # Chunk and embed
        chunks = chunk_document(content)
        await store_chunks_and_embeddings(doc_id, chunks, db_connection)

        return {
            "action": "created",
            "document_id": doc_id,
            "version": 1
        }

# Usage
result = await ingest_with_versioning(
    "/path/to/document.pdf",
    "default",
    db_connection
)

if result["action"] == "skipped":
    print(f"Document unchanged (v{result['version']}), skipped re-embedding")
elif result["action"] == "updated":
    print(f"Document updated: v{result['previous_version']} → v{result['version']}")
else:
    print(f"New document created (v{result['version']})")
```

### Audio Transcription Pipeline

#### Audio Transcription with Whisper

```python
from pathlib import Path
from docling.document_converter import DocumentConverter, AudioFormatOption
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.datamodel import asr_model_specs
from docling.datamodel.base_models import InputFormat
from docling.pipeline.asr_pipeline import AsrPipeline

def transcribe_audio(audio_path: str, language: str = "auto") -> str:
    """
    Transcribe audio file using Whisper ASR via Docling.

    Args:
        audio_path: Path to audio file (MP3, WAV, M4A, FLAC)
        language: Target language or 'auto' for detection

    Returns:
        Markdown-formatted transcript with timestamps
    """
    # Configure ASR pipeline with Whisper Turbo
    pipeline_options = AsrPipelineOptions()
    pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO

    # Create converter with ASR configuration
    converter = DocumentConverter(
        format_options={
            InputFormat.AUDIO: AudioFormatOption(
                pipeline_cls=AsrPipeline,
                pipeline_options=pipeline_options,
            )
        }
    )

    # Transcribe - pass Path object
    audio_file = Path(audio_path).resolve()
    result = converter.convert(audio_file)

    # Export to markdown with timestamps
    # Format: [time: 0.0-4.5] Transcribed text here...
    transcript = result.document.export_to_markdown()

    return transcript

# Usage
transcript = transcribe_audio("/path/to/meeting.mp3", language="en")
print(transcript)
```

#### Audio Metadata Extraction

```python
import subprocess
import json
from pathlib import Path

def get_audio_metadata(audio_path: str) -> dict:
    """
    Extract audio file metadata using FFmpeg.

    Returns:
        dict with duration, format, bitrate, sample_rate
    """
    try:
        # Use ffprobe (part of FFmpeg) to get metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        # Extract relevant fields
        format_info = data.get('format', {})
        audio_stream = next(
            (s for s in data.get('streams', []) if s.get('codec_type') == 'audio'),
            {}
        )

        return {
            'duration': float(format_info.get('duration', 0)),
            'format': format_info.get('format_name', 'unknown'),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': audio_stream.get('channels', 0),
            'file_size': int(format_info.get('size', 0))
        }

    except Exception as e:
        logger.error(f"Failed to extract audio metadata: {e}")
        return {}

# Usage
metadata = get_audio_metadata("/path/to/podcast.mp3")
print(f"Duration: {metadata['duration']:.1f}s")
print(f"Format: {metadata['format']}")
```

#### Language Detection from Transcript

```python
def detect_language_from_transcript(transcript: str) -> str:
    """
    Detect language from transcript content.

    Whisper includes language detection, but this can be used
    to verify or detect language from existing transcripts.
    """
    from langdetect import detect

    try:
        # Sample first 500 characters for detection
        sample = transcript[:500]
        language_code = detect(sample)
        return language_code
    except:
        return "unknown"

# Usage
language = detect_language_from_transcript(transcript)
print(f"Detected language: {language}")
```

#### Transcript Chunking with Timestamps

```python
import re
from typing import List, Tuple

def chunk_transcript_with_timestamps(
    transcript: str,
    max_chunk_size: int = 1000
) -> List[Tuple[str, float, float]]:
    """
    Chunk transcript while preserving timestamp boundaries.

    Returns:
        List of (chunk_text, start_time, end_time) tuples
    """
    # Parse timestamp format: [time: 0.0-4.5] Text here...
    timestamp_pattern = r'\[time:\s*(\d+\.?\d*)-(\d+\.?\d*)\]\s*([^\[]+)'
    matches = re.findall(timestamp_pattern, transcript)

    chunks = []
    current_chunk = ""
    chunk_start = None
    chunk_end = None

    for start_time, end_time, text in matches:
        start = float(start_time)
        end = float(end_time)

        # Initialize first chunk
        if chunk_start is None:
            chunk_start = start

        # Check if adding this segment exceeds max size
        if len(current_chunk) + len(text) > max_chunk_size and current_chunk:
            # Save current chunk
            chunks.append((current_chunk.strip(), chunk_start, chunk_end))

            # Start new chunk
            current_chunk = text
            chunk_start = start
            chunk_end = end
        else:
            # Add to current chunk
            current_chunk += " " + text
            chunk_end = end

    # Add final chunk
    if current_chunk:
        chunks.append((current_chunk.strip(), chunk_start, chunk_end))

    return chunks

# Usage
chunks = chunk_transcript_with_timestamps(transcript, max_chunk_size=1000)
for i, (text, start, end) in enumerate(chunks):
    print(f"Chunk {i}: [{start:.1f}s - {end:.1f}s]")
    print(f"  {text[:100]}...")
```

#### Storing Chunks with Language Metadata for BM25

```python
async def store_audio_chunks_with_language(
    document_id: UUID,
    chunks: List[Tuple[str, float, float]],
    detected_language: str,
    db_connection
) -> None:
    """
    Store audio chunks with language metadata for proper BM25 indexing.

    The language metadata ensures the BM25 trigger uses correct stemming rules.

    Args:
        document_id: Parent document UUID
        chunks: List of (text, start_time, end_time) tuples
        detected_language: ISO language code from Whisper (e.g., 'en', 'es', 'fr')
        db_connection: Database connection
    """
    # Map ISO codes to PostgreSQL text search configs
    language_map = {
        'en': 'english',
        'es': 'spanish',
        'fr': 'french',
        'de': 'german',
        'pt': 'portuguese',
        'it': 'italian',
        'ru': 'russian',
        'nl': 'dutch',
        'sv': 'swedish',
        'no': 'norwegian',
        'da': 'danish',
        'fi': 'finnish',
        # Add more as needed
    }

    # Get PostgreSQL config name, default to 'english' if not mapped
    pg_language = language_map.get(detected_language, 'english')

    for idx, (text, start_ts, end_ts) in enumerate(chunks):
        chunk_id = uuid4()

        # CRITICAL: Store language in metadata for BM25 trigger
        metadata = {
            'language': pg_language,  # Used by BM25 trigger for correct tokenization
            'source_language_code': detected_language  # Original ISO code for reference
        }

        await db_connection.execute("""
            INSERT INTO chunks (
                id, document_id, chunk_index, content,
                char_count, word_count, metadata,
                start_timestamp, end_timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, (
            chunk_id,
            document_id,
            idx,
            text,
            len(text),
            len(text.split()),
            metadata,  # BM25 trigger will extract 'language' field
            start_ts,
            end_ts
        ))

        # BM25 trigger automatically runs and uses metadata->>'language'
        # for correct text search configuration

# Usage example
detected_lang = "es"  # Detected by Whisper
chunks = chunk_transcript_with_timestamps(transcript)
await store_audio_chunks_with_language(
    document_id=doc_id,
    chunks=chunks,
    detected_language=detected_lang,
    db_connection=db
)
# Result: Spanish chunks get 'spanish' stemming in BM25, not 'english'!
```

#### Audio Format Validation

```python
def validate_audio_format(file_path: str) -> bool:
    """
    Check if file is a supported audio format.

    Returns:
        True if format is supported, False otherwise
    """
    from pathlib import Path

    supported_extensions = {'.mp3', '.wav', '.m4a', '.flac'}
    file_ext = Path(file_path).suffix.lower()

    if file_ext not in supported_extensions:
        return False

    # Additional validation: check if FFmpeg can read it
    try:
        cmd = ['ffprobe', '-v', 'error', file_path]
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

# Usage
if validate_audio_format("/path/to/file.mp3"):
    transcript = transcribe_audio("/path/to/file.mp3")
```

### Web Crawling Pipeline

#### URL Type Detection

```python
async def detect_url_type(url: str) -> str:
    """
    Detect if URL is a sitemap, llms.txt, or regular page.
    """
    if url.endswith('/sitemap.xml') or 'sitemap' in url.lower():
        return 'sitemap'

    if url.endswith('/llms.txt') or url.endswith('/llms-full.txt'):
        return 'llms_txt'

    # Try fetching llms.txt at root
    parsed = urlparse(url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(llms_url) as resp:
                if resp.status == 200:
                    return 'llms_txt'
    except:
        pass

    return 'regular'
```

#### Recursive Crawling with Depth Limits

```python
class WebCrawler:
    def __init__(self, max_depth: int = 3, max_pages: int = 1000):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited = set()
        self.crawl4ai = AsyncWebCrawler()

    async def crawl(
        self,
        start_url: str,
        collection: str,
        exclude_patterns: List[str] = None
    ) -> List[Document]:
        """
        Recursively crawl from start_url up to max_depth.
        """
        queue = [(start_url, 0)]  # (url, depth)
        documents = []

        while queue and len(self.visited) < self.max_pages:
            url, depth = queue.pop(0)

            # Skip if already visited
            if url in self.visited:
                continue

            # Skip if exceeds depth
            if depth > self.max_depth:
                continue

            # Skip if matches exclude patterns
            if self._should_exclude(url, exclude_patterns):
                continue

            # Mark as visited
            self.visited.add(url)

            # Crawl page
            try:
                result = await self.crawl4ai.arun(url)
                doc = self._extract_document(result, url, collection)
                documents.append(doc)

                # Extract links if within depth limit
                if depth < self.max_depth:
                    links = self._extract_internal_links(result, url)
                    for link in links:
                        if link not in self.visited:
                            queue.append((link, depth + 1))

            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")

        return documents

    def _should_exclude(self, url: str, patterns: List[str]) -> bool:
        """Check if URL matches any exclude pattern."""
        if not patterns:
            return False
        return any(pattern in url for pattern in patterns)

    def _extract_internal_links(self, result, base_url: str) -> List[str]:
        """Extract internal links from crawled page."""
        soup = BeautifulSoup(result.html, 'html.parser')
        base_domain = urlparse(base_url).netloc

        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)

            # Only include internal links
            if urlparse(absolute_url).netloc == base_domain:
                # Remove fragments and normalize
                clean_url = urldefrag(absolute_url)[0]
                links.append(clean_url)

        return links
```

#### Parallel Crawling with Memory Management

```python
async def crawl_parallel(
    urls: List[str],
    batch_size: int = 5
) -> List[Document]:
    """
    Crawl URLs in parallel batches to manage memory.

    Adapts batch size based on available memory.
    """
    documents = []

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]

        # Check memory before proceeding
        if not self._has_sufficient_memory():
            logger.warning("Low memory, reducing batch size")
            batch_size = max(1, batch_size // 2)
            batch = urls[i:i + batch_size]

        # Crawl batch in parallel
        tasks = [self._crawl_single(url) for url in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        batch_docs = [r for r in results if isinstance(r, Document)]
        documents.extend(batch_docs)

        # Progress update
        logger.info(f"Crawled {len(documents)}/{len(urls)} pages")

    return documents

def _has_sufficient_memory(self, threshold_mb: int = 500) -> bool:
    """Check if sufficient memory is available."""
    import psutil
    available_mb = psutil.virtual_memory().available / 1024 / 1024
    return available_mb > threshold_mb
```

#### Deduplication Strategy

```python
class CrawlDeduplicator:
    """Prevents re-crawling same URLs."""

    def __init__(self, db_connection):
        self.db = db_connection

    async def is_crawled(self, url: str, collection: str) -> bool:
        """Check if URL already crawled for this collection."""
        query = """
            SELECT 1 FROM crawled_urls
            WHERE url = %s AND collection = %s
        """
        result = await self.db.fetchone(query, (url, collection))
        return result is not None

    async def mark_crawled(self, url: str, collection: str, status_code: int):
        """Mark URL as crawled."""
        query = """
            INSERT INTO crawled_urls (id, url, collection, status_code)
            VALUES (gen_random_uuid(), %s, %s, %s)
            ON CONFLICT (url, collection) DO UPDATE
            SET crawled_at = NOW(), status_code = EXCLUDED.status_code
        """
        await self.db.execute(query, (url, collection, status_code))

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL to prevent duplicates.

        - Remove trailing slashes
        - Remove fragments (#)
        - Sort query parameters
        - Lowercase scheme and domain
        """
        parsed = urlparse(url)

        # Normalize scheme and domain
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove trailing slash from path
        path = parsed.path.rstrip('/')

        # Sort query parameters
        query_params = parse_qs(parsed.query)
        sorted_query = urlencode(sorted(query_params.items()))

        # Reconstruct without fragment
        normalized = urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            sorted_query,
            ''  # no fragment
        ))

        return normalized
```

### Hierarchical Markdown Chunking

```python
def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> List[str]:
    """
    Hierarchically split markdown by headers, respecting structure.

    Tries to keep sections together, only splitting when necessary.
    """
    chunks = []

    # Split by # headers first
    sections = re.split(r'\n(?=#\s)', markdown)

    for section in sections:
        if len(section) <= max_len:
            chunks.append(section)
        else:
            # Too large, split by ## headers
            subsections = re.split(r'\n(?=##\s)', section)
            for sub in subsections:
                if len(sub) <= max_len:
                    chunks.append(sub)
                else:
                    # Still too large, split by character count with overlap
                    chunks.extend(fixed_size_chunk(sub, max_len))

    return chunks

def fixed_size_chunk(text: str, max_len: int, overlap: int = 200) -> List[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + max_len
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # overlap with next chunk

    return chunks
```

### Contextual Embeddings

```python
def create_contextual_embedding(chunk: Chunk, document: Document) -> str:
    """
    Add context to chunk before embedding.

    Context includes:
    - Document title
    - Section headers
    - Previous chunk (for continuity)
    """
    context_parts = []

    if document.title:
        context_parts.append(f"Document: {document.title}")

    if chunk.headers:
        context_parts.append(f"Section: {chunk.headers}")

    # Add snippet from previous chunk for continuity
    prev_chunk = get_previous_chunk(chunk)
    if prev_chunk:
        context_parts.append(f"Previous: {prev_chunk.content[-200:]}")

    context = " | ".join(context_parts)
    return f"{context}\n\n{chunk.content}"
```

### Hybrid Search with RRF

```python
async def hybrid_search(
    query: str,
    n_results: int = 5,
    alpha: float = 0.5
) -> List[ScoredChunk]:
    """
    Combine vector and BM25 search using Reciprocal Rank Fusion.

    Args:
        alpha: Weight for vector vs BM25 (0.5 = equal weight)
    """
    # Get more results than needed for fusion
    k = n_results * 3

    # Execute both searches in parallel
    vector_results, bm25_results = await asyncio.gather(
        vector_search(query, n_results=k),
        bm25_search(query, n_results=k)
    )

    # Apply Reciprocal Rank Fusion
    rrf_scores = {}
    k_constant = 60

    for rank, chunk in enumerate(vector_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0) + \
            alpha / (k_constant + rank)

    for rank, chunk in enumerate(bm25_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0) + \
            (1 - alpha) / (k_constant + rank)

    # Sort by combined score
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [get_chunk_by_id(chunk_id) for chunk_id, _ in ranked[:n_results]]
```

### Cross-Encoder Re-ranking

```python
class CrossEncoderReranker:
    """Re-rank search results using cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        chunks: List[Chunk],
        top_k: int = 5
    ) -> List[ScoredChunk]:
        """
        Re-rank chunks using cross-encoder.

        Cross-encoders are more accurate than bi-encoders for ranking
        because they encode query and document together.
        """
        # Prepare query-document pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Get relevance scores
        scores = self.model.predict(pairs)

        # Combine and sort
        scored = [
            ScoredChunk(chunk=c, score=s)
            for c, s in zip(chunks, scores)
        ]
        scored.sort(key=lambda x: x.score, reverse=True)

        return scored[:top_k]
```

---

## Dependencies

### Core Dependencies

```
# requirements.txt

# MCP
fastmcp==2.13.0.2

# Database
psycopg[binary]==3.2.1
pgvector==0.2.5
sqlalchemy==2.0.44

# ML/AI
sentence-transformers==4.1.0
torch==2.7.0
transformers==4.51.3
rank-bm25==0.2.2

# Web Crawling
crawl4ai==0.7.6
playwright==1.48.0
aiohttp==3.10.0

# Audio Processing
docling[vlm]>=2.61.2
openai-whisper>=20250625
ffmpeg-python>=0.2.0
pydub>=0.25.1

# Document processing
pypdf2==3.0.1
python-docx==1.1.2
beautifulsoup4==4.13.4
markdown-it-py==3.0.0
lxml==5.2.0

# Utilities
pydantic==2.11.4
python-dotenv==1.1.0
loguru==3.14.1
aiofiles==24.1.0
psutil==6.0.0
langdetect==1.0.9  # for language detection
```

### Dev Dependencies

```
# requirements-dev.txt
pytest==8.3.5
pytest-asyncio==0.23.0
pytest-cov==4.1.0
black==24.0.0
ruff==0.3.0
mypy==1.9.0
```

---

## Performance Tips

### Target Latencies
- Vector search: <100ms (p95)
- Hybrid search: <200ms (p95)
- Search with re-ranking: <500ms (p95)
- Document ingestion: <5s per document

### Optimizations

**1. Database**
- Use connection pooling (min=5, max=20)
- Tune HNSW parameters: `m=16, ef_construction=64`
- Set `maintenance_work_mem` higher during index creation
- Use `COPY` for bulk inserts

**2. Embeddings**
- Batch embedding generation (32-64 per batch)
- Use GPU if available (10-50x faster)
- Cache embeddings for unchanged chunks
- Prewarm model on startup

**3. Search**
- Limit vector search to top-k candidates before re-ranking
- Cache frequent queries (5-minute TTL)
- Use prepared statements for common queries
- Only enable re-ranking for high-precision needs

**4. Ingestion**
- Process documents in parallel (asyncio)
- Batch database commits
- Use progress tracking for large ingestions

---

## Troubleshooting

### Issue: Slow vector search

**Possible causes:**
- Missing HNSW index
- Low `ef_search` parameter
- Too many results requested

**Solutions:**
```sql
-- Check if index exists
\d embeddings

-- Create HNSW index if missing
CREATE INDEX idx_embeddings_vector ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Increase ef_search at query time
SET hnsw.ef_search = 100;
```

### Issue: Out of memory during ingestion

**Possible causes:**
- Large batch size
- Large embedding model
- Too many documents in memory

**Solutions:**
- Reduce batch size: `EMBEDDING_BATCH_SIZE=16`
- Use 8-bit quantized weights for snowflake-arctic-embed (via bitsandbytes) to shrink VRAM/RAM footprint
- Process documents in smaller batches
- Increase system memory or use swap

### Issue: Poor search results

**Possible causes:**
- Wrong strategy for query type
- Low-quality chunking
- Model not suited for domain

**Solutions:**
- Enable hybrid search: `ENABLE_HYBRID_SEARCH=true`
- Adjust chunk size: `DEFAULT_CHUNK_SIZE=1500`
- Try different embedding model
- Enable re-ranking for higher precision

### Issue: Database connection errors

**Possible causes:**
- PostgreSQL not running
- Wrong credentials
- Connection pool exhausted

**Solutions:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check credentials
psql -h localhost -U amelia -d amelia

# Increase pool size
POSTGRES_POOL_SIZE=30
```

### Issue: Web crawling fails

**Possible causes:**
- Playwright not installed
- Site blocks automated crawlers
- Network/firewall issues
- robots.txt blocking

**Solutions:**
```bash
# Install Playwright browsers
playwright install chromium

# Check if site is accessible
curl -I https://example.com

# Disable robots.txt checking (use responsibly)
WEB_CRAWL_RESPECT_ROBOTS=false

# Try with different user agent
WEB_CRAWL_USER_AGENT="Mozilla/5.0 ..."
```

### Issue: Crawling times out

**Possible causes:**
- Slow website
- JavaScript-heavy site
- Network latency

**Solutions:**
- Increase timeout: `WEB_CRAWL_TIMEOUT=60`
- Reduce batch size: `WEB_CRAWL_BATCH_SIZE=2`
- Disable JS if not needed: `WEB_CRAWL_JS_ENABLED=false`
- Try crawling during off-peak hours

### Issue: Duplicate URLs crawled

**Possible causes:**
- URL normalization issues
- Query parameters creating duplicates
- Redirects

**Solutions:**
- URLs are normalized automatically (trailing slashes, lowercase domains)
- Use `exclude_patterns` to skip parameter variations
- Check `crawled_urls` table for patterns
- Implement custom URL normalization if needed

### Issue: Audio transcription fails

**Possible causes:**
- FFmpeg not installed or not in PATH
- Unsupported audio format
- Corrupted audio file
- Out of memory

**Solutions:**
```bash
# Verify FFmpeg installation
ffmpeg -version

# Install FFmpeg if missing
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Linux
choco install ffmpeg  # Windows

# Check audio file is readable
ffprobe path/to/audio.mp3

# Try with smaller Whisper model
AUDIO_WHISPER_MODEL=base
```

### Issue: Slow audio transcription

**Possible causes:**
- Large Whisper model
- No GPU acceleration
- Large audio files
- CPU bottleneck

**Solutions:**
- Enable GPU if available: `AUDIO_GPU_ENABLED=true`
- Use smaller model: `AUDIO_WHISPER_MODEL=base`
- Process audio files in smaller batches
- Split long audio files into chunks before processing
- Close other resource-intensive applications

### Issue: Poor transcription quality

**Possible causes:**
- Low audio quality
- Background noise
- Wrong language setting
- Small Whisper model
- Accents or speaking speed

**Solutions:**
- Use larger model: `AUDIO_WHISPER_MODEL=medium` or `large`
- Specify correct language: `AUDIO_LANGUAGE=en` instead of `auto`
- Preprocess audio to reduce noise using tools like Audacity
- Ensure audio bitrate is at least 64kbps
- Use lossless formats (WAV, FLAC) for best results

### Issue: Out of memory during transcription

**Possible causes:**
- Whisper model too large for available RAM
- Multiple audio files being processed simultaneously
- Large audio files

**Solutions:**
- Use smaller model: `base` instead of `turbo` or `large`
- Reduce batch size for parallel processing
- Process one audio file at a time
- Increase system RAM or swap space
- Split large audio files (>1 hour) into smaller segments

---

## Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: amelia
      POSTGRES_USER: amelia
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amelia"]
      interval: 10s
      timeout: 5s
      retries: 5

  amelia:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: amelia
      POSTGRES_USER: amelia
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ${DOCUMENTS_DIR}:/documents:ro
    stdin_open: true
    tty: true

volumes:
  postgres_data:
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('snowflake/snowflake-arctic-embed-l-v2.0')"

# Create non-root user
RUN useradd -m -u 1000 amelia && \
    chown -R amelia:amelia /app
USER amelia

CMD ["python", "-m", "amelia"]
```

### Run with Docker

```bash
# Create .env file
echo "POSTGRES_PASSWORD=your_secure_password" > .env
echo "DOCUMENTS_DIR=/path/to/your/docs" >> .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f amelia

# Stop services
docker-compose down
```

---

## FAQ

**Q: Why not use ChromaDB?**
A: PostgreSQL + pgvector is more mature, has richer query capabilities, and scales better. ChromaDB is simpler but less powerful.

**Q: Can I use a different embedding model?**
A: Not for Amelia 1.0. The embeddings table is locked to Snowflake's `snowflake-arctic-embed-l-v2.0` output (1024 dimensions) to keep the system deterministic. Swapping models would require a one-off migration (dropping embeddings, re-embedding, rebuilding HNSW), which is intentionally out of scope until after Phase 4.

**Q: Does this work with GPU?**
A: Yes! Set `EMBEDDING_DEVICE=cuda` to use GPU. You'll need CUDA installed and a compatible GPU.

**Q: How many documents can it handle?**
A: Tested with 100K+ documents. PostgreSQL + pgvector scales well. For 1M+ vectors, consider IVFFlat index instead of HNSW.

**Q: Can I search multiple collections?**
A: Yes! Each document is assigned to a collection. You can search within a specific collection or across all.

**Q: Is re-ranking worth it?**
A: Depends. Re-ranking improves precision but adds ~300ms latency. Enable it for high-precision needs, disable for speed.

**Q: How do I update a document?**
A: Simply re-ingest the document using `ingest_documents`. Amelia automatically detects changes by comparing SHA256 content hashes. If the content is unchanged, it skips re-embedding and keeps the existing version. If the content changed, it increments the version number, re-chunks and re-embeds the content, and updates the `last_modified` (or `crawled_at` for web sources) timestamp. This incremental update approach is efficient and avoids unnecessary reprocessing of unchanged documents.

**Q: How does web crawling work?**
A: Amelia uses Crawl4AI with Playwright for browser automation. It can handle JavaScript-heavy sites, follow links recursively, and respect depth limits.

**Q: Can I crawl authenticated sites?**
A: Not in Phase 3. Authentication support is planned for Phase 2 enhancements. Currently only public documentation is supported.

**Q: How do I prevent crawling too many pages?**
A: Set `max_pages` and `max_depth` limits. Use `exclude_patterns` to skip irrelevant sections. Start with conservative limits and expand as needed.

**Q: Does crawling respect robots.txt?**
A: Yes, by default. You can disable with `respect_robots_txt: false` but use this responsibly and only for sites you have permission to crawl.

**Q: Can I mix local and web sources in one collection?**
A: Yes! Collections can contain both local files and web pages. Use the `source_type` filter to search only local or only web.

**Q: Which Whisper model should I use?**
A:
- **Turbo:** Best balance of speed and accuracy (recommended)
- **Base:** Faster but less accurate
- **Medium/Large:** More accurate but slower (use with GPU)

**Q: Does audio transcription work offline?**
A: Yes! Whisper runs locally on your machine. The model downloads once (~1-5GB depending on model size) and runs offline thereafter.

**Q: Can it identify different speakers in audio?**
A: Not in Phase 3. Speaker diarization is planned for Phase 2 enhancements. Currently, all audio is treated as single-speaker.

**Q: How accurate is the transcription?**
A: Whisper Turbo achieves 90%+ accuracy on clear audio in supported languages. Accuracy depends on:
- Audio quality (background noise, clarity)
- Language (best for English, good for 90+ languages)
- Speaker accents and speaking speed

**Q: Does it support real-time transcription?**
A: Not yet. Current implementation transcribes complete audio files. Real-time streaming transcription is planned for Phase 2.

**Q: What happens if FFmpeg is not installed?**
A: Audio transcription will fail with an error. FFmpeg is required for audio processing. See installation instructions in Prerequisites section.

**Q: Can I transcribe video files?**
A: Not directly in Phase 3, but you can extract audio from video files using FFmpeg first:
```bash
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3
amelia index audio.mp3
```
Native video support is planned for Phase 2.

---

## References

**MCP Protocol:**
- Spec: https://modelcontextprotocol.io/
- FastMCP v2: https://github.com/jlowin/fastmcp

**PostgreSQL + pgvector:**
- pgvector: https://github.com/pgvector/pgvector
- Performance guide: https://github.com/pgvector/pgvector#performance

**Web Crawling:**
- Crawl4AI: https://github.com/unclecode/crawl4ai
- Playwright: https://playwright.dev/python/
- llms.txt spec: https://llmstxt.org/

**Embedding Models:**
- Sentence Transformers: https://www.sbert.net/
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard

**RAG Techniques:**
- Hybrid Search: https://www.anthropic.com/research/contextual-retrieval
- Contextual Embeddings: https://www.anthropic.com/news/contextual-retrieval

---

## License

MIT License - feel free to use, modify, and distribute.

---

**Happy searching!**

For questions or issues, open a GitHub issue or reach out to the maintainers.
