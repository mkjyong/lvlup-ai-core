-- 새 크롤러 증분 상태 저장

CREATE TABLE IF NOT EXISTS crawler_state (
    source TEXT PRIMARY KEY,
    last_ts TIMESTAMPTZ
); 