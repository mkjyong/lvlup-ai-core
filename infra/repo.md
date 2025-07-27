# infra

Terraform & GitHub Actions를 이용해 **IaC + CI/CD** 를 관리하는 레포.

## 디렉터리 스케폴드
```
terraform/
  modules/
    supabase/          # pgvector 확장, RLS 세팅
    redis/
    cloudrun_backend/
    cloudrun_worker/
  envs/
    dev/
      main.tfvars
    prod/
      main.tfvars
.github/
  workflows/
    ci.yml            # lint + tflint + terragrunt validate
    deploy.yml        # Tag → plan & apply + Cloud Build deploy
scripts/
  bootstrap.sh        # 첫 배포용 편의 스크립트
```

## 주요 자원
| 이름 | 유형 | 비고 |
|------|------|------|
| Supabase | Managed Postgres + Storage | `pgvector` 확장 ON, 비공개 네트워크
| Redis    | Render(Starter) / Upstash | TLS, eviction=allkeys-lru
| Cloud Run|  backend, worker 서비스   | CPU only, max-instances 3(dev) / 10(prod)
| Artifact Registry | Docker 이미지 저장소 | 리전: asia-northeast3
| Secret Manager | OPENAI_API_KEY 등   | GitHub OIDC → GCP SA

## 보안·운영 정책
- **OIDC** : GitHub Actions 워크플로에서 GCP 서비스 계정 권한 위임
- least privilege IAM: deploy SA 는 `cloudrun.developer`, `artifactregistry.writer` 만 부여
- Supabase RLS: `request_logs`는 row-owner만 SELECT
- Cloud Run ingress: internal & cloud load-balancing only, Cloud Armor WAF 추가(추후)

## CI 파이프라인(ci.yml)
1. checkout & setup-node → js lint/test (프론트)
2. setup-python → ruff + pytest (백엔드)
3. setup-terraform / tflint / terragrunt validate

## CD 파이프라인(deploy.yml)
1. 태그 `v*` push → GitHub OIDC로 GCP 로그인
2. Docker buildx → `asia-docker.pkg.dev/.../backend:$TAG`
3. terraform apply -auto-approve (prod)
4. gcloud run deploy (backend, worker)

## 모니터링 & 로깅
- **Cloud Logging** 수집 → Log Router ➜ BigQuery (쿼리 비용 < 10$/월 목표)
- **Prometheus** (supabase exporter, redis exporter) → Grafana Cloud 대시보드
- **Sentry** 프론트·백엔드 에러 집계, alert → Slack #alerts
- **Budget Alert**: OpenAI 월 한도 50$ 초과 시 이메일 + Slack 알림

## 환경별 변수 정책
| key | dev | prod |
|-----|-----|------|
| OPENAI_MODEL | gpt-3.5-turbo | gpt-4o |
| REDIS_SIZE   | 100MB | 1GB |
| MAX_INSTANCES| 3 | 10 |

## 향후 작업
- Terraform Cloud → drift 감지 & PR plan 적용
- Argo Rollouts로 backend canary 배포 실험 
