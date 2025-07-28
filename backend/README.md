# 🧩 AI Coach Backend

FastAPI + SQLModel + Celery 로 구성된 AI 코치 백엔드 서비스입니다. 본 문서는 **백엔드** 개발·배포·운영에 필요한 모든 정보를 다룹니다.

> 전체 시스템 아키텍처(프론트/인프라 포함)는 루트 `README.md` 를 참고하세요.

---

## 📂 프로젝트 구조

```
backend/
  app/                # FastAPI 애플리케이션
    ├─ config.py      # 환경변수 설정 (pydantic BaseSettings)
    ├─ main.py        # ASGI 엔트리포인트
    ├─ models/        # SQLModel ORM 엔티티
    ├─ services/      # 비즈니스 로직 (OAuth, 결제, LLM 등)
    ├─ routers/       # API 엔드포인트 모음
    ├─ middleware/    # FastAPI 미들웨어
    ├─ tasks/         # Celery 태스크
    ├─ templates/     # 시스템 프롬프트 Jinja2 템플릿
  tests/              # Pytest 스위트
  tools/              # 스크립트(Seed, Ingest 등)
  requirements.txt    # 런타임 의존성
  env.example         # 백엔드용 환경변수 샘플
```

---

## 🌱 빠른 시작 (개발용)

### 1. 의존성 설치

```bash
# 가상환경 준비 (권장)
python -m venv .venv && source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수

`env.example` → `.env` 로 복사 후 필수 값을 채웁니다.

필수 키 | 설명
--------|------
`DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/ai_coach`
`EMAIL_ENC_KEY` | 32-byte urlsafe_base64 (Fernet)
`JWT_SECRET` | JWT 서명용 시크릿 문자열
`REVENUECAT_API_KEY` | RevenueCat 서버 API Key
`REVENUECAT_WEBHOOK_SECRET` | RevenueCat Webhook HMAC Secret
`DOMAIN_BASE_URL` | ex) `https://app.example.com`

> **Tip**  
> `EMAIL_ENC_KEY` 생성: `python - <<'PY'
> import base64, os, binascii
> print(base64.urlsafe_b64encode(os.urandom(32)).decode())
> PY`

### 3. 서비스 실행

```bash
export PYTHONPATH=.

# FastAPI (hot-reload)
# 1) 레포 루트(lvlup-ai-core) 위치에서 실행
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 2) 혹은 backend 디렉터리 내부에서 실행
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery 워커 (결제 재시도·백그라운드 태스크)
celery -A backend.app.tasks.worker.celery_app worker -l info
```

API 문서: <http://localhost:8000/docs>

---

## Quick Start (local)

```bash
# activate venv & install deps first ...

# run dev server on port 1100
uvicorn app.main:app --reload --port 1100
```

> 기본 포트를 1100으로 사용합니다(OS 환경변수 `PORT` 미설정 시).

---

## 🏗️ 데이터베이스

### 스키마 관리

개발 단계에서는 `AUTO_MIGRATE=true` 로 두면 앱 기동 시 자동으로 `SQLModel.metadata.create_all()` 이 실행되어 테이블이 생성됩니다.

운영 환경에서는 Alembic을 사용해 버전 기반 마이그레이션을 권장합니다.

```
pip install alembic
alembic init alembic
# env.py 수정 후
alembic revision --autogenerate -m "add payment_log table"
alembic upgrade head
```

### 커넥션 풀

`DB_POOL_SIZE` (기본 5) 로 제한됩니다. 인스턴스/워크자 수 × 풀사이즈 ≤ DB `max_connections` 를 반드시 확인하세요.

---

## 🔐 인증 & 보안

1. **Google OAuth**: 프런트엔드에서 받은 `id_token` 검증 후 `access_token`·`refresh_token` 발급.
2. **JWT**: `HS256` 서명, `access_token` 30분 / `refresh_token` 14일.
3. **쿠키**: `refresh_token` → `Secure` `HttpOnly` `SameSite=Lax` (Reverse-Proxy 에서 HTTPS terminate 필요).
4. **PII 로그 마스킹**: 이메일·JWT·Secret 자동 치환.
5. **Rate-Limit**: `/middleware/quota.py` 가 월간/주간 한도, 초당 요청 제한은 API Gateway(또는 RedisLua) 측면에서 추가해야 합니다.

---

## 💳 결제 & 구독 (RevenueCat)

플로우 | 설명
-------|------
Checkout | `POST /billing/initiate` → RevenueCat `/v1/checkouts` 호출 후 `checkout_url` 반환
Webhook | RevenueCat → `POST /billing/notify` : Webhook 서명(HMAC-SHA256) 검증 후 결제/만료 처리
재시도 | Checkout 생성 실패 시 Celery 태스크가 6h 간격, 2회 재시도
취소 | `POST /billing/cancel` → 구독 취소(잔여 기간 유지)  
만료 | Webhook `EXPIRATION` 이벤트 수신 시 `plan_tier` → `free`

---

## 🧪 테스트

```bash
pytest -q tests
```

* `tests/test_*` → FastAPI `TestClient` / SQLModel `sqlite+aiosqlite:///:memory:` 사용.
* CI 예시 (GitHub Actions)
  ```yaml
  - uses: actions/setup-python@v4
    with:
      python-version: '3.11'
  - run: pip install -r backend/requirements.txt
  - run: pytest -q backend/tests
  ```

---

## 📈 모니터링

* **Prometheus**: `/metrics` 자동 노출(`prometheus_fastapi_instrumentator`).
* **Grafana Dashboards**: `LLM Usage`, `Payment Retry`, `Webhook Errors` 권장.
* **AlertRule** 예시
  * `payment_retry_total > 10` (5m) → Slack 알림
  * `quota_exceeded_total > 0` (1m) → Page

---

## 🚀 배포

1. Dockerfile 작성 또는 Uvicorn + Gunicorn (`uvicorn.workers.UvicornWorker`) multi-proc 사용.
2. 환경 변수 `.env` 마운트.
3. Gunicorn: `--worker-class uvicorn.workers.UvicornWorker -w 4 --max-requests 1000` 등.
4. Celery 워커 · Beat 는 별도 컨테이너로 실행.
5. Reverse-Proxy (Nginx / ALB) → 80/443 → Gunicorn.

---

## 🤝 컨트리뷰션

1. `pre-commit` 설치 → Black, Ruff, Isort 자동 포맷.
2. PR 설명에 **Why / What / How** 포함.
3. 테스트 통과 & 커버리지 80% 이상 유지.

---

## License

MIT © 2025 LvlUp-AI 