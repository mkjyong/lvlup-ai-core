-- --------------------------------------------------
-- Initial schema for lvlup-ai-core (backend + data_ingest)
-- --------------------------------------------------
-- This script unifies the table definitions required by:
--   1) backend/app (SQLModel models)
--   2) data_ingest (asyncpg queries & migrations)
--
-- You can apply this script on a fresh PostgreSQL instance:
--   psql -f schema/000_init.sql $DATABASE_URL
-- --------------------------------------------------

-- Extensions -----------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- pgvector extension no longer required (embeddings moved to OpenAI Vector Store)

-- --------------------------------------------------
-- Table: plan_tier
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_tier (
    id               SERIAL PRIMARY KEY,
    name             TEXT    NOT NULL,
    price_usd        NUMERIC NOT NULL DEFAULT 0,
    prompt_limit     INT     NOT NULL DEFAULT 0,
    completion_limit INT     NOT NULL DEFAULT 0,
    weekly_request_limit   INT NOT NULL DEFAULT 0,
    monthly_request_limit  INT NOT NULL DEFAULT 0,
    special_monthly_request_limit INT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_plan_tier_name ON plan_tier(name);

-- --------------------------------------------------
-- Table: user
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS "user" (
    google_sub       TEXT PRIMARY KEY,
    email_enc        TEXT    NOT NULL,
    avatar           TEXT,
    plan_tier        TEXT    NOT NULL DEFAULT 'free',
    referral_code    TEXT UNIQUE,
    referral_credits INT     NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_referral_code ON "user"(referral_code);

-- --------------------------------------------------
-- Table: user_plan
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS user_plan (
    id               SERIAL PRIMARY KEY,
    user_google_sub  TEXT    NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    plan_tier_id     INT     NOT NULL REFERENCES plan_tier (id) ON DELETE CASCADE,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at       TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_user_plan_user ON user_plan(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_user_plan_plan ON user_plan(plan_tier_id);

-- --------------------------------------------------
-- Table: referral
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS referral (
    id                   SERIAL PRIMARY KEY,
    referrer_google_sub  TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    referred_google_sub  TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rewarded_at          TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_referral_referrer ON referral(referrer_google_sub);
CREATE INDEX IF NOT EXISTS idx_referral_referred ON referral(referred_google_sub);

-- --------------------------------------------------
-- Table: game_account
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS game_account (
    id               SERIAL PRIMARY KEY,
    user_google_sub  TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    game             TEXT NOT NULL,
    account_id       TEXT NOT NULL,
    region           TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_game_account UNIQUE(user_google_sub, game)
);
CREATE INDEX IF NOT EXISTS idx_game_account_user ON game_account(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_game_account_game ON game_account(game);

-- --------------------------------------------------
-- Table: game_asset
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS game_asset (
    id          SERIAL PRIMARY KEY,
    game        TEXT NOT NULL,
    type        TEXT NOT NULL,
    key         TEXT NOT NULL,
    image_url   TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_game_asset UNIQUE(game, type, key)
);
CREATE INDEX IF NOT EXISTS idx_game_asset_game ON game_asset(game);
CREATE INDEX IF NOT EXISTS idx_game_asset_type ON game_asset(type);

-- --------------------------------------------------
-- Table: chat_message
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_message (
    id              SERIAL PRIMARY KEY,
    user_google_sub TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    game            TEXT NOT NULL DEFAULT 'generic',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_message_user ON chat_message(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_chat_message_game ON chat_message(game);

-- --------------------------------------------------
-- Table: payment_log
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_log (
    id              SERIAL PRIMARY KEY,
    user_google_sub TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    offering_id     TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,
    amount_usd      NUMERIC NOT NULL DEFAULT 0,
    discount_usd    NUMERIC NOT NULL DEFAULT 0,
    raw_event       JSONB   NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_payment_user ON payment_log(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_payment_event ON payment_log(event_type);

-- --------------------------------------------------
-- Table: match_cache
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS match_cache (
    id              SERIAL PRIMARY KEY,
    user_google_sub TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    game            TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL,
    raw             JSONB   NOT NULL,
    ttl             TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_match_game_user UNIQUE(user_google_sub, game, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_match_cache_user ON match_cache(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_match_cache_game ON match_cache(game);

-- --------------------------------------------------
-- Table: performance_stats
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS performance_stats (
    id              SERIAL PRIMARY KEY,
    user_google_sub TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    game            TEXT NOT NULL,
    period          TEXT NOT NULL,   -- weekly | monthly
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    metrics         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_perf_stats_user ON performance_stats(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_perf_stats_period ON performance_stats(period);

-- --------------------------------------------------
-- Table: raw_data (stage-1)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_data (
    id          SERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    text        TEXT NOT NULL,
    processed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (doc_id, source)
);
CREATE INDEX IF NOT EXISTS idx_raw_data_processed_created_at ON raw_data(processed, created_at);
CREATE INDEX IF NOT EXISTS idx_raw_data_doc_source ON raw_data(doc_id, source);

-- --------------------------------------------------
-- Table: game_knowledge (vector store)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS game_knowledge (
    id          SERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    chunk_id    INT  NOT NULL,
    text        TEXT NOT NULL,
    embedding   FLOAT8[],         -- deprecated local embedding (optional)
    score       NUMERIC CHECK (score >= 0 AND score <= 1),
    metadata    JSONB,
    raw_text    TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (doc_id, chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_game_knowledge_doc ON game_knowledge(doc_id);
-- Removed ivfflat index (local vector similarity search deprecated)

-- --------------------------------------------------
-- Table: rag_feedback
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_feedback (
    id            SERIAL PRIMARY KEY,
    query         TEXT NOT NULL,
    answer        TEXT,
    chunk_ids     INT[],
    hit           BOOLEAN NOT NULL,
    model_version TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_hit_created ON rag_feedback(hit, created_at);

-- --------------------------------------------------
-- Table: review_queue
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS review_queue (
    id          SERIAL PRIMARY KEY,
    chunk_id    INT  NOT NULL,
    doc_id      TEXT NOT NULL,
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | in_progress | done
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chunk_id)
);

-- --------------------------------------------------
-- Table: crawler_state
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS crawler_state (
    source  TEXT PRIMARY KEY,
    last_ts TIMESTAMPTZ
);

-- --------------------------------------------------
-- Table: llm_usage
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_usage (
    id               SERIAL PRIMARY KEY,
    user_google_sub  TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    model            TEXT NOT NULL,
    prompt_tokens    INT  NOT NULL,
    completion_tokens INT NOT NULL,
    total_tokens     INT  NOT NULL,
    cost_usd         NUMERIC NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user ON llm_usage(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_llm_usage_model ON llm_usage(model);

-- --------------------------------------------------
-- Table: cost_snapshot
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS cost_snapshot (
    id                  SERIAL PRIMARY KEY,
    usage_id            INT REFERENCES llm_usage(id) ON DELETE SET NULL,
    model               TEXT NOT NULL,
    input_tokens        INT NOT NULL,
    output_tokens       INT NOT NULL,
    cached_input_tokens INT NOT NULL DEFAULT 0,
    cost_usd            NUMERIC NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cost_snapshot_model ON cost_snapshot(model);

-- --------------------------------------------------
-- Table: usage_limit
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_limit (
    id                  SERIAL PRIMARY KEY,
    user_google_sub     TEXT NOT NULL REFERENCES "user" (google_sub) ON DELETE CASCADE,
    plan_tier           TEXT NOT NULL,
    period_start        TIMESTAMPTZ NOT NULL,
    period_end          TIMESTAMPTZ NOT NULL,
    total_input_tokens  INT NOT NULL DEFAULT 0,
    total_output_tokens INT NOT NULL DEFAULT 0,
    total_requests      INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_limit_user ON usage_limit(user_google_sub);
CREATE INDEX IF NOT EXISTS idx_usage_limit_period ON usage_limit(period_start, period_end);

-- --------------------------------------------------
-- END OF INIT SCHEMA
-- -------------------------------------------------- 