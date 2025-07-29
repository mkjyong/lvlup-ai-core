# Data Ingest Service

A standalone ETL pipeline that crawls external gaming content (patch notes, blogs, wiki dumps, transcripts) → cleans & evaluates → chunks → embeds into the shared Vector Store.

---

## 1. Quick Start

### 1-A. 로컬 테스트 (Ad-hoc)

```bash
# 1) clone & create venv
python3 -m venv .venv && source .venv/bin/activate

# 2) install deps
pip install -r requirements.txt  # + any GPU/DB drivers you need

# 3) copy env & edit
cp data_ingest/env.example .env  # fill DB / API keys etc.

# 4) run an ad-hoc ingest (dry-run)
python -m data_ingest.scripts.adhoc_run run \
    --source lol_patch \
    --since 2025-01-01 \
    --parallel 4 \
    --limit 20 \
    --dry-run
```

`--dry-run` → 벡터스토어/DB 업서트 **X**. 로그만 확인해 흐름을 테스트하세요.

### 1-B. 데몬 모드 (실서비스용)

패키지를 모듈 실행형으로 띄우면 백그라운드에서 주기적으로 새 raw_data 를 처리합니다.

```bash
# 기본 설정으로 실행 (Ctrl-C 로 종료)
python -m data_ingest

# 환경변수로 동작 파라미터 오버라이드
INGEST_SOURCES=lol_patch,pubg_patch \
INGEST_LOOP_INTERVAL=600 \  # 10m
python -m data_ingest
```

* Prometheus metrics: `0.0.0.0:8000/`  
* Health-check: `0.0.0.0:8001/healthz`

데몬은 내부에서 `_process()` 코루틴을 재사용하기 때문에 Airflow / CLI 와 동일한 품질·필터 로직을 따릅니다.

---

## 2. Key Environment Variables

| var | default | 설명 |
|-----|---------|------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost/db` | raw_data, metadata 저장용 Postgres |
| `VECTOR_STORE_URL` |  | Qdrant / Weaviate / Pinecone 접속 DSN |
| `OPENAI_API_KEY` |  | LLM relevance & embedding 호출에 필요 |
| `QUALITY_*` | see `common/config.py` | 품질 스코어 가중치/임계값 |
| `PROM_PORT` | `8008` | Prometheus exporter 포트 |
| `INGEST_SOURCES` | `lol_patch,pubg_patch,namu_wiki` | 데몬 모드 – 처리할 source ID CSV |
| `INGEST_LOOP_INTERVAL` | `300` | 데몬 모드 – sweep 주기(초) |
| `INGEST_LIMIT` | `1000` | 데몬 모드 – 소스별 최대 처리 레코드 수 |
| `INGEST_PARALLEL` | `4` | 데몬 모드 – 동시 embedding 작업 수 |
| `INGEST_BATCH_SIZE` | `100` | 데몬 모드 – DB fetch batch size |
| `INGEST_DRY_RUN` | `false` | `true` → VectorStore/DB 업서트 생략, 로그만 출력 |
| `SLACK_WEBHOOK_ALERT_DATA_INGESTOR_ERR` | _optional_ | 크롤러 에러 Slack 알림 |
| `SENTRY_DSN` | _optional_ | Sentry 연동 |

모든 변수는 `.env` 또는 시스템 환경변수로 주입됩니다.

---

## 3. Data Sources

| source id | crawler entry | 비고 |
|-----------|---------------|------|
| `lol_patch` | `data_ingest.patch_notes.lol_patch.ingest_once` | 공식 LoL 패치노트 |
| `pubg_patch` | `data_ingest.patch_notes.pubg_patch.ingest_once` | PUBG 패치노트 |
| `namu_wiki` | (비활성) | 현재 크롤러 제거됨 → DAG에서 제거 권장 |
| `reddit_tips` | `data_ingest.blogs.*` | Reddit post Tips |

새 소스를 추가하려면 `data_ingest/sources/` 아래에 `FooCrawler` 구현 후 DAG 목록에 아이디를 넣으면 됩니다.

---

## 4. Scheduled Pipelines (Airflow)

```
./infra/airflow/
```

```bash
# init Airflow (SQLite backend for local ≪ test only ≫)
export AIRFLOW_HOME=$(pwd)/.airflow
pip install apache-airflow==2.9.*
airflow db init

# create user
airflow users create -u admin -p admin -r Admin -e you@example.com -f Dev -l User

# trigger daily ingest DAG once
airflow dags trigger daily_ingest
```

DAG 구성:
* `daily_ingest` – 매일 04:00 UTC, 지난 24h 새 글 ingest
* `monthly_namu_dump_ingest` – 나무위키 덤프 파서 (현재 비활성화 가능)

---

## 5. Ad-hoc Ingestion

```bash
python -m data_ingest.scripts.adhoc_run run \
    --source pubg_patch \
    --since 2024-06-01 \
    --parallel 8 \
    --limit 500
```

옵션 설명:
* `--parallel` : 동시에 수행할 embedding task 수 (CPU/GPU 코어 수 고려)
* `--limit` : 처리할 `raw_data` 레코드 수 상한
* `--min-score` : 품질 cutoff 조정

---

## 6. Database Schema

DDL은 `data_ingest/migrations/*.sql` 에 존재합니다.

```bash
psql $DATABASE_URL -f data_ingest/migrations/001_init.sql
```

테스트용 SQLite 는 지원하지 않습니다 (벡터 서브쿼리 등 Postgres 전용).

---

## 7. Testing

```bash
pip install pytest pytest-asyncio
pytest data_ingest/tests -q
```

---

## 8. Troubleshooting

| symptom | 원인 / 해결 |
|---------|-------------|
| `Too Many Requests` on patch crawlers | 사이트 rate-limit → `retry` decorator or sleep 증가 |
| Vector Store upsert 실패 | `VECTOR_STORE_URL` 확인, 네트워크 접속 가능 여부 점검 |
| Sentry not capturing | `SENTRY_DSN` 미설정 혹은 네트워크 차단 |

---

## 9. Contributing

1. Black + Ruff 로 코드 포맷팅: `ruff check . --fix && black .`
2. 기능 추가 시 unit-test & docstring 필수
3. PR 템플릿 따라 설명 작성

---

© 2025 LvlUp-AI Data Ingest Team. 라이선스: MIT
