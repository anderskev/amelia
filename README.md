# Amelia - Local RAG for Claude Code

**Semantic search over your local documentation and web docs, right from Claude Code.**

Version: 0.1.0 (Phase 0 - In Development)
Status: 🚧 Planning Complete, Ready to Build

---

## What is Amelia?

Amelia is an MCP server that makes your documentation instantly searchable using natural language. Ask Claude Code questions about your docs, and Amelia retrieves the most relevant content using semantic search.

**Key Features** (when complete):
- 🔍 Semantic search (find by meaning, not just keywords)
- 📁 Local files (markdown, PDF, DOCX, audio)
- 🌐 Web documentation (crawl and index)
- 🏃 Fast (sub-second queries)
- 🔒 Private (runs locally, your data stays on your machine)
- 🎯 Accurate (hybrid search combining semantic + keyword matching)

---

## Quick Start

**Current Status**: Planning phase complete. Follow the implementation guide to build Amelia.

### Prerequisites

- Python 3.12+
- Docker Desktop
- Claude Code
- 4GB+ RAM

### Build It Yourself

This is a learning project! Follow the execution guide to build Amelia using parallel Claude Code subagents:

```bash
# 1. Clone the repo
git clone https://github.com/your-org/amelia.git
cd amelia

# 2. Read the execution guide
cat docs/EXECUTION_GUIDE.md

# 3. Start Phase 0 (Week 1)
# Follow docs/plans/phase-0-minimal-viable.md
# Launch parallel agents using templates in docs/agents/phase-0/

# 4. Build incrementally
# Phase 0 (Week 1): Minimal viable search
# Phase 1 (Weeks 2-3): Daily-usable tool
# Phase 2 (Weeks 4-6): Advanced features
# Phase 3 (Weeks 7-8): Production polish
```

---

## Documentation

### For Builders

- **[EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md)** - How to build Amelia using parallel subagents
- **[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Overview of the optimized plan

### Phase Plans

- **[Phase 0: Minimal Viable](docs/plans/phase-0-minimal-viable.md)** (Week 1) - Get something working
- **[Phase 1: Daily-Usable](docs/plans/phase-1-daily-usable.md)** (Weeks 2-3) - Build a tool you use every day
- **[Phase 2: Advanced Features](docs/plans/phase-2-advanced-features.md)** (Weeks 4-6) - Production quality
- **[Phase 3: Production Polish](docs/plans/phase-3-production-polish.md)** (Weeks 7-8) - Team-shareable

### Agent Task Templates

Located in `docs/agents/phase-X/`:
- Detailed specifications for each development track
- Code examples and acceptance criteria
- Testing checklists and validation commands
- Common issues and solutions

### Original Design Docs

- **[PRD.md](docs/prd.md)** - Product requirements
- **[TDD.md](docs/tdd.md)** - Original technical design (comprehensive reference)

---

## Project Goals

This project serves three purposes:

1. **Personal utility**: Build a tool for your own development workflow
2. **Learning**: Understand RAG, embeddings, vector search, MCP, and more
3. **Team sharing**: Create something others can learn from and use

The implementation plan is optimized for all three goals.

---

## Technology Stack

**Core**:
- **MCP**: FastMCP v2 (Model Context Protocol)
- **Database**: PostgreSQL + pgvector (vector similarity search)
- **Embeddings**: Snowflake Arctic Embed L (1024 dims, local)
- **Language**: Python 3.12+

**Phase 1+**:
- Web crawling: aiohttp + BeautifulSoup
- Hybrid search: PostgreSQL full-text search (BM25)

**Phase 2+**:
- Browser automation: Crawl4AI + Playwright
- Audio transcription: faster-whisper (Whisper Turbo)
- Document parsing: pypdf2, python-docx

**Phase 3+**:
- Testing: pytest + pytest-asyncio
- Deployment: Docker Compose
- Monitoring: Structured logging (JSON)

---

## Timeline

**Total: 8 weeks** (optimized from original 10-14 weeks)

- **Week 1** (Phase 0): Minimal viable search
- **Weeks 2-3** (Phase 1): Daily-usable tool with web crawling
- **Weeks 4-6** (Phase 2): Advanced RAG features
- **Weeks 7-8** (Phase 3): Production polish and team onboarding

**Execution model**: Single developer orchestrating 3-4 parallel Claude Code subagents

---

## Architecture (Final)

```
Claude Code
    ↓ (MCP Protocol)
Amelia MCP Server
    ├─ Document Processor (local files, web, audio)
    ├─ Embedding Manager (Snowflake Arctic Embed)
    ├─ RAG Engine (hybrid search: vector + BM25)
    └─ PostgreSQL + pgvector (vector database)
```

---

## Example Usage (When Complete)

### From Claude Code

```
You: Index my documentation folder
Claude: [Calls amelia.ingest_documents]
Amelia: Indexed 127 files (1,456 chunks) in ~/projects/myapp/docs

You: Crawl the FastAPI documentation
Claude: [Calls amelia.crawl_website]
Amelia: Crawled 243 pages from https://fastapi.tiangolo.com

You: How do we handle authentication in our API?
Claude: [Calls amelia.search_documents]
Amelia: [Returns relevant chunks from your docs]
Claude: Based on your documentation, authentication is handled using...
```

### From CLI

```bash
# Index local docs
amelia ingest ~/projects/docs --collection my-docs

# Crawl web docs
amelia crawl https://docs.python.org --collection python-docs

# Search
amelia search "async await" --collection python-docs

# Manage collections
amelia list-collections
amelia stats --collection my-docs
```

---

## Let's Build! 🚀

This project is optimized for learning by doing. Follow the execution guide, launch your parallel agents, and build a production-quality RAG system while mastering cutting-edge technologies.

**Ready?** Start with `docs/EXECUTION_GUIDE.md` and launch Phase 0!

---

_Built with Claude Code • Powered by MCP • Designed for Learning_
