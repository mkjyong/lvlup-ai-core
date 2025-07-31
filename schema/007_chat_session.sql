-- ChatSession table for Gemini native chats
CREATE TABLE IF NOT EXISTS chat_session (
    id TEXT PRIMARY KEY,
    user_google_sub TEXT NOT NULL,
    model TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    context_cache_id TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_session_user_last ON chat_session(user_google_sub, last_used_at DESC);
