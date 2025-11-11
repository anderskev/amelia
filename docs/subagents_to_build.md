# Sub-Agent Ideas for Amelia Project

**Version:** 1.0 | **Last Updated:** 2025-11-10

This document outlines specialized sub-agents that would accelerate development of the Amelia local RAG MCP server. Each sub-agent is designed to handle specific aspects of the project based on the technical design document.

---

## 1. Database Schema Engineer

**Purpose:** Handles all PostgreSQL schema design, migrations, and pgvector optimization.

**Key Responsibilities:**
- Design and validate database schemas
- Write migration scripts using the canonical `init.sql` format
- Optimize HNSW index parameters (`m`, `ef_construction`)
- Create database triggers (e.g., BM25 auto-indexing trigger)
- Review schema changes for performance implications
- Generate test fixtures for database operations

**Tool Access:**
- Read, Write, Edit (for SQL files)
- Bash (for `psql` commands)
- Grep, Glob (for searching existing schema patterns)

**When to Use:**
- "Design the crawl_queue table schema"
- "Optimize the embeddings HNSW index"
- "Create a migration to add retry tracking"
- "Review this schema change for performance issues"

**System Prompt Focus:**
- Deep PostgreSQL expertise
- pgvector index tuning knowledge
- Understanding of ACID properties
- Trigger and constraint design patterns

---

## 2. RAG Strategy Architect

**Purpose:** Designs and optimizes retrieval-augmented generation strategies and algorithms.

**Key Responsibilities:**
- Design vector search algorithms and similarity metrics
- Design hybrid search strategies (vector + BM25) with RRF fusion formulas
- Build contextual embedding strategies
- Design cross-encoder re-ranking approaches
- Tune strategy auto-selection logic
- Benchmark retrieval quality (NDCG, precision@k, MRR)
- Create evaluation harnesses for retrieval quality
- Define ranking fusion weights and parameters

**Note:** Works closely with LangChain Integration Specialist (#16) who implements these algorithms as LangChain LCEL chains and retrievers.

**Tool Access:**
- Read, Write, Edit
- Bash (for running benchmarks)
- WebFetch (for researching latest RAG techniques)

**When to Use:**
- "Design a hybrid search strategy with reciprocal rank fusion"
- "Define contextual embedding strategy to improve retrieval"
- "Calculate optimal BM25 weighting for hybrid search"
- "Create an evaluation harness for retrieval quality"
- "Design auto-selection logic for query routing"

**System Prompt Focus:**
- Vector similarity search algorithms
- BM25 and text search fundamentals
- Ranking fusion techniques (RRF, CombSUM)
- Retrieval evaluation metrics (NDCG, MRR, precision@k)
- Algorithm design and optimization

---

## 3. Audio Pipeline Specialist

**Purpose:** Handles audio transcription, FFmpeg integration, and Whisper ASR.

**Key Responsibilities:**
- Implement Whisper ASR transcription via Docling
- Integrate FFmpeg for format validation and metadata extraction
- Design timestamp-preserving chunking strategies
- Handle language detection and propagation to BM25
- Optimize transcription performance (GPU acceleration, batching)
- Implement audio-specific metadata extraction

**Tool Access:**
- Read, Write, Edit
- Bash (for FFmpeg commands, testing audio files)
- Grep, Glob (for finding audio processing code)

**When to Use:**
- "Add support for MP3 transcription with Whisper"
- "Extract audio metadata using FFmpeg"
- "Implement timestamp-aware chunking for transcripts"
- "Optimize Whisper transcription for GPU"

**System Prompt Focus:**
- Whisper ASR API and model variants
- FFmpeg audio processing
- Language detection and multi-language support
- Audio format specifications (MP3, WAV, M4A, FLAC)

---

## 4. Web Crawler Engineer

**Purpose:** Builds and optimizes the web crawling pipeline with Crawl4AI.

**Key Responsibilities:**
- Implement Crawl4AI integration with Playwright
- Design recursive crawling with depth limits
- Build URL deduplication and normalization
- Implement per-domain rate limiting (token bucket)
- Design retry logic with exponential backoff
- Implement circuit breaker for failing domains
- Handle sitemap.xml and llms.txt parsing

**Tool Access:**
- Read, Write, Edit
- Bash (for testing crawls)
- WebFetch (for understanding target sites)
- Grep, Glob

**When to Use:**
- "Implement recursive web crawling with max depth"
- "Add per-domain rate limiting to prevent server overload"
- "Parse sitemap.xml and extract all URLs"
- "Implement circuit breaker for failing domains"

**System Prompt Focus:**
- Crawl4AI and Playwright APIs
- HTTP protocol and status codes
- Rate limiting algorithms (token bucket, leaky bucket)
- URL parsing and normalization
- robots.txt compliance

---

## 5. Job Coordinator Architect

**Purpose:** Designs and implements the job orchestration system.

**Key Responsibilities:**
- Design job queue architecture (asyncio.Queue + PostgreSQL persistence)
- Implement retry logic with exponential backoff
- Build backpressure management (semaphores, concurrency limits)
- Design crash recovery from persisted state
- Implement progress tracking and status reporting
- Handle job lifecycle (pending, running, completed, failed)

**Tool Access:**
- Read, Write, Edit
- Bash (for testing async operations)
- Grep, Glob

**When to Use:**
- "Design the job coordinator with retry and backpressure"
- "Implement crash recovery from the jobs table"
- "Add progress tracking for long-running crawls"
- "Implement exponential backoff for failed jobs"

**System Prompt Focus:**
- asyncio programming patterns
- Distributed job queue design
- State persistence and recovery
- Backpressure and concurrency control

---

## 6. MCP Protocol Expert

**Purpose:** Handles all Model Context Protocol server implementation.

**Key Responsibilities:**
- Design MCP tool definitions with proper schemas
- Implement JSON-RPC over stdio transport
- Handle MCP request/response lifecycle
- Design tool input validation
- Implement error handling and status reporting
- Write MCP integration tests

**Tool Access:**
- Read, Write, Edit
- Bash (for testing MCP server)
- WebFetch (for MCP spec reference)

**When to Use:**
- "Define the search_documents MCP tool schema"
- "Implement the ingest_documents tool handler"
- "Add proper error handling to MCP responses"
- "Test the MCP server with Claude Code"

**System Prompt Focus:**
- MCP protocol specification
- FastMCP v2 API
- JSON-RPC protocol
- Tool schema design (input validation, output formatting)

---

## 7. Embedding Pipeline Engineer

**Purpose:** Manages embedding generation and optimization.

**Key Responsibilities:**
- Integrate Snowflake Arctic Embed model
- Implement batched embedding generation
- Design embedding caching strategies
- Handle GPU vs CPU execution
- Optimize batch sizes for memory efficiency
- Implement model warmup on startup

**Tool Access:**
- Read, Write, Edit
- Bash (for testing embeddings, profiling)

**When to Use:**
- "Integrate snowflake-arctic-embed-l-v2.0 for embeddings"
- "Implement batched embedding generation"
- "Add embedding cache for unchanged chunks"
- "Optimize GPU memory usage for embedding"

**System Prompt Focus:**
- sentence-transformers library
- PyTorch model loading and inference
- GPU memory management
- Embedding normalization and dimension handling

---

## 8. Chunking Strategy Specialist

**Purpose:** Implements document chunking strategies.

**Key Responsibilities:**
- Design hierarchical markdown chunking
- Implement semantic chunking (sentence/paragraph boundaries)
- Build timestamp-aware chunking for audio
- Handle chunk overlap strategies
- Extract and preserve section headers
- Optimize chunk size for retrieval quality

**Tool Access:**
- Read, Write, Edit
- Bash (for testing chunking)

**When to Use:**
- "Implement hierarchical markdown chunking"
- "Design timestamp-aware chunking for transcripts"
- "Optimize chunk size and overlap parameters"
- "Extract section headers during chunking"

**System Prompt Focus:**
- Text processing and regex
- Markdown structure understanding
- Semantic boundary detection
- Chunk size optimization for embeddings

---

## 9. Document Parser Engineer

**Purpose:** Handles parsing of various document formats.

**Key Responsibilities:**
- Implement PDF parsing with PyPDF2
- Build DOCX parsing with python-docx
- Handle HTML content extraction with BeautifulSoup
- Parse markdown with markdown-it-py
- Extract metadata (title, author, headers)
- Implement content normalization

**Tool Access:**
- Read, Write, Edit
- Bash (for testing parsers with sample files)

**When to Use:**
- "Implement PDF parsing with metadata extraction"
- "Build DOCX parser that preserves formatting"
- "Extract clean content from HTML pages"
- "Parse markdown and extract hierarchical headers"

**System Prompt Focus:**
- Document format specifications
- Library-specific APIs (PyPDF2, python-docx, BeautifulSoup)
- Metadata extraction techniques
- Text normalization and cleaning

---

## 10. Versioning & Change Detection Expert

**Purpose:** Implements content hashing and incremental updates.

**Key Responsibilities:**
- Design SHA256 content hashing strategy
- Implement version tracking and increment logic
- Build change detection workflows
- Handle re-embedding only when content changes
- Design timestamp tracking (last_modified, crawled_at)
- Optimize skip logic for unchanged documents

**Tool Access:**
- Read, Write, Edit
- Grep, Glob

**When to Use:**
- "Implement content hash-based change detection"
- "Design incremental update workflow"
- "Add version tracking to documents table"
- "Optimize re-ingestion to skip unchanged files"

**System Prompt Focus:**
- Cryptographic hashing (SHA256)
- Database versioning patterns
- Content comparison strategies
- Efficient update detection

---

## 11. Performance Optimization Engineer

**Purpose:** Profiles and optimizes system performance across all components including LangChain pipelines.

**Key Responsibilities:**
- Profile database query performance
- Optimize HNSW index parameters
- Tune connection pooling
- Implement query caching
- Optimize batch processing
- Monitor memory usage and prevent leaks
- Benchmark latencies (vector search, hybrid search, transcription)
- Profile LangChain LCEL chain execution
- Optimize LangChain batching and streaming performance
- Measure LangChain tracing overhead
- Tune retriever response times

**Tool Access:**
- Read, Edit
- Bash (for profiling tools, benchmarks)

**When to Use:**
- "Profile vector search and optimize HNSW parameters"
- "Reduce P95 latency for hybrid search"
- "Optimize memory usage during batch ingestion"
- "Benchmark transcription performance"
- "Profile LangChain chain execution and identify bottlenecks"
- "Optimize batching in LangChain retrievers"
- "Measure tracing overhead in production"

**System Prompt Focus:**
- PostgreSQL query optimization (EXPLAIN, ANALYZE)
- Memory profiling tools (psutil, memory_profiler)
- Asyncio performance patterns
- Latency measurement and P95/P99 analysis
- LangChain performance profiling
- Chain composition optimization

---

## 12. Testing & Quality Assurance Specialist

**Purpose:** Writes comprehensive tests and ensures quality gates including LangChain component testing.

**Key Responsibilities:**
- Write unit tests for core components
- Design integration tests for pipelines
- Build end-to-end MCP workflow tests
- Create evaluation harnesses for retrieval quality
- Implement chaos tests for retry/backpressure
- Design soak tests for long-running operations
- Write contract tests with recorded fixtures
- Test LangChain custom retrievers with deterministic outputs
- Write integration tests for LCEL chain composition
- Validate LangChain tracing and fixture recording
- Test golden answers for retrieval chains

**Tool Access:**
- Read, Write, Edit
- Bash (for running pytest, coverage)

**When to Use:**
- "Write unit tests for the chunking module"
- "Create integration tests for the crawl pipeline"
- "Design an eval harness for retrieval quality"
- "Add chaos tests for job coordinator retries"
- "Write unit tests for LangChain pgvector retriever"
- "Create integration test for hybrid search LCEL chain"
- "Validate tracing IDs in contract tests"
- "Test retriever chain outputs against golden answers"

**System Prompt Focus:**
- pytest framework and fixtures
- Test design patterns (AAA, Given-When-Then)
- Coverage measurement and analysis
- Retrieval evaluation metrics (NDCG, MRR)
- LangChain testing patterns (retriever tests, chain tests)
- Fixture recording and golden answer validation

---

## 13. Deployment & DevOps Engineer

**Purpose:** Handles Docker, CI/CD, and operational tooling.

**Key Responsibilities:**
- Design Dockerfile and docker-compose.yml
- Write deployment scripts and health checks
- Implement database bootstrap automation
- Create smoke tests for deployments
- Design logging and telemetry (structured JSON logs)
- Build disaster recovery procedures

**Tool Access:**
- Read, Write, Edit
- Bash (for Docker commands, deployment scripts)

**When to Use:**
- "Create a Dockerfile for Amelia"
- "Design docker-compose for local development"
- "Add health checks and smoke tests"
- "Implement structured logging with trace IDs"

**System Prompt Focus:**
- Docker and docker-compose
- PostgreSQL initialization scripts
- Health check design
- Structured logging (JSON, trace IDs)

---

## 14. Documentation Writer

**Purpose:** Creates and maintains project documentation.

**Key Responsibilities:**
- Write API documentation for MCP tools
- Create setup and configuration guides
- Document troubleshooting procedures
- Write code examples and tutorials
- Maintain architecture diagrams
- Update README and changelog

**Tool Access:**
- Read, Write, Edit
- WebFetch (for documentation best practices)

**When to Use:**
- "Document the search_documents MCP tool"
- "Write a troubleshooting guide for common errors"
- "Create setup instructions for Docker deployment"
- "Update the README with new features"

**System Prompt Focus:**
- Technical writing clarity
- Markdown formatting
- Documentation structure and navigation
- Code example quality

---

## 15. Multi-Language BM25 Specialist

**Purpose:** Handles language detection and BM25 text search configuration.

**Key Responsibilities:**
- Implement language detection from Whisper
- Map ISO language codes to PostgreSQL regconfig
- Design BM25 trigger with dynamic language selection
- Handle fallback to English for unknown languages
- Test BM25 indexing across multiple languages
- Document supported language configurations

**Tool Access:**
- Read, Write, Edit
- Bash (for testing PostgreSQL text search)

**When to Use:**
- "Implement the BM25 trigger with language detection"
- "Map Whisper language codes to PostgreSQL configs"
- "Test BM25 search quality for Spanish content"
- "Add support for new text search languages"

**System Prompt Focus:**
- PostgreSQL text search configurations
- Language stemming and tokenization
- ISO language code standards
- BM25 algorithm fundamentals

---

## 16. LangChain Integration Specialist

**Purpose:** Manages LangChain framework integration across the Amelia RAG pipeline.

**Key Responsibilities:**
- Design and implement LCEL (LangChain Expression Language) chains for retrieval workflows
- Build custom LangChain retrievers wrapping pgvector and BM25 backends
- Integrate cross-encoder rerankers as LangChain components
- Implement `tool_router` module for MCP tool orchestration within chains
- Configure LangChain tracing and observability (LangSmith integration)
- Propagate trace IDs to structured logs and database tables (jobs, search_requests)
- Design batching and streaming patterns for efficient retrieval
- Bridge RAG algorithms to MCP tools via LangChain pipeline
- Write LangChain-specific unit and integration tests
- Optimize chain composition for latency and memory efficiency

**Note:** The TDD states "All MCP search requests go through this LangChain pipeline—there is no fallback path—making it a first-class, mandatory dependency." This specialist is critical from Phase 1.

**Tool Access:**
- Read, Write, Edit
- Bash (for testing chains, running benchmarks)
- WebFetch (for LangChain documentation, LCEL patterns)
- Grep, Glob

**When to Use:**
- "Implement the LCEL chain for hybrid search in amelia/langchain/pipeline.py"
- "Create a custom pgvector retriever for LangChain"
- "Add LangSmith tracing to the search pipeline"
- "Design the tool_router for MCP orchestration"
- "Optimize batching in LangChain retrievers"
- "Implement the parallel vector + BM25 retriever chain"
- "Add cross-encoder reranker as LangChain component"

**System Prompt Focus:**
- LangChain Expression Language (LCEL) patterns and composition
- Custom retriever development (BaseRetriever interface)
- LangChain tracing and observability (LangSmith)
- Batching and streaming interfaces
- Chain orchestration and parallel execution
- Integration with external tools (MCP)
- LangChain testing patterns (unit tests for retrievers, integration tests for chains)

---

## How to Use These Sub-Agents

### Priority for Phase 1 (MVP)
1. **Database Schema Engineer** – critical for initial setup
2. **MCP Protocol Expert** – core functionality
3. **LangChain Integration Specialist** – mandatory pipeline infrastructure (no fallback path)
4. **Embedding Pipeline Engineer** – essential for vector search
5. **RAG Strategy Architect** – algorithm design (works with LangChain specialist)
6. **Document Parser Engineer** – needed for ingestion
7. **Testing & Quality Assurance Specialist** – ensures quality gates

**Note:** LangChain Integration Specialist is critical from Phase 1 because all MCP search requests must go through the LangChain pipeline.

### Priority for Phase 2 (Advanced RAG)
1. **RAG Strategy Architect** – algorithm design for hybrid search, contextual embeddings
2. **LangChain Integration Specialist** – LCEL chain expansion, parallel retrievers, reranker integration
3. **Chunking Strategy Specialist** – hierarchical chunking
4. **Versioning & Change Detection Expert** – incremental updates
5. **Performance Optimization Engineer** – latency improvements, LangChain chain profiling

**Note:** Heavy collaboration between RAG Strategy Architect (algorithm design) and LangChain Integration Specialist (framework implementation) in this phase.

### Priority for Phase 3 (Web & Audio)
1. **Web Crawler Engineer** – Crawl4AI integration
2. **Audio Pipeline Specialist** – Whisper transcription
3. **Job Coordinator Architect** – async job orchestration
4. **Multi-Language BM25 Specialist** – language-aware search

### Priority for Phase 4 (Polish)
1. **Performance Optimization Engineer** – final tuning
2. **Deployment & DevOps Engineer** – Docker packaging
3. **Documentation Writer** – comprehensive docs
4. **Testing & Quality Assurance Specialist** – coverage goals

---

## Creating These Sub-Agents

Use the `/agents` command in Claude Code to create each sub-agent. For example:

```
/agents
```

Then describe the sub-agent:
```
Create a "Database Schema Engineer" sub-agent that specializes in PostgreSQL
schema design, migrations, and pgvector optimization for the Amelia project.
```

Claude will generate the initial configuration. Customize:
- System prompt (use the "System Prompt Focus" section above)
- Tool access (use the "Tool Access" list above)
- Save to `.claude/agents/` for project-level access

---

## Best Practices

1. **Start with Phase 1 sub-agents** before building advanced ones
2. **Test each sub-agent** with sample tasks before relying on them
3. **Iterate on system prompts** based on output quality
4. **Limit tool access** to what's strictly necessary
5. **Version control** sub-agent configs in `.claude/agents/`
6. **Chain sub-agents** for complex workflows (e.g., Schema Engineer → Testing Specialist)
7. **Use explicit invocation** when learning what each sub-agent does well
8. **Trust automatic delegation** once sub-agents are mature

---

## Example Workflow: Implementing Hybrid Search

1. **Use RAG Strategy Architect** to design hybrid search algorithm
2. **Use Database Schema Engineer** to optimize BM25 index
3. **Use Performance Optimization Engineer** to profile and tune
4. **Use Testing & Quality Assurance Specialist** to write integration tests
5. **Use Documentation Writer** to document the feature

This demonstrates sub-agent chaining for a complete feature.

---

**Next Steps:**
1. Create the Phase 1 priority sub-agents first
2. Test them with simple tasks
3. Refine system prompts based on results
4. Build Phase 2/3/4 sub-agents as needed
5. Share successful sub-agent configs with the team
