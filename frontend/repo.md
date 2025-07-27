# frontend

React + Vite + **TypeScript** 기반 SPA 클라이언트.

## 핵심 화면 (MVP)
1. **AuthPage** – 이메일/비밀번호 로그인·회원가입
2. **ChatPage** – 질문 입력, AI 답변, 로딩, 토스트 알림
3. **HistoryPage** – 질문/답변 목록, 무한 스크롤
4. **SettingsPage** – 프로필, 테마, 프리미엄 업그레이드

## 디렉터리 구조(예시)
```
src/
  pages/
    AuthPage.tsx
    ChatPage.tsx
    HistoryPage.tsx
    SettingsPage.tsx
  components/
    ChatBubble.tsx
    GameToggle.tsx
    MarkdownViewer.tsx
  hooks/
    useAuth.ts
    useCoachApi.ts
  store/
    index.ts        # Recoil root atoms/selectors
  api/
    client.ts       # axios 인스턴스 + interceptor(JWT)
  utils/
    formatTime.ts
    copyToClipboard.ts
  styles/
    tailwind.css
  i18n/
    ko.json
    en.json
```

## 기술 스택 & 라이브러리
- React 18 + Vite 5, TypeScript 5
- State 관리: **Recoil** (소규모·반응형)
- 라우터: `react-router-dom` v6.22 (SPA)
- HTTP: **axios** + interceptor ➜ JWT 자동 첨부 & 401 리프레시
- UI 스타일: **Tailwind CSS** + **Headless UI**
- Markdown 렌더링: `react-markdown` + `rehype-highlight`
- form 관리: `react-hook-form`
- 상태 기반 모션: `framer-motion` (로딩 애니)
- 테스팅: **Vitest** + **React Testing Library** + `msw`

## UX 지침
- **모바일 우선** 레이아웃 (flex-col → md:flex-row)
- Chat 입력: `Cmd/Ctrl+Enter` 전송, `↑` 최근 메시지 편집
- 답변 스트리밍(추후) 대비 ChatBubble 컴포넌트에서 progressive render 구현
- 오류 발생 시 토스트로 사용자 친화적 메시지 출력
- 다크·라이트 테마 토글 제공

## API 계약
| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/auth/login` | `{email, password}` | `{access_token}` |
| POST | `/api/coach/query` | `{question, game}` | `{answer}` |
| GET  | `/api/coach/history?limit=20` | - | `{items: Log[]}` |

모든 요청은 `Authorization: Bearer <token>` 헤더 필요(로그인 제외).

## CI & 품질관리
- Pre-commit: `eslint`, `prettier`, `vitest --run`
- GitHub Actions: build → vitest → Cypress e2e(추후)
- Code coverage 목표 80%

---

## 🚀 빠른 시작 (개발용)

### 1. 의존성 설치

```bash
# pnpm 사용 시 (선호)
pnpm install
# npm
npm install
```

### 2. 환경 변수 설정

```bash
cp env.example .env.local  # 또는 .env
vi .env.local  # VITE_API_BASE_URL, VITE_GOOGLE_CLIENT_ID 등 수정
```

### 3. 개발 서버 실행

```bash
npm run dev  # 브라우저 자동 오픈
# 또는
pnpm dev
```

접속: http://localhost:5173 (기본 포트)

### 4. 린트 & 테스트

```bash
npm run lint   # ESLint
npm run test   # Vitest
```

### 5. 프로덕션 빌드

```bash
npm run build  # dist/ 생성
npm run preview  # 로컬 프리뷰 서버
```

환경 변수 노트
- `VITE_` 프리픽스가 붙은 키만이 클라이언트 번들에 노출됩니다.
- 변수는 Vite 런타임(`import.meta.env.*`)에서 사용됩니다.

## 추후 확장
- WebSocket 스트리밍 응답, SSE 지원
- PWA 모드(워크박스)로 모바일 오프라인 캐싱
- i18n: `react-i18next`로 영어 UI 추가 