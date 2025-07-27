# 🎮 Gamer-Centric Frontend SPA – Critical Project Plan

> **Revision Date:** 2025-07-23  
> **Author:** DevAgent (Senior Full-Stack / UI·UX Expert)

---

## 1. Vision & Goals

| Goal | Success Metric |
|------|---------------|
| AI 코치 챗 경험 최적화 | 평균 응답 지연 ≤ 150 ms (프론트 측) |
| 게이머 친화 UI (네온 다크) | 사용성 테스트 SUS ≥ 85 |
| 접근성 보장 | WCAG 2.1 AA 100 % 통과 |
| 성능 최적화 | LCP < 2 s, CLS < 0.1 (모든 6 주요 페이지) |
| 품질 보증 | 테스트 커버리지 ≥ 80 % & E2E critical path 100 % 녹색 |

---

## 2. Scope

### **In Scope (MVP)**
1. **Auth Flow** – 이메일/비밀번호 + 대기열식 소셜 확장용 훅(Discord, Twitch)
2. **Chat Flow** – 실시간 질문 → 스트리밍 답변(Chunk render)
3. **History** – 무한 스크롤, 삭제/북마크, 게임 필터
4. **Settings** – 프로필, 테마, 언어 (ko/en) 스위치
5. **PWA & Offline Shell** – 캐시 전략 (BG Sync fallback)

### **Out of Scope (Phase 2+)**
- WebSocket 전환 (현재 SSE fallback)  
- 프리미엄 결제(Stripe)  
- 실시간 친구 초대 & 파티 챗  
- 멀티모달(음성/이미지) 입력

---

## 3. Technical Architecture

```mermaid
graph TD;
  UI[React 18 + Vite 5 SPA] --> Router[react-router-dom v6.22]
  UI --> State[Recoil minimal atoms]
  State --> Cache[IndexedDB via idb-keyval]
  UI --> API[axios client]
  API --> Auth[JWT + Refresh Token]
  API --> Coach[/api/coach/*]
  UI --> SW[Workbox Service Worker]
  SW --> |Stale-While-Revalidate| Cache
```

### Key Decisions
- **CSR+PWA** 선택: 게임 커뮤니티 → 실시간 상호작용 비중 ↑, 오프라인 접근 필요.
- **Recoil vs Redux**: 전역 상태 작음, 보일러플레이트 최소화.
- **TailwindCSS** + CSS Variables 토큰: 빠른 시제품 + 다크/라이트 전환 용이.

---

## 4. Design System (Dark Neon)

| Token | HEX | 사용처 |
|-------|-----|-------|
| `--color-bg` | `#080B12` | Root 배경 |
| `--color-surface` | `#0F1420` | Card / Panel |
| `--color-primary` | `#00B3FF` | Accent (버튼, 링크) |
| `--color-secondary` | `#FF006A` | Accent 2 (토글, 강조) |
| `--color-text` | `#E0E6F6` | 본문 텍스트 |
| `--color-muted` | `#8892B0` | 부 텍스트 |
| `--color-border` | `#1E2538` | 선 / 구분선 |

Font Stack:  
- Headings → `Orbitron`, fallback `sans-serif`  
- Body → `Inter`, fallback `system-ui`

---

## 5. Implementation Roadmap (4 Weeks)

| Week | Focus | Deliverables | Review Gate |
|------|-------|-------------|-------------|
| **1** | 🏗 Project Bootstrap | Vite + TS strict, Tailwind setup, SW scaffold, CI(Lint/Vitest) | Build passes, Lighthouse perf > 90 |
| **2** | 🔐 Auth + API Layer | AuthPage, axios interceptor, Refresh logic, MSW unit tests | E2E Auth flow green |
| **3** | 💬 Chat + History | ChatPage progressive render, HistoryPage infinite scroll, GameToggle | p95 render delay < 150 ms |
| **4** | ⚙️ Settings + PWA | Theme/i18n, offline shell, Sentry, Playwright E2E suite | Coverage ≥ 80 %, Core Web Vitals target met |

> **Continuous:** Daily stand-ups, code review policy(2 approvals), weekly retrospective.

---

## 6. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenAI rate-limit / cost | Medium | Medium | Cached embeddings, SWR strategy, fallback model |
| Dark theme contrast 문제 | High | Low | Contrast checker CI job + manual a11y QA |
| Mobile keyboard viewport bug | Medium | Medium | Use visual viewport API, E2E mobile tests |
| Token expiry edge cases | Medium | Medium | Axios queue suspension + retry strategy |
| Recoil state explosion | Low | Low | Strict atom design guide + ESLint plugin |

---

## 7. Open Questions
1. **Brand — 네온 팔레트 확정?**  → UI/UX 팀 리뷰 필요.
2. **Multiplayer live features** 우선순위?  
3. **Deployment Target** (Netlify vs Vercel) 풍부한 Edge 함수 필요 여부.

---

## 8. Conclusion
이 계획은 **4 주 내 MVP 출시**를 달성하기 위해 범위와 위험을 통제하며, 게이머를 위한 어두운 네온 UI와 빠른 AI 코치 경험을 보장한다.  
변경 요청은 **주간 스프린트 리뷰**에서 평가·반영한다. 