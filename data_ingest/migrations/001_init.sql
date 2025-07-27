CREATE EXTENSION IF NOT EXISTS "pgvector";

-- --------------------------------------------------
-- Table: raw_data
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_data (
    id SERIAL PRIMARY KEY,
    doc_id TEXT NOT NULL,
    source TEXT NOT NULL,
    text TEXT NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (doc_id, source)
);

CREATE INDEX IF NOT EXISTS idx_raw_data_processed_created_at
    ON raw_data (processed, created_at);

-- --------------------------------------------------
-- Table: game_knowledge
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS game_knowledge (
    doc_id TEXT NOT NULL,
    chunk_id INT NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    score NUMERIC CHECK (score >= 0 AND score <= 1),
    metadata JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (doc_id, chunk_id)
);

-- Vector index for similarity search (L2 distance)
CREATE INDEX IF NOT EXISTS idx_game_knowledge_embedding
    ON game_knowledge USING ivfflat (embedding vector_l2_ops); 