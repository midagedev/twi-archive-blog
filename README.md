# Midage Dev Notes - Repository Guide

`/Users/hckim/Documents/twi`는 다음 두 파트로 구성됩니다.

- `twi2blog` (Python): X 아카이브 -> Markdown 변환기
- `blog` (Astro): 실제 블로그 사이트

## 프로젝트 목적

- 과거 트위터 글을 블로그 자산으로 전환해 이직/브랜딩에 활용
- 트윗 원문 복붙이 아니라 맥락, 선택, 결과를 보강한 글로 재작성

## 빠른 시작

```bash
cd /Users/hckim/Documents/twi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

cd blog
npm install
npm run dev
```

## 콘텐츠 추가 기본 루틴

1. 초안 생성

```bash
cd /Users/hckim/Documents/twi
source .venv/bin/activate
twi2blog --archive data/tweets.js --out blog/src/content/blog --min-likes 20 --min-retweets 5
```

2. 수동 편집
- `blog/src/content/blog/*.md`에서 제목, 설명, 태그, 본문 보강
- 권장 구조: `문제 -> 선택/실행 -> 결과 -> 배운 점`

3. 로컬 검증

```bash
cd /Users/hckim/Documents/twi/blog
npm run dev
SITE_URL=https://blog.midagedev.com npm run build
```

4. 배포
- 변경사항을 PR로 검토
- `main` 머지 후 GitHub Actions가 Cloudflare Pages에 자동 배포

## 배포 파이프라인 (Cloudflare Pages)

- CI: `.github/workflows/ci.yml`
  - `twi2blog` 변환 스모크 테스트
  - Astro 빌드 테스트
- CD: `.github/workflows/deploy-cloudflare-pages.yml`
  - `main`의 `blog/**` 변경 시 Cloudflare Pages(`twi-archive-blog`) 자동 배포
- 도메인:
  - Cloudflare Pages 커스텀 도메인: `blog.midagedev.com`
  - Cloudflare DNS: `blog` CNAME -> `twi-archive-blog.pages.dev`
- GitHub repository secrets:
  - `CLOUDFLARE_API_KEY`
  - `CLOUDFLARE_EMAIL`
  - `CLOUDFLARE_ACCOUNT_ID`

## 문서 인덱스

- 설정/배포: `/Users/hckim/Documents/twi/docs/SETUP.md`
- 배포 런북: `/Users/hckim/Documents/twi/docs/DEPLOYMENT.md`
- 콘텐츠 운영: `/Users/hckim/Documents/twi/docs/WORKFLOW.md`
- Astro 프로젝트 참고: `/Users/hckim/Documents/twi/blog/README.md`

## 핵심 경로

- 변환기 코드: `/Users/hckim/Documents/twi/src/twi2blog`
- 블로그 콘텐츠: `/Users/hckim/Documents/twi/blog/src/content/blog`
- 사이트 코드: `/Users/hckim/Documents/twi/blog/src`
