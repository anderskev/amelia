-- Amelia database bootstrap script
-- Initializes core tables, indexes, and triggers for the local RAG stack

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents metadata
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

-- Chunk storage
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

-- Embeddings table fixed to Snowflake Arctic Embed (1024 dims)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding vector(1024) NOT NULL,
    model_name VARCHAR(255) NOT NULL DEFAULT 'snowflake-arctic-embed-l-v2.0'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Keyword search support
CREATE TABLE IF NOT EXISTS bm25_index (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    tsvector_content tsvector NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bm25_tsvector ON bm25_index USING GIN(tsvector_content);

CREATE OR REPLACE FUNCTION update_bm25_index()
RETURNS TRIGGER AS $$
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

DROP TRIGGER IF EXISTS chunks_bm25_trigger ON chunks;
CREATE TRIGGER chunks_bm25_trigger
AFTER INSERT OR UPDATE OF content, metadata ON chunks
FOR EACH ROW
EXECUTE FUNCTION update_bm25_index();

-- Crawl queue state
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

-- Job coordinator persistence
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
