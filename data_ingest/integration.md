# 데이터 인제스트 모듈 연동 가이드 (integration.md)

본 문서는 백엔드 서비스가 `data_ingest` 파이프라인을 연동하여
게임 지식 베이스(Game-Knowledge)를 구축·갱신하기 위해 필요한 모든 정보를 정리합니다.

> ⚠️ 예시는 **로컬 개발 환경** 기준입니다. 운영 환경에 맞게 값(호스트·경로·리소스 규모 등)을 조정하세요.

---

## 1. 아키텍처 개요

```mermaid
flowchart TD
    A[원천 데이터(크롤러/백엔드)] -->|INSERT| B(raw_data 테이블)
    B -->|Airflow DAG or adhoc CLI| C[data_ingest 파이프라인]
    C -->|UPSERT| D(game_knowledge 테이블)
    C -->|Prometheus Exporter| E(Metrics)
```

1. 백엔드는 원본 텍스트(패치 노트, 게시글, 자막 등)를 **`raw_data`** 테이블에 적재합니다.
2. Airflow DAG(일간/시간별) 또는 `scripts/adhoc_run.py` CLI가 미처리(raw_data.processed=false) 레코드를 읽어
   ‑ 클린업 → 품질 점수 계산 → 문단 압축 → 임베딩 → **`game_knowledge`** UPSERT 를 수행합니다.
3. 처리 완료 시 `raw_data.processed` 가 `true` 로 변경되어 중복 처리를 방지합니다.

---

## 2. 의존성 설치

```bash
# Python 3.10+
$ pip install -r requirements.txt
```

추가로 **PostgreSQL 13+** 와 (선택) **Redis** 가 필요합니다.

---

## 3. 환경 변수 설정

`env.example` 파일을 참고하여 서비스 환경 변수 혹은 `.env` 를 구성하세요.

필수 항목

| 이름 | 설명 | 예시 |
| --- | --- | --- |
| `PG_CONN_STR` | Postgres 접속 DSN | `postgresql://user:pass@host:5432/db` |
| `OPENAI_API_KEY` | 임베딩/LLM 호출용 키 | `sk-...` |
| `OPENAI_EMBEDDING_MODEL` | 임베딩 모델명 | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | 요약/중요도 분석 Chat 모델 | `gpt-4o-mini` |
| `EMBED_BATCH_SIZE` | 임베딩 API batch size | `16` |

옵션 항목은 `env.example` 주석을 참고하세요.

### 3.1 고급 환경 변수

| 이름 | 설명 | 기본값 |
| --- | --- | --- |
| `QUALITY_WEIGHT_KEYWORD` | 키워드 가중치(품질 점수) | `0.4` |
| `QUALITY_WEIGHT_NOVELTY` | 새로움 가중치 | `0.3` |
| `QUALITY_WEIGHT_LENGTH` | 길이 가중치 | `0.2` |
| `QUALITY_WEIGHT_LLM` | LLM 중요도 가중치 | `0.1` |
| `MIN_QUALITY_SCORE` | 임베딩 최소 점수 임계값 | `0.75` |
| `CHUNK_SIZE` | 청크 길이(문자) | `220` |
| `CHUNK_OVERLAP_RATIO` | 청크 슬라이딩 윈도우 오버랩 비율 | `0.5` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `METRICS_PORT` | Prometheus exporter 포트 | `8000` |
| `SENTRY_DSN` | Sentry DSN(선택) | _(빈 문자열)_ |
| `ENVIRONMENT` | 배포 환경 태그 | `local` |
| `REDIS_URL` | Redis 연결 URL(선택) | `redis://localhost:6379/0` |
| `KEYWORD_FILE` | 키워드 필터 YAML 경로 | `/etc/keywords.yaml` |

---

## 4. 데이터베이스 준비

### 4.1 스키마 마이그레이션

최초 배포 시 다음 SQL 스크립트를 순서대로 적용하세요.

```bash
$ psql $PG_CONN_STR -f migrations/001_init.sql
$ psql $PG_CONN_STR -f migrations/002_feedback.sql
$ psql $PG_CONN_STR -f migrations/003_crawler_state.sql
$ psql $PG_CONN_STR -f migrations/004_raw_text.sql
```

(또는) `python tools/migrate.py up` 으로 일괄 실행할 수 있습니다.

### 4.2 주요 테이블 설명

| 테이블 | 용도 | 비고 |
| --- | --- | --- |
| `raw_data` | 원본 텍스트 저장, `processed` 플래그로 상태 관리 | doc_id + source 유니크 |
| `game_knowledge` | 클린·임베딩된 문단 단위 지식 | (doc_id, chunk_id) PK |
| `rag_feedback` | 검색 품질 피드백 로그 | |
| `review_queue` | 수동 검수 큐 | |

---

## 5. 백엔드 연동 방식

### 5.1 원본 데이터 적재 API 예시 (FastAPI)

```python
from data_ingest.common import db
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/ingest")
async def ingest(doc_id: str, source: str, text: str):
    try:
        await db.upsert_raw_data(doc_id=doc_id, source=source, text=text)
        return {"status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

* `doc_id` 는 소스 내에서 유니크해야 합니다. 중복 호출 시 무시되어 idempotent 합니다.
* 대량 적재가 필요한 경우 **COPY** 혹은 배치 임포트를 권장합니다.

### 5.2 파이프라인 트리거 (선택)

1. **Airflow DAG 사용**: `dags/daily_ingest.py` 등 주기성 DAG을 사용하면 자동 처리됩니다.
2. **CLI 수동 실행**: 특정 소스를 즉시 처리하고 싶다면

```bash
$ python scripts/adhoc_run.py --source video_transcripts \
                             --since 2024-01-01 \
                             --parallel 4 \
                             --limit 2000 \
                             --dry-run false
```

옵션 설명:  
`--since` 처리 시작 시각, `--parallel` 임베딩 동시 요청 수, `--limit` 최대 레코드 수, `--dry-run` DB upsert skip.

---

## 6. 메트릭 & 모니터링

파이프라인 실행 시 **Prometheus** exporter 가 `METRICS_PORT` (기본 8000) 로 기동됩니다.

주요 지표

| Metric | Label | 의미 |
| --- | --- | --- |
| `ingest_processed_total` | source | 처리된 raw_data 행 수 |
| `ingest_latency_seconds` | | fetch→upsert 전체 지연 시간 |
| `quality_score_histogram` | | 품질 점수 분포 |
| `upsert_latency_seconds` | | game_knowledge UPSERT 시간 |

---

## 7. 예외 처리 & 재시도 전략

| 단계 | 실패 시 행동 | 재시도 |
| --- | --- | --- |
| DB 연결 | 커넥션 풀에서 예외 발생 시 로그 후 5초 대기 | 무한 재시도 (Airflow 기본) |
| OpenAI API | `asyncio.TimeoutError` 또는 `RateLimitError` 시 exponential backoff | 3회 |
| game_knowledge UPSERT | 예외 시 해당 chunk 건너뜀 + `review_queue` 등록 | 수동 처리 |

---

## 8. 로컬 개발 Tip

```bash
# venv & postgres, redis 로컬 실행 예시
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
$ brew services start postgresql@15
$ docker run -d --name redis -p 6379:6379 redis:7
$ export $(grep -v '^#' env.example | xargs)   # 빠른 로컬 세팅
```

---

## 9. FAQ

**Q1. `langdetect` ImportError 발생**  
A. `pip install langdetect` (requirements.txt 포함)

**Q2. Game-Knowledge 검색/QA에 바로 반영되나요?**  
A. 파이프라인 처리 후 검색 인덱스(RAG 서비스) 재빌드가 필요합니다. 백엔드의 Ingestion Complete 이벤트를 수신하여 RAG 서버에 `/reload` 호출을 권장합니다.

**Q3. 특정 문단이 저품질로 걸러진 이유는?**  
A. [`common/scorer.py`](./common/scorer.py) 의 상세 로직과 품질 점수 histogram을 확인하세요. 가중치·임계값을 조정할 수 있습니다.

---

## 10. 운영 체크리스트 & 외부 서비스

### 10.1 Airflow 설치

```bash
$ pip install apache-airflow==2.8.*
$ export AIRFLOW_HOME=~/airflow && airflow db init
# dags/ 디렉터리를 Airflow DAG 폴더에 심볼릭 링크하거나 CI로 동기화
```

* `AIRFLOW__CORE__LOAD_EXAMPLES=false` 로 예제 DAG 로딩을 비활성화하세요.
* 운영 환경에서는 Executor를 Local → Celery/Kubernetes 로 전환할 것을 권장합니다.

### 10.2 Prometheus 스크랩 설정

```yaml
scrape_configs:
  - job_name: 'data_ingest'
    static_configs:
      - targets: ['ingest-hostname:8000']
```

### 10.3 OpenAI Rate-Limit 대응

* 429/500 오류 시 지수 Backoff(`initial=2s, factor=2, max=60s`) 로 3회 재시도합니다.
* 초당 요청 수 한도를 `--parallel` 값과 임베딩 배치 사이즈로 제어하세요.

---

## 11. 배포 & CI/CD

1. **Docker**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "scripts.adhoc_run", "--help"]
```

2. **마이그레이션 자동화**

```bash
$ python tools/migrate.py up   # idempotent, CI에서 반복 실행 가능
```

3. **SemVer 태그**로 `data_ingest@vX.Y.Z` 이미지를 빌드해 Airflow & CLI 모두 동일 버전을 사용하도록 맞춥니다.

---

## 12. 테스트/검증 지침

```bash
$ pip install -r requirements.txt -r requirements-dev.txt  # pytest 포함
$ pytest -q   # tests/ 디렉터리
```

부하 테스트 예시: 1만 행 `raw_data` 삽입 후 `adhoc_run.py --limit 10000` 실행, 처리 시간과 메모리 peak 기록.

---

## 13. 확장 FAQ

**Q4. `context_length_exceeded` OpenAI 오류가 납니다.**  
A. `compress_chunks` 호출 시 입력 길이를 `16k` 토큰 이하로 자르거나, gpt-4o 계열 모델로 업그레이드하세요.

**Q5. Postgres 벡터 인덱스는 어떻게 설정하나요?**  
A. `game_knowledge.embedding` 컬럼에 `ivfflat` 인덱스를 추천합니다.

```sql
CREATE INDEX gk_emb_idx ON game_knowledge USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Q6. Redis 연결 실패 시 파이프라인이 중단되나요?**  
A. 캐시 미스 모드로 폴백하여 파이프라인은 계속 진행됩니다(로깅만 발생).

---

문의: `#ingest-platform` 슬랙 채널 또는 `data-platform@yourcompany.com` 