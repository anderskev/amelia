# Amelia - Local RAG MCP Server

**Version:** 1.0 | **Last Updated:** 2025-11-10

A Model Context Protocol (MCP) server that makes your local documents searchable by Claude Code using advanced RAG techniques.

---

## What is Amelia?

Amelia is a local-first document search tool that:
- Indexes your local docs (PDFs, DOCX, TXT, MD, HTML)
- Transcribes and indexes audio files (MP3, WAV, M4A, FLAC)
- Crawls and indexes web documentation (URLs, sitemaps, llms.txt)
- Lets Claude Code search everything using natural language
- Uses advanced RAG strategies for accurate retrieval
- Runs entirely on your machine (privacy-friendly)

**Key Features:**
- MCP server integration (plug right into Claude Code)
- Advanced RAG: contextual embeddings, hybrid search, re-ranking
- Audio transcription via Whisper ASR (Automatic Speech Recognition)
- Web crawling via Crawl4AI with browser automation
- PostgreSQL + pgvector for vector storage
- Configurable strategies based on query type
- Fast: <100ms for vector search, <200ms for hybrid, ~5-10x real-time transcription

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
**What it does:** Orchestrates long-running operations and manages system resources

**Key parts:**
- **Job Queue Manager:** Separate queues for ingestion, crawling, and transcription jobs
- **Status Tracking:** Monitors job progress (pending, running, completed, failed)
- **Retry Logic:** Exponential backoff for failed operations with persisted retry state
  - Retry delays: 1s, 2s, 4s, 8s, 16s, 32s (max 60s)
  - Default max retries: 3 attempts per job
  - Persists `retry_count`, `max_retries`, `next_run_at`, `last_retry_at`, and `backoff_delay` to jobs table
- **Backpressure Management:** Limits concurrent jobs to prevent resource exhaustion
  - Max 3 crawl jobs concurrently
  - Max 2 transcription jobs (memory intensive)
  - Max 5 ingestion jobs
- **Crash Recovery:** Full state persistence enables recovery after server restarts
  - On startup, queries jobs table for `status='running'` or jobs with `next_run_at <= NOW()`
  - Reconstructs retry state from `retry_count`, `next_run_at`, and `backoff_delay` columns
  - Resumes pending retries or marks stale jobs as failed
  - Re-enqueues interrupted jobs based on persisted progress and metadata
- **Progress Reporting:** Returns real-time status to MCP clients

**Implementation:**
- Uses asyncio.Queue for in-memory job queuing
- PostgreSQL `jobs` table for durable state persistence
- Worker pool pattern with semaphores for concurrency control
- Periodic background task to check for scheduled retries (`next_run_at`)

### 3. Document Processing Pipeline
**What it does:** Ingests and prepares documents for search

**Key parts:**
- **Parsers:** PDF, DOCX, TXT, MD, HTML
- **Audio Transcriber:** Whisper ASR for speech-to-text
- **Content Hash Generator:** Computes SHA256 hash of document content for change detection
- **Version Manager:** Compares content hash with existing documents
  - If hash matches: Skip re-embedding, keep existing version
  - If hash differs: Increment version, re-chunk, re-embed, update timestamp
  - Enables efficient incremental updates without manual tracking
- **Chunker:** Splits docs into searchable pieces
  - Hierarchical markdown chunking (respects headers)
  - Semantic chunking (respects sentences/paragraphs)
  - Timestamp-aware chunking for audio transcripts
  - Fixed-size with overlap (fallback)
- **Metadata extractor:** Pulls out title, author, headers, audio duration, etc.
- **Embedding generator:** Creates vector embeddings

### 4. Web Crawling Pipeline
**What it does:** Fetches and processes web documentation

**Key parts:**
- **URL Detection:** Identifies sitemap, llms.txt, or regular pages
- **Crawl4AI Integration:** Browser automation for JavaScript-heavy sites
- **Worker Pool:** Manages concurrent crawlers with configurable pool size
  - Default: 5 workers per crawl job
  - Adaptive sizing based on available memory
- **Per-Domain Rate Limiting:** Prevents overwhelming target servers
  - Default: 1 request/second per domain
  - Configurable via `rate_limit_per_domain` setting
  - Uses token bucket algorithm for burst handling
- **Link Extractor:** Finds and follows internal links
- **Deduplication:** Prevents re-crawling same URLs
- **Content Normalizer:** Cleans and extracts main content
- **Batch Processor:** Parallel crawling with memory management
- **Depth Tracker:** Enforces max crawl depth limits
- **Retry with Backoff:** Handles transient failures (timeouts, 5xx errors)
  - Max 3 retries per URL
  - Exponential backoff: 2^retry_count seconds (2s, 4s, 8s)
  - Uses `last_attempt_at` timestamp to enforce retry delays
  - Query-based: SELECT URLs WHERE (status='failed' AND retry_count < 3 AND last_attempt_at < NOW() - backoff_interval)
- **Circuit Breaker:** Stops crawling a domain after repeated failures
  - Query-based: Before selecting a URL, count failed URLs from same domain
  - Skip domains with >= 10 recent failures (within last 5 minutes)
  - No separate state table needed - queries `crawl_queue` for failure counts

**Implementation:**
- asyncio worker pool with semaphores
- aiohttp for HTTP requests with connection pooling
- Per-domain rate limiters using asyncio locks + timestamps
- Backoff/circuit-breaker implemented via SQL queries (no in-memory state)
- Change detection: SHA256 content hashing to avoid re-embedding unchanged documents (see Data Flows above)
  - Note: MVP supports detecting changes during crawls, but does NOT include automated re-crawl scheduling

### 5. Audio Processing Pipeline
**What it does:** Transcribes audio files into searchable text with multi-language support

**Key parts:**
- **Format Detector:** Identifies MP3, WAV, M4A, FLAC files
- **FFmpeg Integration:** Audio format conversion and validation
- **Whisper ASR:** OpenAI Whisper for transcription
  - Turbo model for speed/accuracy balance
  - 90+ language support with automatic detection
  - Language detection is CRITICAL for search quality
- **Language Propagation:** Detected language flows to chunks.metadata for BM25 indexing
  - Ensures correct stemming and tokenization for non-English content
  - Example: Spanish content gets 'spanish' config, not 'english' stemming rules
  - Prevents silent degradation of multilingual search quality
- **Timestamp Extractor:** Preserves temporal markers in transcripts
- **Metadata Collector:** Audio duration, bitrate, format, detected language
- **Transcript Formatter:** Converts to markdown with timestamp annotations

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
**What it does:** Intelligently combines multiple search approaches

**Strategies:**
1. **Vector Search** - Semantic similarity (always used)
2. **Hybrid Search** - Combines vector + BM25 keyword search
3. **Contextual Embeddings** - Adds document context to chunks
4. **Re-ranking** - Uses cross-encoder for final ranking (optional, slower)

**Auto-selection logic:**
- Technical terms/acronyms? → Add BM25
- Long query? → Use contextual embeddings
- Large corpus? → Apply re-ranking

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

### Unit Tests

```python
# tests/test_chunking.py
def test_hierarchical_chunking():
    markdown = """
    # Main Header
    Content 1
    ## Sub Header
    Content 2
    """
    chunks = smart_chunk_markdown(markdown, max_len=100)
    assert len(chunks) > 0
    assert any("# Main Header" in c for c in chunks)

# tests/test_search.py
@pytest.mark.asyncio
async def test_vector_search():
    results = await search_engine.vector_search("test query")
    assert len(results) > 0
    assert results[0].score > 0

# tests/test_crawler.py
@pytest.mark.asyncio
async def test_url_detection():
    assert await detect_url_type("https://example.com/sitemap.xml") == "sitemap"
    assert await detect_url_type("https://example.com/llms.txt") == "llms_txt"
    assert await detect_url_type("https://example.com/page") == "regular"

@pytest.mark.asyncio
async def test_crawl_deduplication():
    dedup = CrawlDeduplicator(db)
    await dedup.mark_crawled("https://example.com/page", "test-collection", 200)
    assert await dedup.is_crawled("https://example.com/page", "test-collection")

@pytest.mark.asyncio
async def test_recursive_crawl_depth():
    crawler = WebCrawler(max_depth=2)
    results = await crawler.crawl("https://example.com", "test")
    # Should not crawl beyond depth 2
    assert all(r.metadata.get("depth", 0) <= 2 for r in results)

# tests/test_audio.py
def test_audio_format_validation():
    assert validate_audio_format("test.mp3") == True
    assert validate_audio_format("test.wav") == True
    assert validate_audio_format("test.txt") == False

@pytest.mark.asyncio
async def test_audio_transcription():
    # Mock audio file
    audio_path = "tests/fixtures/sample.mp3"
    transcript = await transcribe_audio(audio_path, language="en")
    assert len(transcript) > 0
    assert "[time:" in transcript  # Check for timestamp markers

def test_audio_metadata_extraction():
    metadata = get_audio_metadata("tests/fixtures/sample.mp3")
    assert "duration" in metadata
    assert metadata["duration"] > 0
    assert metadata["format"] in ["mp3", "wav", "m4a", "flac"]

def test_transcript_chunking_preserves_timestamps():
    transcript = "[time: 0.0-4.5] First segment. [time: 4.5-10.2] Second segment."
    chunks = chunk_transcript_with_timestamps(transcript, max_chunk_size=50)
    assert len(chunks) > 0
    for text, start, end in chunks:
        assert start < end
        assert len(text) <= 50
```

### Integration Tests

```python
# tests/test_pipeline.py
@pytest.mark.asyncio
async def test_ingest_and_search(tmp_path):
    # Create test document
    doc = tmp_path / "test.txt"
    doc.write_text("This is about RAG systems.")

    # Ingest
    result = await pipeline.ingest(str(doc))
    assert result.success

    # Search
    results = await search_engine.search("RAG systems")
    assert len(results) > 0
    assert "RAG" in results[0].content
```

### End-to-End Test

```python
# tests/test_mcp_e2e.py
def test_mcp_workflow(tmp_path):
    # Start Amelia server
    server = start_amelia()

    # Call ingest_documents
    response = server.call_tool("ingest_documents", {
        "paths": [str(tmp_path)]
    })
    assert response["status"] == "success"

    # Call search_documents
    response = server.call_tool("search_documents", {
        "query": "test"
    })
    assert len(response["results"]) > 0
```

**Run tests:**
```bash
pytest tests/ -v
pytest tests/ --cov=amelia  # with coverage
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

## Implementation Roadmap

### Phase 1: MVP (2-3 weeks)
**Goal:** Basic working MCP server

- [ ] MCP server with stdio transport
- [ ] Basic document ingestion (TXT, MD)
- [ ] Vector search
- [ ] PostgreSQL + pgvector setup
- [ ] Simple chunking (fixed-size)
- [ ] Basic tools: ingest, search, list

**Success:** Can ingest and search markdown files

**Gate to Phase 2 (all required):**
- Contract tests for `ingest_documents`, `search_documents`, `list_sources` running in CI with recorded fixtures.
- Repeatable database bootstrap verified via `docker-compose up` + smoke test script (no manual tweaks).
- P95 vector search latency <500 ms on the 10K-chunk sample corpus captured under `tests/data/sample_corpus`.
- Structured logs (JSON) emitted for every MCP request with trace IDs so failures can be replayed.

### Phase 2: Advanced RAG (3-4 weeks)
**Goal:** Production-quality search

- [ ] Hybrid search (vector + BM25)
- [ ] Contextual embeddings
- [ ] Hierarchical chunking
- [ ] Support PDF, DOCX, HTML
- [ ] Cross-encoder re-ranking
- [ ] Advanced tools: remove, statistics

**Success:** 20% improvement in search accuracy

**Gate to Phase 3 (all required):**
- Retrieval evaluation harness demonstrating ≥20% NDCG lift over Phase 1 baseline and checked into `tests/evals/`.
- Hybrid + re-ranker paths covered by integration tests with golden answers.
- Benchmark notebook (or markdown report) showing hierarchical chunking quality vs. runtime trade-offs.
- Alerting hook (statsd/Prometheus) for embedding latency regressions wired into Job Coordinator metrics.

### Phase 3: Web Crawling & Audio (3-4 weeks)
**Goal:** Add web documentation and audio support

- [ ] Crawl4AI integration
- [ ] URL type detection (sitemap, llms.txt, regular)
- [ ] Recursive crawling with depth limits
- [ ] Parallel/batched crawling
- [ ] URL deduplication
- [ ] Content extraction and normalization
- [ ] crawl_website MCP tool
- [ ] Web source metadata tracking
- [ ] Audio transcription (Whisper ASR)
- [ ] FFmpeg integration
- [ ] Timestamp preservation
- [ ] Audio metadata extraction
- [ ] Multi-language support

**Success:** Can crawl documentation sites and transcribe audio files

**Gate to Phase 4 (all required):**
- End-to-end soak tests for `crawl_website` and audio transcription covering >3 hour workload without orphaned jobs.
- Backpressure and retry policies validated in CI via chaos test (forced Crawl4AI/playwright failures).
- Data retention policy docs for crawled pages + transcripts (location, TTL, manual purge steps).
- Minimum telemetry dashboards for crawl throughput, transcription queue depth, and failure counts.

### Phase 4: Polish (2-3 weeks)
**Goal:** Production-ready

- [ ] Performance optimization
- [ ] Caching (embeddings, queries)
- [ ] Docker packaging
- [ ] Documentation
- [ ] Testing (>85% coverage)
- [ ] Error handling & logging

**Success:** <100ms vector search, complete docs, robust crawling, audio transcription ~5-10x real-time

**Release Gate:**
- Full regression suite (unit + integration + eval harness) green on CI twice consecutively.
- Disaster recovery drill documented: restore database from snapshot + rebuild embeddings.
- Operational playbooks published for on-call (startup, shutdown, log triage, manual job retry).

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
