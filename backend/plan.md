# Backend 서비스 개발 계획

본 문서는 `backend/repo.md`에 정의된 범위와 요구사항을 바탕으로 8주간 진행될 FastAPI 기반 백엔드 프로젝트의 상세 개발 계획을 정의합니다. 모든 일정은 1주 스프린트(칸반) 단위로 관리되며, 각 스프린트 종료 시점에 목표 **성공 기준(Definition of Done, DoD)** 충족 여부를 리뷰합니다.

---
## 1. 프로젝트 개요
* **목표**: 게임별 AI 코치 서비스를 위한 확장‧유연한 백엔드 구축
* **핵심 기능**
  1. 인증·권한(JWT) 및 사용자 관리
  2. 프롬프트·RAG·LLM 파이프라인 제공
  3. 비용 절감을 위한 캐싱/Rate-limit
  4. 장시간 비동기 작업 처리(큐 워커)
  5. 모니터링·배포 자동화(CI/CD)

---
## 2. 아키텍처 하이라이트
| Layer | 주요 구성 | 기술 스택 |
|-------|-----------|-----------|
| API    | REST `/auth`, `/api/coach`, `/admin` | FastAPI, Pydantic |
| Service| LLM, Prompt, RAG, Cache | OpenAI, pgvector, Redis Vector |
| Data   | PostgreSQL (asyncpg, SQLModel) | AWS RDS or Supabase |
| Queue  | Task Worker | Celery + Redis |
| Infra  | CI/CD, Observability | GitHub Actions, Docker, Prometheus |

> Diagram은 추후 `/docs/architecture.md`에 Mermaid로 작성 예정.

---
## 3. 일정(8주) 및 마일스톤

| Sprint | 주차 | 마일스톤(MS) | 목표 기능 | 주요 산출물 |
|--------|------|--------------|-----------|-------------|
| 0      | 0.5  | 준비 | CI 파이프라인, 스캐폴드 | 리포지토리 초기화, GitHub Actions 기본 워크플로 |
| 1      | 1    | MS1 | 공통 인프라 | `app/main.py`, DB 세션, 오류 핸들러 |
| 2      | 1    | MS2 | 인증 모듈 | `/auth/*` API + 테스트 |
| 3      | 1    | MS3 | LLM Wrapper & Prompt | `services/llm.py`, 템플릿 로더 |
| 4-5    | 2    | MS4 | RAG & 캐싱 | `services/rag.py`, Redis Vector Cache |
| 6      | 1    | MS5 | 비동기 워커 | Celery 워커, 샘플 태스크 |
| 7      | 1    | MS6 | 운영/통계 API | `/admin/*`, Metrics Export |
| 8      | 0.5  | 릴리스 | v0.1.0 배포 | Dockerfile, README, CHANGELOG |

총 8주 + 1주 버퍼(회고 및 개선) = **9주** 계획.

---
## 4. 세부 작업 Breakdown

### Sprint 0 – 프로젝트 부트스트랩 (0.5주)
1. Repo 초기화 및 Poetry(or pip-tools) 의존성 관리
2. ruff, black, isort 설정 + pre-commit 훅 배포
3. `docker-compose.yml` ‑ Postgres, Redis 로컬 스택
4. GitHub Actions 파이프라인 템플릿 작성

**DoD**: 로컬/CI에서 `uvicorn app.main:app` 기동 및 `/healthz` 200 OK

---
### Sprint 1 – 공통 인프라 (1주)
1. FastAPI 앱 팩토리 + Router 등록 패턴 확정
2. `config.py` ‑ env 관리 및 타입 안전 설정
3. SQLModel 세션 팩토리(`models/db.py`) + Alembic 초기화
4. 전역 예외 핸들러(HTTPError ↔ AIError) 작성
5. 구조화 로깅(JSON) 설정

**DoD**: 샘플 테이블 CRUD 테스트 통과, 커버리지 80% 유지

---
### Sprint 2 – 인증·권한 (1주)
1. Users 테이블 & Pydantic 스키마 정의
2. Google OAuth2 ID Token 검증(`services/auth_google.py`) & JWT 발급
3. `/auth/google/login` 엔드포인트 구현 (최초 로그인 시 user auto-create)
4. 인증 미들웨어 & `deps.py` 의존성 주입
5. Happy/Edge 케이스 Pytest 작성

**DoD**: 모든 `/auth/*` 요청 케이스 200/401 명확히 분기

---
### Sprint 3 – LLM & 프롬프트 (1주)
1. `services/llm.py` ─ OpenAI 호출, 지수백오프(1→2→4) 최대 3회
2. `services/prompt.py` ─ Jinja2 템플릿 관리, 변수 바인딩 & 테스트
3. 시스템 프롬프트 템플릿 초기 버전 작성(`templates/system_prompt/...`)
4. 모킹을 통한 단위 테스트(HTTPX Mock)

**DoD**: LLM 래퍼가 정상적으로 토큰·모델 파라미터 적용

---
### Sprint 4-5 – RAG 검색 & 캐싱 (2주)
1. PostgreSQL `pgvector` 확장 & 인덱스 적용 스크립트 작성
2. `services/rag.py`: 임베딩 계산 → similarity 검색(top_k=5)
3. Redis Vector Semantic Cache(유사도>0.9, TTL 28일) 구현
4. Short-TTL 캐시(sha1(question), 5분) 로직 통합
5. `/api/coach/ask` 라우터: 질문→RAG→LLM 파이프라인 연결
6. 캐시 hit/miss 로깅 및 DB `is_cached` 필드 업데이트

**DoD**: 통합 테스트 95% 이상, 캐싱으로 평균 응답 30% 단축

---
### Sprint 6 – 장시간 작업 큐 (1주)
1. Celery(Redis broker) vs RQ 평가 → 도입 결정
2. `tasks/worker.py` 워커 엔트리포인트 구현
3. 예시 태스크: 저장된 자막 요약 → DB 저장
4. `/admin/queues` 헬스체크 라우터 작성
5. retry/backoff 정책 + 실패 알림(Slack Webhook)

**DoD**: 워커에서 태스크 성공 & 재시도 로직 검증 완료

---
### Sprint 7 – 운영/통계 API (1주)
1. `/admin/stats` 비용·캐시 통계 엔드포인트
2. Prometheus metrics FastAPI 미들웨어 설치
3. Grafana 대시보드 기본 패널(LLM 호출, 캐시 hit rate)
4. 경보 룰(월 비용 임계치) 설정

**DoD**: 메트릭 확인 가능, 통계 API 200 OK

---
### Sprint 8 – 배포 및 문서화 (0.5주)
1. Dockerfile multi-stage 최적화 + 이미지 스캔(Trivy)
2. GitHub Actions 태그 트리거 → prod 배포(wkld-runner)
3. README 갱신: 로컬 실행, CI/CD 흐름, 아키텍처 다이어그램
4. CHANGELOG 및 `v0.1.0` Git Tag 생성
5. 프로젝트 회고 & 다음 분기 로드맵 초안

**DoD**: `main` → `prod` 파이프라인 완전 자동화, 신규 인력 30분 이내 온보딩 가능

---
## 5. 테스트 전략
* **단위 테스트**: pytest, httpx.AsyncClient, 평균 커버리지 80%↑ 유지
* **통합 테스트**: Docker-Compose(Service+DB+Redis)로 E2E 테스트
* **CI**: lint ▶ test ▶ build ▶ deploy 순, 병렬화(이슈 병목 제거)

---
## 6. 리스크 & 대응
| 구분 | 위험 | 완화 전략 |
|------|------|-----------|
| 일정 | LLM API Limit 증가 | 캐싱 전략 확대, 모델 파라미터 조절 |
| 비용 | GPT-4o 과금 폭증 | 프리미엄 플랜 사용자 비율 모니터링 |
| 기술 | pgvector 성능 | 인덱스 파라미터 튜닝, materialized view |
| 인력 | 백엔드 리소스 부족 | 스프린트 조정, 외부 기여자(onboarding) |

---
## 7. 커뮤니케이션 & 규칙
* 모든 PR은 1명 이상의 리뷰 승인 필수
* Slack #backend-dev 채널로 데일리 스탠드업 요약
* 스프린트 플래닝 & 회고: 매주 월/금 30분
* 중요 결정(아키텍처, 패키지 교체)는 ADR(Architecture Decision Record) 파일로 기록

---
## 8. 참고 문서
* [`backend/repo.md`](backend/repo.md) – 요구사항 및 가이드라인
* OpenAI Usage Policy, FastAPI Docs, Celery Best Practices

---
> **최종 수정:** 2025-07-21

해당 계획은 초기 버전이며, 실제 진행 상황 및 리스크에 따라 조정될 수 있습니다. 각 스프린트 시작 전 플래닝 미팅에서 세부 태스크를 재검토해 주세요. 