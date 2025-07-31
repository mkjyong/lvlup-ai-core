-- add session_id column to chat_message
ALTER TABLE chat_message ADD COLUMN IF NOT EXISTS session_id TEXT;
ALTER TABLE chat_message ADD CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_session(id);
CREATE INDEX IF NOT EXISTS idx_chat_msg_session ON chat_message(session_id, created_at);
