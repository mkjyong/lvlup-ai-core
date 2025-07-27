-- Add raw_text column to game_knowledge for storing original paragraph before compression
ALTER TABLE IF NOT EXISTS game_knowledge
    ADD COLUMN IF NOT EXISTS raw_text TEXT; 