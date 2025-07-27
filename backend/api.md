# AI 코치 백엔드 API 문서

> 최신 업데이트 2025-07-23

## 공통 정보

* **Base URL** 예시: `https://api.example.com`
* 모든 요청/응답 `Content-Type: application/json; charset=utf-8`
* 시간 ISO-8601 UTC (`2025-07-23T12:34:56Z`)
* 인증이 필요한 엔드포인트는 헤더 `Authorization: Bearer <access_token>` 포함

---

## 1. 헬스 체크

| 메서드 | URL | 인증 | 설명 | 응답 예 |
|--------|-----|------|------|--------|
| GET | `/healthz` | ❌ | 서비스 상태 확인 | `{ "status": "ok" }` |

---

## 2. 인증 / 토큰

| 단계 | 메서드 & URL | 본문 | 쿼리 | 응답 / 특이사항 |
|------|-------------|------|-------|-----------------|
| Google 로그인 | **POST** `/auth/google/login` | `{ "id_token": "…" }` | `referral_code?=`(선택) | 200 → `{ "access_token": "…", "token_type": "bearer" }` <br>• `refresh_token` 쿠키(`Path=/auth/refresh`, Max-Age 30d) |
| 토큰 재발급 (공통) | **POST** `/auth/refresh` | – | – | 동일 결과 |

> **access_token**: JWT (30분) ― 모든 보호 API에 필요
>
> **refresh_token**: Secure/HttpOnly 쿠키, 30일

---

## 3. AI 코치 기능

### 3-1. 질문/답변

| 메서드 | URL | 인증 | 본문 | 응답 | 응답 헤더 |
|--------|-----|------|------|-------|-----------|
| POST | `/api/coach/ask` | ✅ | `{ "question": "…", "game": "generic|lol|pubg", "prompt_type": "…" }` | `{ "answer": "…" }` | `X-Plan-Remaining`: 남은 월간 호출 수 |

### 3-2. 대화 기록

| 메서드 | URL | 인증 | 파라미터 | 응답 |
|--------|-----|------|----------|-------|
| GET | `/api/coach/history` | ✅ | `limit` (int, 기본 20), `game` ("generic|lol|pubg", 선택) | `{ "items": [ { "question": "…", "answer": "…", "created_at": "…" } ] }` |

---

## 4. 결제·구독 (Stripe + RevenueCat)

### 4-1. 결제 세션 생성

| POST | `/billing/initiate` | 인증 ✅ | `{ "offering_id": "monthly_basic" }` | `{ "checkout_url": "https://stripe.com/..." }` |

### 4-2. RevenueCat Webhook (서버→서버)

| POST | `/billing/notify` | RevenueCat → API | 헤더 `X-RevenueCat-Signature` | `{ "status": "ok" }` |
| 동작 |  • 결제 완료 → `user.plan_tier = "basic"` <br>• 사용자 보유 `referral_credits` 만큼 자동 할인 <br>• `PaymentLog`에 할인/실결제 기록 <br>• 최초 결제(`INITIAL_PURCHASE`)라면 추천인 크레딧 +1 |

### 4-3. 구독 취소

| POST | `/billing/cancel` | 인증 ✅ | `{ "product_id": "price_123" }` | `{ "status": "cancelled", "rc": { …RevenueCat 응답… } }` |
| 비고 | RevenueCat API 호출로 다음 갱신부터 과금 중단, 서버 내 `plan_tier`를 즉시 `free` 로 변경 |

---

## 5. 레퍼럴(추천)

| 메서드 | URL | 인증 | 설명 | 응답 |
|--------|-----|------|------|------|
| GET | `/referral/me` | ✅ | 내 레퍼럴 코드/크레딧/실적 조회 | `{ "referral_code": "ABC123", "credits": 5, "referred_count": 20 }` |

### 흐름
1. 신규 사용자가 `/auth/google/login?referral_code=ABC123` 로 가입
2. 친구가 **첫 결제** 완료 → 추천인 `referral_credits += 1`
3. 사용자가 결제할 때마다 크레딧(1 USD 단위) 자동 차감

---

## 6. 관리자(Admin)

| 메서드 | URL | 인증(별도) | 설명 |
|--------|-----|------------|------|
| GET | `/admin/stats` | Admin JWT 등 | 월간 토큰·매출 통계 |
| GET | `/admin/prompts` | – | 시스템 프롬프트 타입 목록 |

---

## 7. 주요 데이터 스키마

### 7-1. User
```jsonc
{
  "google_sub": "string",
  "email": "string",
  "avatar": "url",
  "plan_tier": "free | basic | …",
  "referral_code": "ABC123",
  "referral_credits": 5
}
```

### 7-2. PaymentLog
```jsonc
{
  "id": 1,
  "user_google_sub": "…",
  "offering_id": "monthly_basic",
  "event_type": "INITIAL_PURCHASE",
  "amount_usd": 8.0,      // 할인 후 실 결제액
  "discount_usd": 2.0,    // 레퍼럴 크레딧 사용액
  "created_at": "…"
}
```

---

## 8. 시퀀스 다이어그램

```mermaid
sequenceDiagram
  participant FE as Front-End
  participant API
  participant Google
  participant Stripe
  participant RC as RevenueCat

  FE->>Google: Google OAuth (id_token)
  FE->>API: POST /auth/google/login (id_token, referral_code?)
  API-->>FE: access_token + refresh_token(cookie)

  FE-)API: Authenticated /api/coach/ask
  API-->>FE: answer (X-Plan-Remaining)

  FE->>API: POST /billing/initiate
  API->>RC: create_checkout
  RC->>Stripe: Create Checkout Session
  API-->>FE: checkout_url
  FE->>Stripe: Redirect & Pay

  Stripe->>RC: payment_succeeded
  RC->>API: POST /billing/notify
  API: apply discount, update plan, give referral credit
```

---

### 보안 메모
* `access_token` 30분, `refresh_token` 30일
* RevenueCat Webhook HMAC 검증 필수
* CORS, Rate-limit, Quota 미들웨어 적용

---

### 문의
* 필드 확장·추가 요구 사항은 백엔드 팀에 공유 바랍니다. 