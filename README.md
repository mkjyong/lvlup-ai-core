# lvlup-ai-core

## 인증 플로우
1. 사용자는 Google OAuth 로그인 → `/auth/google/login` 호출
   - 응답: `access_token` (Bearer), `refresh_token` 쿠키(HttpOnly)
2. Access Token 만료(15분) 시 프론트엔드는 `/auth/refresh` POST 호출
   - 쿠키의 `refresh_token` 검증 후 새로운 `access_token` 반환
3. 모든 보호 API는 `Authorization: Bearer <access_token>` 헤더 필요
4. `X-Plan-Remaining` 응답 헤더로 남은 호출 수 표시

---

## 🛠️ 프로젝트 세팅 가이드

### 1. 사전 요구 사항

| 스택 | 버전 / 비고 |
|------|-------------|
| Python | 3.11 이상 (Poetry / venv 권장) |
| PostgreSQL | 14+ (DATABASE_URL 로 접속) |
| Redis | 6+ (Celery Broker & Backend) |
| Node (선택) | API 문서/테스트용 툴 사용 시 |


### 2. 레포 클론 & 의존성 설치

```bash
# 1) 소스 클론
git clone git@github.com:my-org/lvlup-ai-core.git
cd lvlup-ai-core

# 2) 가상환경
python -m venv .venv && source .venv/bin/activate

# 3) 패키지 설치
pip install -r backend/requirements.txt
```


### 3. 환경 변수 설정

1. `backend/env.example` 파일을 복사해 `.env` 로 변경합니다.
2. **필수** 항목을 반드시 수정하세요. 비어 있으면 서버가 부팅되지 않습니다.

| Key | 설명 |
|-----|------|
| DATABASE_URL | `postgresql+asyncpg://user:pass@host:5432/db` |
| EMAIL_ENC_KEY | 32-byte urlsafe_base64 (Fernet) |
| JWT_SECRET | JWT 서명 키 |
| DOMAIN_BASE_URL | ex) https://app.example.com |

기타 값들은 필요에 따라 수정하거나 그대로 사용해도 됩니다.


### 4. 데이터베이스 초기화

개발 환경에서는 `AUTO_MIGRATE=true` 로 두면 서버 기동 시 테이블이 자동 생성됩니다.

운영 환경에서는 Alembic 마이그레이션을 별도로 수행한 뒤 `AUTO_MIGRATE=false` 로 두는 것을 권장합니다.


### 5. 서버 실행

```bash
# 프로젝트 루트(lvlup-ai-core) 기준
export PYTHONPATH=.

# FastAPI (Uvicorn)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

접속: `http://localhost:8000/docs` (Swagger UI)


### 6. Celery 워커 실행 (결제 재시도 등 비동기 작업)

```bash
celery -A backend.app.tasks.worker.celery_app worker -l info
```


### 7. 테스트 실행

```bash
pytest -q backend/tests
```


### 8. 운영 체크리스트

* **쿠키 보안**: `refresh_token` → Secure + HttpOnly + SameSite=Lax 적용
* **Rate-Limit**: API Gateway or Redis 기반 초당 요청 제한 권장
* **Prometheus**: `/metrics` 엔드포인트 노출, AlertRule 정의 필요
* **로그/PII**: 이메일·JWT·Secret 자동 마스킹 확인
* **DB 커넥션**: 인스턴스 수 × 풀사이즈 ≤ DB max_conn 검증

---

# 데이터 인제스트 파이프라인 (`data_ingest`)

## 1. 개요
게임 패치 노트, 블로그, 커뮤니티 글 등 **비정형 텍스트**를 주기적으로 수집·정제하고 임베딩하여 `pgvector` 테이블 `game_knowledge` 에 저장합니다. 전처리-임베딩 로직은 `data_ingest/` 서브모듈에 있으며 Airflow DAG 으로 스케줄링하거나 CLI 로 수동 실행할 수 있습니다.

---

## 2. 의존성 설치
```bash
# 파이프라인 전용 의존성
pip install -r data_ingest/requirements.txt

# Airflow (local dev) – extra[postgres] 권장
pip install "apache-airflow[postgres]==2.7.*" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.7.2/constraints-3.11.txt"
```

---

## 3. 환경 변수 설정 (`.env`)
`data_ingest/env.example` 파일을 복사해 프로젝트 루트의 `.env` 로 저장하고 **필수 값**을 채워주세요.

| Key | 설명 | 예시 |
|-----|------|------|
| PG_CONN_STR | Postgres 연결 DSN (**pgvector 확장 필수**) | `postgresql://user:pass@localhost:5432/ingest` |
| EMBEDDING_PROVIDER | 임베딩 백엔드(`openai`\|`local`) | `openai` |
| OPENAI_API_KEY | OpenAI API Key | `sk-...` |
| OPENAI_EMBEDDING_MODEL | 임베딩 모델명 | `text-embedding-3-small` |
| OPENAI_CHAT_MODEL | LLM 분류/요약용 모델 | `gpt-4o-mini` |
| EMBED_BATCH_SIZE | OpenAI embed 호출 batch 크기 | `16` |
| QUALITY_WEIGHT_* | 품질 점수 가중치(키워드/신규성/길이/LLM) | `0.4,0.3,0.2,0.1` |
| MIN_QUALITY_SCORE | 필터 임계값(0~1) | `0.75` |
| CHUNK_SIZE | 슬라이딩 윈도우 chunk 크기(글자) | `220` |
| CHUNK_OVERLAP_RATIO | 윈도우 overlap 비율 | `0.5` |
| LOG_LEVEL | 기본 로그 레벨 | `INFO` |
| METRICS_PORT | Prometheus Exporter 포트 | `8000` |
| SENTRY_DSN | (옵션) Sentry DSN |  |
| ENVIRONMENT | `local`/`prod` 등 실행 환경 | `local` |
| REDIS_URL | (옵션) 캐시/큐 용 Redis URL | `redis://localhost:6379/0` |
| KEYWORD_FILE | 키워드 YAML 경로(사전 필터) | `/etc/keywords.yaml` |
| LOL_PATCH_INDEX_URL | LoL 패치노트 인덱스 URL |  |
| NAMU_TITLES | 나무위키 문서 제목 CSV | `리그 오브 레전드,배틀그라운드` |
| REDDIT_SUBS | Reddit Subreddit CSV | `leagueoflegends,PUBG` |

`.env` 로드 순서는 다음과 같습니다.
1. Airflow / CLI 프로세스에서 `python-dotenv` 로 자동 로드
2. 시스템 환경변수 값이 있으면 **우선** 사용

---

## 4. 데이터베이스 초기화 (pgvector)
```bash
# Postgres 16 + pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# 마이그레이션 적용
python -m data_ingest.tools.migrate  # .env 의 PG_CONN_STR 사용
```

---

## 5. 로컬 CLI 실행 예시
```bash
# 최신 LoL 패치노트 500건 파싱 & 임베딩 (병렬 4)
python -m data_ingest.scripts.adhoc_run --source lol_patch \
  --since 2024-01-01 --parallel 4 --limit 500
```

실행 시 `METRICS_PORT`(기본 8000) 로 Prometheus 지표가 노출되며 `/healthz` 로 헬스체크가 가능합니다.

---

## 6. Airflow 배포
```bash
# 1) 초기화
export AIRFLOW_HOME=$PWD/.airflow
airflow db init

# 2) 주요 변수를 .env 또는 Airflow Variables 로 설정
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# 3) DAG 폴더 추가 (plugins 필요 없음)
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/data_ingest/dags

# 4) 웹서버 & 스케줄러 기동 (개발용)
airflow users create --username admin --password admin --role Admin --email admin@example.com
airflow webserver --port 8080 &
airflow scheduler &
```

DAG 목록에 `daily_ingest`, `hourly_transcript_ingest`, `nightly_feedback_ingest` 가 표시되면 정상입니다.

---

## 7. 운영 환경 배포 팁
* **Docker Compose**: Postgres(pgvector) + Airflow + Ingest Worker 컨테이너를 하나의 네트워크로 묶어 `.env` 공유
* **휴리스틱 튜닝**: `QUALITY_WEIGHT_*`, `MIN_QUALITY_SCORE` 값을 조절하여 데이터 품질 제어
* **모니터링**: Prometheus + Grafana 대시보드(공통 지표 사용)
* **롤백 전략**: 모델 버전(`EmbeddingProvider.model_version`) 태깅 후 A/B 평가(`tools/rollout_model.py` CLI)

---