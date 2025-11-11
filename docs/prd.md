# Amelia: Local RAG for Claude Code

**A personal dev tool to search your local docs with Claude Code**

Version: 1.0
Last Updated: November 10, 2025

---

## What It Does

Amelia is a local MCP server that lets Claude Code semantically search your documentation - both local files and web content. Ask Claude questions about your docs, and it instantly finds relevant content using RAG (Retrieval-Augmented Generation).

**In short:** Your local docs AND web documentation become instantly searchable with natural language, right from Claude Code.

## Why It's Useful

**The Problem:**
- Context switching between Claude Code and documentation files kills your flow
- File system search only does keyword matching (misses semantic matches)
- You forget which file contains what
- Your runbooks, API docs, research papers, and notes are scattered everywhere
- Important documentation lives on the web (official docs, wikis, guides)

**The Solution:**
Amelia indexes your local docs AND crawls web documentation, letting Claude Code search everything semantically. Just ask "How do we handle authentication?" and Claude finds the answer across all your docs - local and web.

**Privacy:** Local files stay on your machine. Web crawling fetches public documentation. All processing and storage is local (unless you opt-in to cloud embeddings).

---

## Core Features

### 1. Semantic Document Search
- Natural language queries: "How do I deploy to production?"
- Finds semantically similar content, not just keyword matches
- Returns ranked results with relevance scores
- Works across multiple document formats and sources

### 2. Web Documentation Crawling
- Crawl documentation websites via URLs, sitemaps, or llms.txt files
- Recursive crawling of internal links with configurable depth
- Parallel and batched crawling for performance
- Browser automation via Crawl4AI for JavaScript-heavy sites
- Automatic deduplication and content normalization

### 3. Supported Sources
**Local Files:**
- Markdown (`.md`)
- Text files (`.txt`)
- PDFs (`.pdf`)
- HTML (`.html`)
- Audio files (`.mp3`, `.wav`, `.m4a`, `.flac`) - automatically transcribed

**Web Sources:**
- Direct URLs (https://docs.example.com/guide)
- Sitemaps (sitemap.xml)
- llms.txt files (documentation discovery)
- Recursive site crawling

### 4. Smart Chunking
- Respects document structure (headers, sections)
- Preserves context around matched content
- Configurable chunk sizes
- Same chunking strategy for local and web content

### 5. Local-First Privacy
- All processing happens on your machine
- Local files never leave your machine
- Web crawling fetches only public documentation
- You control where data is stored
- Optional cloud embeddings if you want better quality

### 6. Audio Transcription
- Automatic speech-to-text using OpenAI Whisper
- Supports MP3, WAV, M4A, FLAC formats
- Preserves timestamps for referencing specific moments
- 90+ language support (multilingual transcription)
- Handles podcasts, meetings, lectures, interviews
- Transcripts fully searchable like any other document

### 7. Multiple Collections
- Create separate collections for different projects
- Mix local files, web sources, and audio in same collection
- Keep work docs separate from personal research
- Easy collection management via Claude Code

### 8. MCP Integration
- Native Model Context Protocol support
- Automatic tool invocation from Claude Code
- No manual API calls needed

---

## How It Works

```
Local Docs ──┐
Web URLs  ───┤──→ Amelia indexes → PostgreSQL + pgvector (local DB)
Audio Files ─┘                              ↓
                                            ↓
Claude Code asks question → Amelia searches → Returns relevant chunks
```

**Under the hood:**

**For Local Files:**
1. Amelia scans your docs folder
2. Splits documents into smart chunks (respecting headers)
3. Generates embeddings (vector representations)
4. Stores everything in local PostgreSQL with pgvector
5. When you query via Claude Code, finds most relevant chunks
6. Claude synthesizes the answer from retrieved content

**For Web Crawling:**
1. Amelia detects URL type (sitemap, llms.txt, or regular page)
2. Crawls content using Crawl4AI (browser automation)
3. Follows internal links recursively (respects depth limits)
4. Extracts and normalizes content
5. Chunks and embeds same as local files
6. Stores in same database with source metadata
7. Deduplicates to avoid re-crawling same URLs

**For Audio Files:**
1. Amelia detects audio format (MP3, WAV, M4A, FLAC)
2. Transcribes using Whisper Turbo (via Docling's ASR pipeline)
3. Preserves timestamps in transcript markdown
4. Chunks transcript same as text documents
5. Stores with audio metadata (duration, language, format)
6. Makes entire audio content searchable by topic/keywords

---

## User Stories

**As a developer using Claude Code, I want to...**

1. **Index my docs folder**
   - "Index my documentation at ~/projects/myapp/docs"
   - Amelia recursively scans, chunks, and embeds all files
   - Reports: "Indexed 127 files (1,456 chunks) in 2m 15s"

2. **Crawl web documentation**
   - "Crawl the FastAPI documentation at https://fastapi.tiangolo.com"
   - Amelia detects sitemap, crawls recursively
   - Reports: "Crawled 243 pages (3,891 chunks) in 8m 32s"
   - All content stored locally and searchable

3. **Search across all sources**
   - "How do we handle rate limiting in the payment service?"
   - Gets relevant sections across local files AND web docs
   - No need to remember file names, URLs, or locations

4. **Filter searches by source**
   - "Search only web sources for FastAPI examples"
   - "Search only local PDFs in my research folder for attention mechanisms"
   - Narrow results by source type, file type, domain, path, or date

5. **Manage multiple collections**
   - "Create a collection called 'aws-docs' from ~/aws-documentation"
   - "Add https://docs.aws.amazon.com to my aws-docs collection"
   - Mix local files and web sources in same collection
   - Keep work docs separate from personal research

6. **Keep docs updated**
   - "Re-index my docs folder" (only re-processes changed files)
   - "Re-crawl https://docs.example.com" (fetches updated content)
   - Fast incremental updates for both local and web

7. **Get contextual results**
   - Results show section headers, source URLs/paths, relevance scores
   - Claude synthesizes answers from multiple sources (local + web)
   - Can click through to original files or web pages

8. **Index audio recordings**
   - "Index my meeting recordings folder at ~/recordings"
   - Amelia transcribes all audio files automatically
   - Reports: "Transcribed 12 audio files (2.5 hours) in 18m 45s"
   - All conversations become searchable

9. **Search across audio transcripts**
   - "Find where someone mentioned the authentication bug in our standup recordings"
   - Gets relevant sections with timestamps: [time: 12:30-13:15]
   - "Search my podcast downloads for episodes about RAG systems"
   - Mix results from text docs, web pages, and audio transcripts

10. **Get timestamp references**
   - Search results from audio include time markers
   - "The discussion happened at [time: 45:30-47:20]"
   - Jump directly to relevant moments in original recording
   - Perfect for referencing meetings, interviews, lectures

11. **Crawl with control**
   - "Crawl https://docs.example.com but only 2 levels deep"
   - "Crawl this sitemap but exclude /legacy/ pages"
   - Configure max depth, URL patterns, concurrency

12. **Work privately**
   - Local files never leave your machine
   - Web crawling only fetches public documentation
   - Audio transcription processed locally (no cloud API calls)
   - All processing and storage is local
   - Optional: Use OpenAI/Cohere embeddings for better quality

---

## Technical Overview

### Stack
- **Language:** Python 3.10+
- **Vector DB:** PostgreSQL + pgvector (local, persistent)
- **Embeddings:** Sentence Transformers (local, privacy-first)
- **Web Crawler:** Crawl4AI (browser automation)
- **Browser:** Playwright (headless Chrome/Firefox)
- **Audio Transcription:** OpenAI Whisper (via Docling ASR)
- **Audio Processing:** FFmpeg (format conversion)
- **MCP Framework:** FastMCP v2
- **Optional:** OpenAI or Cohere embeddings (better quality, requires API key)

### Architecture
```
Claude Code
    ↓ (MCP Protocol)
Amelia MCP Server
    ├─ Document Processor (scan, chunk, extract)
    ├─ Web Crawler (Crawl4AI + Playwright)
    ├─ Audio Processor (Whisper + FFmpeg)
    ├─ Embedding Manager (local or cloud)
    ├─ RAG Engine (search, rank, filter)
    └─ PostgreSQL + pgvector (vector database)
```

### MCP Tools Exposed

**1. `amelia_search`**
- Natural language search across collections
- Parameters: query, n_results, collection, filters

**2. `amelia_index_documents`**
- Index a folder into a collection (supports local files and audio)
- Parameters: folder_path, collection, recursive, file_patterns, transcription_language (optional)

**3. `amelia_crawl_website`**
- Crawl web documentation into a collection
- Parameters:
  - url: Starting URL or sitemap
  - collection: Collection name
  - max_depth: Max crawl depth (default: 3)
  - max_pages: Max pages to crawl (default: 1000)
  - follow_links: Whether to follow internal links (default: true)
  - exclude_patterns: URL patterns to exclude
  - include_patterns: Only crawl URLs matching these patterns
  - batch_size: Pages to crawl in parallel (default: 5)

**4. `amelia_list_collections`**
- List all collections with metadata

**5. `amelia_collection_info`**
- Get details about a specific collection

**6. `amelia_hybrid_search`** (Phase 1)
- Combines semantic + keyword search
- Better for specific technical terms

---

## Setup & Configuration

### Installation
```bash
pip install amelia-mcp
amelia init
```

### Claude Code Configuration
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "amelia": {
      "command": "python",
      "args": ["-m", "amelia.server"],
      "env": {
        "AMELIA_DB_PATH": "/Users/username/.amelia/db",
        "AMELIA_EMBEDDING_MODEL": "all-mpnet-base-v2"
      }
    }
  }
}
```

### Configuration File
Auto-generated at `~/.amelia/config.yaml`:

```yaml
database:
  path: ~/.amelia/postgres_data

embeddings:
  provider: sentence-transformers  # or 'openai' or 'cohere'
  model: all-mpnet-base-v2

indexing:
  chunk_size: 1000
  chunk_overlap: 200
  respect_gitignore: true

search:
  default_n_results: 5

web_crawling:
  max_depth: 3              # Maximum link depth to follow
  max_pages: 1000           # Maximum pages per crawl
  batch_size: 5             # Pages to crawl in parallel
  timeout: 30               # Timeout per page (seconds)
  user_agent: "Amelia-Bot/1.0"
  respect_robots_txt: true
  follow_external_links: false
  js_enabled: true          # Use browser automation for JS sites

audio:
  whisper_model: turbo      # turbo, base, medium, large
  language: auto            # auto-detect or specify: en, es, fr, etc.
  include_timestamps: true  # Preserve temporal markers
  gpu_enabled: false        # Use GPU for faster transcription (optional)
```

### First Run
```bash
# Index local docs (including audio files)
amelia index ~/projects/docs --collection my-docs

# Index audio recordings folder
amelia index ~/recordings --collection meeting-notes

# Crawl web docs
amelia crawl https://docs.python.org/3/ --collection python-docs

# Test it
amelia search "authentication" --collection my-docs
amelia search "budget discussion" --collection meeting-notes

# Now ask Claude Code:
# "Search my docs for authentication"
# "Search python-docs for async/await examples"
# "Find where we discussed the Q4 budget in meeting-notes"
```

---

## Performance Targets

**Query Speed:**
- P95 latency: < 500ms (collections up to 100k docs)
- Cold start: < 3s (first query after launch)

**Indexing Speed:**
- Markdown: ~100 docs/min
- PDFs: ~30 docs/min
- Web pages: ~20-40 pages/min (depends on site)
- Audio transcription: ~5-10x real-time (5 min audio = 30-60s processing)
- Incremental re-indexing: < 10% of full index time

**Resource Usage:**
- Idle: < 200MB RAM
- Active (indexing/crawling): < 800MB RAM
- Active (audio transcription): < 2GB RAM (depends on Whisper model)
- Active (searching): < 500MB RAM
- CPU: < 5% when idle, 30-60% during crawling, 40-80% during transcription

**Scalability:**
- Supports up to 100,000 documents per collection
- Multiple collections per instance
- Audio files: Handles hours of recordings efficiently

---

## Security & Privacy

**Local-First:**
- Local files never leave your machine
- Audio transcription processed locally (Whisper runs on-device)
- Web crawling fetches only public documentation
- Vector DB stored locally
- Default embeddings run locally (no API calls)
- No telemetry or analytics

**Web Crawling Privacy:**
- Only crawls publicly accessible URLs
- Respects robots.txt by default
- Configurable User-Agent identification
- All crawled content stored locally
- No tracking or cookies sent

**Optional Cloud Embeddings:**
- If you choose OpenAI/Cohere embeddings
- Document content sent to provider API
- Better quality results, but less private
- You decide the tradeoff

**Data Protection:**
- Relies on OS-level encryption (FileVault, BitLocker)
- API keys stored in environment variables
- Never commit secrets to config files

**Best Practices:**
- Don't index folders with secrets (`.env`, credentials)
- Use `.gitignore` patterns to exclude sensitive files
- Don't crawl password-protected or internal sites
- Be mindful of sensitive audio recordings (internal meetings, private calls)
- Separate collections by sensitivity level
- Use exclude_patterns to avoid crawling sensitive pages

---

## CLI Commands

**Status & Info:**
```bash
amelia status                    # Server status
amelia stats --collection <name> # Collection stats
amelia logs --tail 100          # View logs
```

**Collection Management:**
```bash
amelia index <path> --collection <name>        # Index local docs
amelia crawl <url> --collection <name>         # Crawl website
amelia reindex --collection <name>             # Re-index local
amelia recrawl <url> --collection <name>       # Re-crawl website
amelia list                                    # List collections
amelia delete --collection <name>              # Delete collection
```

**Maintenance:**
```bash
amelia backup --output ~/backups        # Backup DB
amelia restore --input ~/backups/...    # Restore
amelia optimize                         # Optimize DB
amelia cache clear                      # Clear cache
```

---

## Troubleshooting

**Slow queries?**
- Check collection size: `amelia stats --collection <name>`
- Optimize DB: `amelia optimize`
- Reduce chunk size or split large collections

**Claude Code can't connect?**
- Verify `claude_desktop_config.json` syntax
- Check AMELIA_DB_PATH exists and is writable
- Restart Claude Code

**Low quality results?**
- Try hybrid search (semantic + keyword)
- Adjust chunk size (smaller = more granular)
- Try better embedding model (mpnet or OpenAI)
- Use filters to narrow search scope

**Out of memory during indexing?**
- Reduce batch size: `amelia index --batch-size 50`
- Index in smaller batches (by subfolder)
- Close other applications

**Web crawling fails or times out?**
- Reduce batch_size: `amelia crawl --batch-size 2`
- Increase timeout: `amelia crawl --timeout 60`
- Check robots.txt isn't blocking
- Try with JavaScript disabled if site is simple HTML
- Some sites may block automated crawlers

**Crawling too slow?**
- Increase batch_size (parallel crawling)
- Disable JavaScript if not needed: `js_enabled: false`
- Reduce max_depth to limit scope
- Use sitemap URLs for faster discovery

**Duplicate pages being crawled?**
- Check URL normalization (trailing slashes, query params)
- Amelia deduplicates by URL, but parameterized URLs are treated as unique
- Use exclude_patterns to skip duplicate content patterns

**Audio transcription fails?**
- Check FFmpeg is installed: `ffmpeg -version`
- Install FFmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)
- Ensure audio file format is supported (MP3, WAV, M4A, FLAC)
- Check file isn't corrupted or DRM-protected

**Audio transcription too slow?**
- Enable GPU acceleration if available: `gpu_enabled: true` in config
- GPU provides 10-50x speedup for transcription
- Use smaller Whisper model: `whisper_model: base` instead of `turbo`
- Process audio files in smaller batches

**Poor transcription quality?**
- Try larger Whisper model: `whisper_model: medium` or `large`
- Specify language if known: `language: en` (auto-detect can be less accurate)
- Check audio quality (background noise, low bitrate can affect accuracy)
- Consider audio preprocessing (noise reduction) before ingestion

---

## Future Ideas

### Phase 1 Enhancements (Next 6 months)
- Hybrid search (semantic + keyword)
- Re-ranking for better relevance
- Web crawling via URLs, sitemaps, llms.txt (COMPLETED)
- Cohere embeddings integration
- Docker deployment option
- Smart crawl scheduling (auto-refresh stale docs)

### Phase 2 Ideas (6-12 months)
- Query expansion (generate alternative phrasings)
- Agentic RAG (multi-step retrieval)
- Multi-modal support (images, tables from web)
- Speaker diarization (identify different speakers in audio)
- Real-time audio transcription (stream processing)
- Video transcription (extract audio track)
- Collaborative collections (team sharing)
- Browser extension to save web pages to Amelia
- Incremental crawling (only fetch changed pages)
- Authentication support for private docs

### Phase 3 Wishlist (12+ months)
- Knowledge graphs (entity/relationship extraction)
- Active learning from user feedback
- IDE plugins (VSCode, JetBrains)
- Slack/Discord bots
- Fine-tuned embeddings on your domain
- Federated search across multiple Amelia instances

---

## Contributing

This is an open-source project! Contributions welcome:
- Report bugs via GitHub Issues
- Submit PRs for features or fixes
- Share feedback on what works/doesn't work
- Suggest new RAG strategies or embedding models

---

## Technical Details

### Chunking Strategy
Based on `crawl4ai-rag` implementation:
1. Split by `#` (h1) headers
2. Then by `##` (h2) headers
3. Then by `###` (h3) headers
4. Finally by character count if still too large
5. Preserve header context in each chunk
6. Respect boundaries (don't split mid-sentence or mid-code-block)

### Embedding Models

**Local (default):**
- `all-mpnet-base-v2`: High quality, 768 dimensions (default)
- `all-MiniLM-L6-v2`: Faster, 384 dimensions (lower quality)

**Cloud (optional):**
- OpenAI `text-embedding-3-small`: 1536 dimensions
- OpenAI `text-embedding-3-large`: 3072 dimensions (best quality)
- Cohere `embed-multilingual-v3.0`: Multilingual support

### Search Strategies

**Vector Search (default):**
- Semantic similarity via embeddings
- Cosine distance metric
- Returns top-k results

**Hybrid Search (Phase 1):**
- Combines vector + BM25 keyword search
- Reciprocal Rank Fusion (RRF) to merge scores
- Configurable weighting (default: 70% semantic, 30% keyword)

**Metadata Filtering:**
- Pre-filter before semantic search
- Filter by file_type, path, date, etc.
- Improves relevance and speed

---

## Data Models

**DocumentChunk:**
```python
{
  "chunk_id": "doc123-chunk0",
  "content": "Chunk text content...",
  "embedding": [0.123, -0.456, ...],
  "metadata": {
    "source_type": "local",  # or "web"
    "source_path": "/absolute/path/to/doc.md",  # for local files
    "source_url": "https://docs.example.com/guide",  # for web pages
    "domain": "docs.example.com",  # for web sources
    "file_type": "markdown",
    "chunk_index": 0,
    "headers": "## Installation > ### Prerequisites",
    "char_count": 843,
    "modified_at": "2025-11-10T10:23:45Z",
    "crawled_at": "2025-11-10T14:32:10Z"  # for web sources
  }
}
```

**SearchResult:**
```python
{
  "content": "Relevant chunk text...",
  "metadata": {...},
  "relevance_score": 0.89,
  "rank": 1
}
```

---

## License

MIT License (Open Source)

---

## Acknowledgments

Inspired by:
- `crawl4ai-rag` for chunking strategies and web crawling architecture
- Crawl4AI library for browser-based web crawling
- Claude's Model Context Protocol (MCP)
- Anthropic's vision for extensible AI tools

Built for developers who want their docs instantly accessible without sacrificing privacy.

---

**Questions? Ideas? Bugs?**
Open an issue on GitHub: [github.com/ottomator/amelia](https://github.com/ottomator/amelia)

---

END OF SIMPLIFIED PRD
