# backend

FastAPI 기반 **서비스 애플리케이션** 코드가 위치합니다.

## 주요 책임
1. REST API 및 (추후) WebSocket 제공 – `/auth`, `/api/coach`, `/admin`
2. 프롬프트 생성, RAG 검색(pgvector) 및 LLM(OpenAI) 호출
3. Semantic Cache( Redis Vector Index ) 및 Rate-limit → 비용/지연 최적화
4. 장시간 작업(Celery/RQ) 처리 – 이미 저장된 자막·텍스트 요약 등
5. 자동 테스트, 린터, 배포 파이프라인(GitHub Actions) 관리

## 디렉터리 스캐폴드(예시)
```
app/
  main.py          # FastAPI 앱 부트스트랩 & Router 등록
  deps.py          # 공통 의존성(JWT 검증, DB 세션)
  routers/
    auth_google.py # Google OAuth 로그인·JWT 발급
    billing.py     # 구독 결제·웹훅
    coach.py       # 질문 처리·히스토리 조회
    admin.py       # 운영/통계 API
  services/
    prompt.py      # 시스템·유저 프롬프트 템플릿 관리(Jinja2)
    rag.py         # 임베딩 계산, pgvector 검색, 문서 후처리
    llm.py         # OpenAI 래퍼(재시도·백오프 포함)
    cache.py       # Redis Semantic Cache & short-ttl cache
    auth.py        # 비즈니스 로직 계층의 인증 헬퍼
    revenuecat.py  # RevenueCat 구독 관리 서비스
  models/
    db.py          # asyncpg 기반 SQLModel 세션 팩토리
    schemas/       # Pydantic 응답/요청 모델
  tasks/
    worker.py      # Celery/RQ 워커 진입점
templates/
  system_prompt/   # 게임별 시스템 프롬프트(Jinja2)
  ...
 tests/
```

## 개발 지침
- **async/await** + `asyncpg` + `SQLModel` 조합 사용
- 민감 정보는 `.env`   ➜ `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`
- 서비스 모듈은 **단일 책임 원칙(SRP)** 준수
- API 스펙은 Pydantic 모델로 명시, `response_model` 활용
- 예외는 `fastapi.exception_handler` 에 통합(HTTPError ↔ AIError 매핑)
- 코드 스타일: `ruff`(lint) + `black`(format) + `isort`(import sort)

## LLM 연동 정책
| 구분 | 기본 | 프리미엄 |
|------|------|---------|
| 모델 | `gpt-3.5-turbo` | `gpt-4o` |
| max_tokens | 512 | 1024 |
| 재시도 | 지수백오프(1→2→4), 최대 3회 | 동일 |

## RAG 검색 파라미터
- `top_k = 5`, `probes = 10`
- 필터: `game`, `category`, `tags` 3개 컬럼 모두 적용
- `content` 길이 > 1200 token 시 `llm.summarize_chunk()`로 요약 후 삽입

## 캐싱 전략
1. **Short TTL** – 동일 `user_id + sha1(question)` 5분 유지(타이핑 실수 재전송 대비)
2. 로그 테이블에 `is_cached` 컬럼 기록 → 비용 모니터링

## 테스트 & CI
- `pytest` + `httpx.AsyncClient` 로 라우터 테스트
- GitHub Actions: lint ▶ test ▶ docker build ▶ deploy(태그 시)
- 코드커버리지 80% 이상 유지 

## 요금제 · 토큰 한도
| 플랜 | 모델 | 프롬프트 토큰 | 응답 토큰 | 호출 한도 |
|------|------|--------------|-----------|-----------|
| 무료 | GPT-4o-mini / o4-mini | 1 000 | 2 000 | 30회/주 (≈200회/월) |
| 베이직 | GPT-4o-mini | 2 000 | 4 000 | 200회/주 (≈800회/월) |
| 베이직(특화) | o4-mini | 2 000 | 4 000 | 100회/월 |

백엔드는 `PLAN_TOKEN_LIMITS`·`PLAN_CALL_LIMITS` 상수( `app/config.py` )를 기반으로
1) `QuotaMiddleware` – 주·월 호출 횟수 제한
2) `llm.chat_completion()` – 요청·응답 토큰 길이 제한
을 강제합니다.

응답 헤더(`/api/coach/ask`)
```
X-Cost-USD: 0.00225
X-Plan-Remaining: 162
``` 