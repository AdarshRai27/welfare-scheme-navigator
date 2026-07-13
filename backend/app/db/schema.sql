-- Active the pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Table containing welfare schemes metadata, eligibility JSON, and embeddings
CREATE TABLE IF NOT EXISTS schemes (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    issuing_body VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    eligibility_rules JSONB NOT NULL,
    source_url TEXT,
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding vector(1024) -- BGE-M3 dense representation vector (1024 dimensions)
);

-- Table mapping required document types to schemes
CREATE TABLE IF NOT EXISTS scheme_documents_required (
    id SERIAL PRIMARY KEY,
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL, -- e.g., 'aadhaar', 'income_certificate'
    mandatory BOOLEAN NOT NULL DEFAULT TRUE
);

-- Audit table tracking Scrapy scrape operations and metrics
CREATE TABLE IF NOT EXISTS scrape_runs (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL, -- e.g., 'myscheme', 'up_portal'
    run_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed'
    schemes_added INTEGER NOT NULL DEFAULT 0,
    schemes_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

-- Define index on embedding vector for faster cosine distance matching
CREATE INDEX IF NOT EXISTS schemes_embedding_idx ON schemes USING hnsw (embedding vector_cosine_ops);
