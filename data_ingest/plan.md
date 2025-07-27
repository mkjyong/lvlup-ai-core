# 🗺️ 데이터 인제스트 파이프라인 설계서

## 🎯 목표
- 게임 전략 노트(텍스트) 및 영상 자막을 **최소 비용으로 고품질 임베딩**하여 `pgvector` 기반 RAG 인덱스를 구축한다.
- **토큰/임베딩 비용 최적화**를 위해 *품질 점수*가 일정 임계값 이상인 문서만 저장한다.
- **1시간 주기**로 신규/변경 데이터를 자동 감지해 반영한다.

---

## 🏗️ 아키텍처 개요
```mermaid
graph TD;
    subgraph Source
        A[game_strategy_notes ✍️] -->|write| STG1
        B[video_transcripts 🎥] -->|write| STG1
        C[patch_notes RSS] -->|crawl| STG1
    end
    STG1[(raw_data)] --> CLEAN{clean\n&\nscore}
    CLEAN -->|score>=TH| CHUNK[chunk 200~300자]
    CHUNK --> EMBED[embed]
    EMBED --> UPSERT[{pgvector\n game_knowledge}]
    CLEAN -->|score<TH| REJ[✂️ drop]
    UPSERT --> AUDIT[(logs/metrics)]
```

- **STG1**: 원본 텍스트 적재(임시 테이블)
- **CLEAN & SCORE**: HTML 태그 제거, 중복/불용어 제거 후 `quality_score` 계산
- **TH**: 환경변수 `MIN_QUALITY_SCORE` (기본 0.75)
- **UPSERT**: 동일 `doc_id` 충돌 시 `embedding`, `score`, `updated_at` 갱신

---

## 🔄 파이프라인 단계 상세
| 단계 | 모듈 | 주요 로직 |
|------|------|-----------|
| **fetch** | `common/db.py` | `SELECT * FROM raw_data WHERE processed=false AND created_at>last_run` |
| **clean** | `common/cleaner.py` | BeautifulSoup, regex 정규화, 언어 감지(ko/en) |
| **score** | `common/scorer.py` | 1) 문장 길이·독창성 2) 키워드 가중치 3) LLM(classify) → 0~1 점수 |
| **chunk** | `common/chunker.py` | 220자씩 슬라이딩(50% overlap) |
| **embed** | `common/embedding.py` | OpenAI `text-embedding-3-small` (fallback: local `all-MiniLM-L6-v2`) |
| **upsert** | `common/db.py` | `INSERT ... ON CONFLICT (doc_id, chunk_id)` |
| **audit** | `common/logger.py` | pydantic 모델 → JSON → Sentry & Prometheus |

---

## 🧮 품질 점수(quality_score) 산정식
```
score = 0.4 * keyword_weight +
        0.3 * novelty_weight +
        0.2 * length_weight +
        0.1 * llm_relevance
```
- **keyword_weight**: 게임별 전략 키워드 매칭 비율
- **novelty_weight**: MinHash 기반 기존 문서와 중복률 반비례(새로울수록 ↑)
- **length_weight**: 100~1500자 사이일 때 최고점
- **llm_relevance**: LLM 분류(중요/보통/낮음 → 1/0.5/0)

`score ≥ 0.75` 일 때만 임베딩 진행.

---

## ⚙️ 스케줄링 & 오케스트레이션
- **Airflow** `dags/hourly_transcript_ingest.py`
  - Trigger: `@hourly`
  - Tasks: `extract` → `clean_score` → `chunk` → `embed` → `upsert` → `audit`
- **Daily** DAG: patch notes & blogs
- **CLI**: `python scripts/adhoc_run.py --source video_transcripts --since 2024-01-01 --parallel 4`

---

## 📊 모니터링 & 품질 지표
| Metric | Target |
|--------|--------|
| 임베딩 실패율 | < 1% |
| upsert latency p95 | < 500 ms |
| 중복률 | < 5% |
| RAG hit rate | > 80% |
| Quality score 분포 | 평균 ≥ 0.8 |

- Prometheus + Grafana 대시보드
- Sentry: failure alert, exception tracing

---

## 🛠️ TODO 리스트
- [ ] **DB**: `raw_data`, `game_knowledge` 테이블 스키마 확정 및 마이그레이션
- [ ] **common**: cleaner, scorer, chunker 모듈 구현
- [ ] **embedding**: OpenAI + local fallback, exponential backoff
- [ ] **Airflow DAG** 템플릿 2종(hourly, daily)
- [ ] **Prometheus exporter** & Grafana dashboard
- [ ] **Pytest** 단위/통합 테스트 (mock PG, mock OpenAI)
- [ ] **CI**: `ruff`, `black`, `pytest`, `mypy` 파이프라인 추가

---

## 📅 예상 일정
| 주차 | 작업 항목 |
|------|-----------|
| 1주차 | 스키마 설계, cleaner/scorer 프로토타입 |
| 2주차 | chunker, embedding 모듈, Upsert 로직 |
| 3주차 | Airflow DAG + 모니터링 스택 구축 |
| 4주차 | 테스트 커버리지 80% 달성 & 리팩터링 |

---

## 🚀 향후 개선
- Dagster/Prefect로 오케스트레이션 전환 평가
- LlamaIndex / Haystack로 **semantic cache** 도입
- 멀티모달(이미지+텍스트) 임베딩 연구(Clip, FLAVA) 