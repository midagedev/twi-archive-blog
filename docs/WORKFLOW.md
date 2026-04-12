# Content & Ops Workflow

이 문서는 X 글 수집, 선별, 노트 발행 흐름과 주요 파일 위치를 정리합니다.

## 1. 운영 원칙

- 목표: X/Twitter 글 중 실무 판단이 담긴 것만 선별해 짧은 엔지니어링 노트로 보존
- 홈은 랜딩보다 노트 소비 중심
- 디자인은 미니멀(단색 배경, 저채도 UI)
- 한글 폰트는 `Pretendard`로 통일
- AI는 작가가 아니라 편집자/아카이비스트로 사용
- 원문에 있는 실무 경험, 판단, 농담, 거친 리듬을 가능한 한 보존

## 2. 문체 및 AI 사용 원칙

- 최근 트위터 문체(간결, 직설, 실무 중심)를 기본 톤으로 사용
- 트윗을 기본 단위로 발행하고, 억지로 600~1200자 글로 늘리지 않음
- 에이전트는 수집, 중복 제거, 주제 묶기, 태그 정리, 저신호 글 제거에 집중
- 문장을 새로 쓰거나 확장할 때는 명시적으로 요청한 경우에만 수행
- 최종 콘텐츠는 개인 X 글의 어투를 보존해야 하며, 일반적인 AI식 에세이 문장을 피함

## 3. 과거 아카이브 흐름

1. 병렬 에이전트 리뷰로 `docs/manual_agent_selected_100.json` 준비
2. 아래 명령으로 후보/노트 재생성

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

3. `blog/src/content/blog/*.md` 내용 점검
4. 로컬 확인 (`npm run dev`, `npm run build`)
5. PR 생성 -> CI 통과 확인 -> `main` 머지
6. Cloudflare Pages 배포 확인

## 3.1 X HAR로 최근 글 가져오기

공식 API를 쓰지 않고 최근 공개 글만 1회성으로 가져올 때는 브라우저 HAR를 사용합니다. HAR에는 쿠키/세션 정보가 포함될 수 있으므로 커밋하지 않습니다(`*.har`는 gitignore 처리).

1. 브라우저에서 X에 로그인
2. 검색 페이지 열기: `from:midagedev since:2026-02-10`
3. `Latest` 탭에서 마지막 작성 기준 이전 날짜가 보일 때까지 스크롤
4. 개발자 도구 `Network` 탭에서 `Save all as HAR with content`로 `data/x_recent.har` 저장
5. 먼저 dry-run으로 확인

```bash
cd /Users/hckim/Documents/twi
python3 scripts/import_x_har.py --har data/x_recent.har --dry-run
```

6. 결과가 맞으면 Markdown 생성

```bash
python3 scripts/import_x_har.py --har data/x_recent.har --since-date 2026-02-20
cd blog
npm run build
```

기본 동작은 `blog/src/content/blog`의 최신 `pubDate` 이후 글만 가져오고, 이미 존재하는 `originalTweetUrl`의 tweet id는 건너뜁니다. 날짜 기준을 직접 지정하려면 `--since-date 2026-02-20`, 전체를 다시 훑으려면 `--since-date none`을 사용합니다.

가져온 뒤에는 병렬 selector/merger 리뷰로 발행 대상을 줄입니다. 2026-04-12 수집분은 `docs/recent_agent_shortlist_20260412.json`과 `docs/recent_agent_shortlist_20260412.md`를 기준으로 71개 중 43개만 남겼습니다.

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
- 최근 X HAR 가져오기 스크립트: `/Users/hckim/Documents/twi/scripts/import_x_har.py`
- 에이전트 선별 결과 ID 목록: `/Users/hckim/Documents/twi/docs/manual_agent_selected_100.json`
- 후보 리포트(JSON/MD): `/Users/hckim/Documents/twi/docs/topic_candidates.json`, `/Users/hckim/Documents/twi/docs/topic_candidates.md`
- 최근 HAR 선별 결과(JSON/MD): `/Users/hckim/Documents/twi/docs/recent_agent_shortlist_20260412.json`, `/Users/hckim/Documents/twi/docs/recent_agent_shortlist_20260412.md`
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
- HAR 파일이 git에 포함되지 않았는지 확인

PR 후:
- `CI` 워크플로 성공 확인 (`.github/workflows/ci.yml`)

머지 후:
- `Deploy Cloudflare Pages` 워크플로 성공 확인 (`.github/workflows/deploy-cloudflare-pages.yml`)
- `https://blog.midagedev.com` 접속 확인
- `rss.xml` 확인
- canonical host 확인 (`blog.midagedev.com`)

## 9. 권장 주기

- 주 1회: 최근 X 글 HAR 수집 + 에이전트 선별 + 노트 발행
- 월 1회: 태그/상단 글 재정리
