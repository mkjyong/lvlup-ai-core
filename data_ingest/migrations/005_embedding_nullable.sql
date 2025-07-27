-- Migration: make embedding column nullable now that we store vectors in OpenAI Vector Store
-- Apply with: psql -f 005_embedding_nullable.sql

ALTER TABLE IF EXISTS game_knowledge
    ALTER COLUMN embedding DROP NOT NULL; 