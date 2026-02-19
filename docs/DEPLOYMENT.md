# Deployment Runbook

이 문서는 `blog.midagedev.com` 운영 배포를 빠르게 복구/점검하기 위한 런북입니다.

## 1. 배포 구조

- Build: GitHub Actions (`.github/workflows/deploy-cloudflare-pages.yml`)
- Host: Cloudflare Pages project `twi-archive-blog`
- Domain: `blog.midagedev.com`
- DNS: `blog` CNAME -> `twi-archive-blog.pages.dev` (Proxied)

## 2. 정상 동작 체크

1. GitHub Actions `Deploy Cloudflare Pages` 성공
2. Cloudflare Pages 최신 deployment가 `production`으로 반영
3. `https://blog.midagedev.com` 응답이 `200`

빠른 확인 명령:

```bash
curl -I -L https://blog.midagedev.com/
```

## 3. 실패 시 우선 점검

### GitHub Actions 인증 실패

- 저장소 시크릿 존재 여부 확인
  - `CLOUDFLARE_API_KEY`
  - `CLOUDFLARE_EMAIL`
  - `CLOUDFLARE_ACCOUNT_ID`
- 키/토큰 교체 후 시크릿도 즉시 갱신

### 배포 성공인데 도메인 반영 안 됨

- Cloudflare Pages 프로젝트에서 커스텀 도메인 상태가 `active`인지 확인
- DNS 레코드가 아래와 동일한지 확인
  - Type: `CNAME`
  - Name: `blog`
  - Target: `twi-archive-blog.pages.dev`

### canonical URL 불일치

- 배포 워크플로 빌드 환경변수 `SITE_URL=https://blog.midagedev.com` 확인

## 4. 수동 배포(비상)

```bash
cd /Users/hckim/Documents/twi/blog
SITE_URL=https://blog.midagedev.com npm run build
cd /Users/hckim/Documents/twi
npx wrangler@4.65.0 pages deploy blog/dist --project-name twi-archive-blog --branch main
```

## 5. 보안 권장

- 가능하면 Global API Key 대신 scoped API Token 사용
- 키가 노출되면 즉시 폐기(rotate) 후 GitHub 시크릿 동시 갱신
