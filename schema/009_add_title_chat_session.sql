-- add title column
ALTER TABLE chat_session ADD COLUMN IF NOT EXISTS title TEXT;
CREATE INDEX IF NOT EXISTS idx_chat_session_user_last ON chat_session(user_google_sub, last_used_at DESC);
