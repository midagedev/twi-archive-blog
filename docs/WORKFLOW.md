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

## 3. 글 작성 흐름 (에이전트 선별 전용)

1. 병렬 에이전트 리뷰로 `docs/manual_agent_selected_100.json` 준비
2. 아래 명령으로 후보/포스트 재생성

```bash
cd /Users/hckim/Documents/twi
python3 scripts/agent_curation_pipeline.py \
  --archive twitter-2026-02-14-1222227abadceeb048d368042ea1c9a5fb39fa3bb74113fbf40e59755047273a.zip \
  --selection-json docs/manual_agent_selected_100.json \
  --candidate-json docs/topic_candidates.json \
  --candidate-md docs/topic_candidates.md \
  --draft-dir blog/src/content/blog \
  --max-items 0 \
  --clean-draft-dir
```

3. `blog/src/content/blog/*.md` 내용 점검 및 필요한 수동 보강
4. 로컬 확인 (`npm run dev`, `npm run build`)
5. PR 생성 -> CI 통과 확인 -> `main` 머지
6. Cloudflare Pages 배포 확인

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
- 에이전트 선별 기반 생성 스크립트: `/Users/hckim/Documents/twi/scripts/agent_curation_pipeline.py`
- 에이전트 선별 결과 ID 목록: `/Users/hckim/Documents/twi/docs/manual_agent_selected_100.json`
- 후보 리포트(JSON/MD): `/Users/hckim/Documents/twi/docs/topic_candidates.json`, `/Users/hckim/Documents/twi/docs/topic_candidates.md`
- Astro 전역 스타일: `/Users/hckim/Documents/twi/blog/src/styles/global.css`
- 헤더: `/Users/hckim/Documents/twi/blog/src/components/Header.astro`
- 메타 태그: `/Users/hckim/Documents/twi/blog/src/components/BaseHead.astro`
- 홈(글 목록): `/Users/hckim/Documents/twi/blog/src/pages/index.astro`
- 블로그 인덱스: `/Users/hckim/Documents/twi/blog/src/pages/blog/index.astro`
- 포스트 레이아웃: `/Users/hckim/Documents/twi/blog/src/layouts/BlogPost.astro`

## 6. 제거된 구 선별 흐름

다음 파일/흐름은 더 이상 사용하지 않습니다.

- `scripts/run_codex_subagents.sh`
- `scripts/prepare_tweet_corpus.py`
- `scripts/agent_blog_pipeline.py`
- `docs/manual_include_tweet_ids.json`
- `docs/topic_shortlist.json`, `docs/topic_shortlist.md`

## 7. 테마/브랜딩 수정 포인트

- 사이트명/설명/X 링크: `/Users/hckim/Documents/twi/blog/src/consts.ts`
- 색/타이포/간격: `/Users/hckim/Documents/twi/blog/src/styles/global.css`

## 8. CI/CD 체크리스트

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

## 9. 권장 주기

- 주 1회: 초안 생성 + 발행
- 월 1회: 상단 글 재정리(타이틀/설명/태그)
