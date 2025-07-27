-- --------------------------------------------------
-- RAG Feedback & Review Queue Tables
-- --------------------------------------------------

CREATE TABLE IF NOT EXISTS rag_feedback (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    answer TEXT,
    chunk_ids INT[],
    hit BOOLEAN NOT NULL,
    model_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_feedback_hit_created
    ON rag_feedback (hit, created_at);

-- Review queue for low-quality chunks needing re-evaluation
CREATE TABLE IF NOT EXISTS review_queue (
    id SERIAL PRIMARY KEY,
    chunk_id INT NOT NULL,
    doc_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | in_progress | done
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_review_chunk ON review_queue(chunk_id); 