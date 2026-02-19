# Content & Ops Workflow

이 문서는 글 작성/관리 흐름과 주요 파일 위치를 정리합니다.

## 1. 운영 원칙

- 목표: 트위터 글을 블로그 자산으로 전환해 이직/브랜딩에 기여
- 홈은 랜딩보다 글 소비 중심
- 디자인은 미니멀(단색 배경, 저채도 UI)
- 한글 폰트는 `Pretendard`로 통일
- AI 티가 과도한 문장보다, 본인 실무 경험이 드러나는 문장을 우선

## 2. 문체 및 분량 원칙

- 최근 트위터 문체(간결, 직설, 실무 중심)를 기본 톤으로 사용
- 트윗을 블로그로 확장할 때는 맥락/판단 근거/결과를 추가
- 권장 구조: `문제 -> 선택/실행 -> 결과 -> 배운 점`
- 권장 분량: 주제별 600~1200자 이상(짧은 노트형 예외 가능)

## 3. 글 작성 흐름

기본:
1. `twi2blog`로 초안 생성
2. `blog/src/content/blog/*.md` 수동 편집
3. 로컬 확인 (`npm run dev`, `npm run build`)
4. 브랜치에서 PR 생성
5. CI 통과 확인 후 `main` 머지
6. Cloudflare Pages 자동 배포 확인

대안(권장):
1. `scripts/run_codex_subagents.sh <archive.zip>` 실행
2. `docs/topic_shortlist.md`에서 주제 우선순위 확인
3. `drafts/codex/*.md`에서 초안 선택 후 수동 보강
4. `blog/src/content/blog`로 반영 후 로컬 확인
5. PR 생성 -> CI 확인 -> `main` 머지

## 4. Markdown frontmatter 규칙

```yaml
---
title: "..."
description: "..."
pubDate: 2026-02-14
source: twitter
tags:
  - ai
  - productivity
---
```

## 5. 주요 파일 맵

- 변환기 CLI: `/Users/hckim/Documents/twi/src/twi2blog/cli.py`
- 변환기 로직: `/Users/hckim/Documents/twi/src/twi2blog/convert.py`
- Astro 전역 스타일: `/Users/hckim/Documents/twi/blog/src/styles/global.css`
- 헤더: `/Users/hckim/Documents/twi/blog/src/components/Header.astro`
- 메타 태그: `/Users/hckim/Documents/twi/blog/src/components/BaseHead.astro`
- 홈(글 목록): `/Users/hckim/Documents/twi/blog/src/pages/index.astro`
- 블로그 인덱스: `/Users/hckim/Documents/twi/blog/src/pages/blog/index.astro`
- 포스트 레이아웃: `/Users/hckim/Documents/twi/blog/src/layouts/BlogPost.astro`

## 6. 테마/브랜딩 수정 포인트

- 사이트명/설명/X 링크: `/Users/hckim/Documents/twi/blog/src/consts.ts`
- 색/타이포/간격: `/Users/hckim/Documents/twi/blog/src/styles/global.css`

## 7. CI/CD 체크리스트

PR 전:
- `npm run build` 성공
- 홈/목록/포스트 페이지 확인
- 오타/문장 톤 확인

PR 후:
- `CI` 워크플로 성공 확인 (`.github/workflows/ci.yml`)

머지 후:
- `Deploy Cloudflare Pages` 워크플로 성공 확인 (`.github/workflows/deploy-cloudflare-pages.yml`)
- `https://blog.midagedev.com` 접속 확인
- `rss.xml` 확인
- canonical host 확인 (`blog.midagedev.com`)

## 8. 권장 주기

- 주 1회: 초안 생성 + 발행
- 월 1회: 상단 글 재정리(타이틀/설명/태그)
