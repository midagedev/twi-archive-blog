# Setup Guide

이 문서는 `twi2blog + Astro + Cloudflare Pages` 스택의 설치/배포 설정을 정리합니다.

## 1. 로컬 환경

### Python (twi2blog)
```bash
cd /Users/hckim/Documents/twi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Node (Astro)
```bash
cd /Users/hckim/Documents/twi/blog
npm install
```

## 2. 콘텐츠 생성

X 아카이브 파일(`data/tweets.js`)을 준비한 후:

```bash
cd /Users/hckim/Documents/twi
source .venv/bin/activate
twi2blog \
  --archive data/tweets.js \
  --out blog/src/content/blog \
  --min-likes 20 \
  --min-retweets 5
```

생성 파일 위치:
- `/Users/hckim/Documents/twi/blog/src/content/blog`

## 3. 로컬 미리보기/빌드

```bash
cd /Users/hckim/Documents/twi/blog
npm run dev
SITE_URL=https://blog.midagedev.com npm run build
```

## 4. GitHub Actions 시크릿 설정 (1회)

배포 워크플로에 필요한 시크릿:
- `CLOUDFLARE_API_KEY`
- `CLOUDFLARE_EMAIL`
- `CLOUDFLARE_ACCOUNT_ID`

`gh` CLI로 설정:

```bash
cd /Users/hckim/Documents/twi
gh secret set CLOUDFLARE_API_KEY --body "<global_or_api_key>"
gh secret set CLOUDFLARE_EMAIL --body "<cloudflare_account_email>"
gh secret set CLOUDFLARE_ACCOUNT_ID --body "<cloudflare_account_id>"
```

`CLOUDFLARE_ACCOUNT_ID` 조회:

```bash
wrangler whoami
```

## 5. Cloudflare Pages 프로젝트 설정

현재 운영 프로젝트 정보:
- Project: `twi-archive-blog`
- Subdomain: `twi-archive-blog.pages.dev`
- Domain: `blog.midagedev.com`

## 6. Cloudflare DNS 설정

`blog.midagedev.com`을 Cloudflare Pages로 연결:

- Type: `CNAME`
- Name: `blog`
- Target: `twi-archive-blog.pages.dev`
- Proxy status: `Proxied` (권장)

## 7. 배포 방식

자동 배포입니다.

- PR 생성/수정 시: CI 실행 (`ci.yml`)
- `main` 머지 시: Cloudflare Pages 배포 실행 (`deploy-cloudflare-pages.yml`)

수동 실행이 필요하면 GitHub Actions 탭에서 `Deploy Cloudflare Pages` 워크플로를 `Run workflow`로 실행합니다.

## 8. 트러블슈팅

### 배포 워크플로 인증 실패
- 저장소 시크릿 값(`CLOUDFLARE_API_KEY`, `CLOUDFLARE_EMAIL`, `CLOUDFLARE_ACCOUNT_ID`) 재확인
- 토큰/키 갱신 시 GitHub 시크릿도 같이 업데이트

### 도메인 연결이 `pending`
- Cloudflare `blog` 레코드가 `CNAME -> twi-archive-blog.pages.dev`인지 확인
- Pages 프로젝트의 커스텀 도메인 상태가 `active`인지 확인

### canonical URL이 잘못됨
- 배포 워크플로 빌드 단계에서 `SITE_URL=https://blog.midagedev.com`이 들어가는지 확인
