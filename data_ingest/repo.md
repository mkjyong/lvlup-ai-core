# data_ingest

외부 **게임 지식 콘텐츠**를 정제·임베딩하여 pgvector 테이블에 upsert 하는 ETL 파이프라인 모음.

## 파이프라인 단계
1. **fetch** : HTTP/API 크롤링 – 패치노트, 블로그, 이미 추출된 자막 JSON
2. **clean** : HTML → 텍스트, 불용어·중복 제거, 정규화
3. **chunk** : 200~300자(한글 기준) 크기로 슬라이딩 윈도우 분할
4. **embed** : `text-embedding-ada-002`(기본) 또는 `all-MiniLM-L6-v2` 호출
5. **upsert** : `game_knowledge` 테이블 INSERT ... ON CONFLICT UPDATE
6. **audit** : 결과 로그, 실패 시 Sentry 알림

## 코드 구조(예시)
```
patch_notes/
  lol_patch.py      # 라이엇 패치노트 RSS → DB
  pubg_patch.py
blogs/
  crawler.py        # 공략 블로그 스크랩 + 요약
video_transcripts/
  postprocess.py    # 자막 JSON → chunk & embed
common/
  embedding.py      # 모델 추상화, rate-limit backoff
  db.py             # asyncpg Connection Pool Wrapper
dags/
  daily_ingest.py   # Airflow DAG 예시
scripts/
  adhoc_run.py      # CLI 진입점 (cron/GH Actions 용)
```

## 설정 파일 예시
`.env`
```
PG_CONN_STR=postgresql://...
EMBEDDING_PROVIDER=openai    # 또는 local
CHUNK_SIZE=220               # 문자 단위
LOG_LEVEL=INFO
```

## 사용 예시
```bash
python scripts/adhoc_run.py --source lol_patch --since 2024-01-01
```
- 멀티ソ스 동시 실행 시 `--parallel 4` 옵션 제공
- CLI 모든 인자는 Airflow DAG에서도 동일하게 호출

## 빠른 시작 (개발용)

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 구성

```bash
cp env.example .env  # 루트 또는 data_ingest/ 경로에 복사
# 필수 값
vi .env  # PG_CONN_STR, OPENAI_API_KEY, OPENAI_VECTOR_STORE_ID 등 수정
```

### 3. 데이터베이스 초기화 (pgvector)

```bash
python -m data_ingest.tools.migrate up
```

### 4. 파이프라인 실행

수동 Ad-hoc 실행

```bash
python -m data_ingest.scripts.adhoc_run \
  --source lol_patch --since 2024-01-01 --parallel 4
```

Airflow 로컬 테스트

```bash
# Airflow 초기화
export AIRFLOW_HOME=$PWD/.airflow
airflow db init

# DAG 폴더 지정
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/data_ingest/dags

# 관리자 계정 생성 & 서비스 기동
airflow users create --username admin --password admin \
  --role Admin --email admin@example.com
airflow webserver --port 8080 &
airflow scheduler &
```

메트릭 확인: http://localhost:8000/metrics

## 품질 지표 & 모니터링
- 신규 문서 수, 중복률, 평균 토큰 길이
- 임베딩 실패율 < 1% 유지 (5xx 에러 자동 재시도 3회)
- pgvector upsert latency p95 < 500ms

## 향후 확장
- Dagster/Prefect 택1하여 워크플로 우아하게 관리
- 자연어 요약 품질 체크용 Rouge/LlamaIndex eval 도입
- 멀티모달 임베딩(이미지+텍스트) 적용 연구 