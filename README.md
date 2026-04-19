# Midage Dev Notes - Repository Guide

`/Users/hckim/Documents/twi`는 X/Twitter 아카이브와 최근 공개 글에서 고신호 글을 선별해 짧은 엔지니어링 노트로 보존하는 저장소입니다.

## 현재 운영 방식 (에이전트 선별 전용)

- 에이전트는 글을 길게 대필하지 않고 수집, 중복 제거, 선별, 주제 묶기만 담당합니다.
- 과거 아카이브는 병렬 에이전트 리뷰 결과(`manual_agent_selected_100.json`)를 기준으로 생성합니다.
- 최근 글은 브라우저 HAR를 `scripts/import_x_har.py`로 읽고, 병렬 에이전트 shortlist를 거쳐 남깁니다.
- 제목은 별도 생성하지 않고 본문 발췌를 사용해 원래 어투를 보존합니다.

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

## 과거 아카이브 생성 (100개 기준)

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

## 최근 X 글 수집/선별

브라우저에서 X 검색 결과를 `Save all as HAR with content`로 저장한 뒤 가져옵니다. HAR에는 쿠키가 들어갈 수 있으므로 커밋하지 않습니다.

```bash
cd /Users/hckim/Documents/twi
python3 scripts/import_x_har.py \
  --har data/x_recent.har \
  --since-date 2026-02-20 \
  --dry-run
```

dry-run 결과를 확인한 뒤 실제 Markdown을 생성하고, 병렬 에이전트 선별 결과는 `docs/recent_agent_shortlist_YYYYMMDD.*`로 남깁니다.

단독 트윗은 기본적으로 URL을 제외한 본문이 100자 이상일 때만 가져옵니다. 아주 짧은 한 줄 메모까지 보존해야 하는 경우에만 `--min-text-chars 0`을 사용합니다.

X 미디어는 외부 핫링크가 깨질 수 있으므로 발행 전 로컬 asset으로 복사합니다.

```bash
python3 scripts/localize_tweet_media.py
```

관련 노트 관계도는 전체 콘텐츠를 다시 훑어 갱신합니다.

```bash
python3 scripts/build_related_notes.py
```

## 로컬 검증

```bash
cd /Users/hckim/Documents/twi/blog
npm run dev
SITE_URL=https://blog.midagedev.com npm run build
```

## 배포

- 변경사항 커밋 후 `main` 푸시
- GitHub Actions가 Cloudflare Pages로 자동 배포

## 문서 인덱스

- 설정/배포: `/Users/hckim/Documents/twi/docs/SETUP.md`
- 배포 런북: `/Users/hckim/Documents/twi/docs/DEPLOYMENT.md`
- 콘텐츠 운영: `/Users/hckim/Documents/twi/docs/WORKFLOW.md`
- 이번 정리 로그: `/Users/hckim/Documents/twi/docs/2026-02-20-candidate-refresh.md`

## 핵심 경로

- 에이전트 파이프라인: `/Users/hckim/Documents/twi/scripts/agent_curation_pipeline.py`
- 최근 HAR 가져오기: `/Users/hckim/Documents/twi/scripts/import_x_har.py`
- X 미디어 로컬 복사: `/Users/hckim/Documents/twi/scripts/localize_tweet_media.py`
- 관련 노트 관계도 갱신: `/Users/hckim/Documents/twi/scripts/build_related_notes.py`
- 수동 선별 ID: `/Users/hckim/Documents/twi/docs/manual_agent_selected_100.json`
- 후보 결과: `/Users/hckim/Documents/twi/docs/topic_candidates.json`
- 최근 선별 결과: `/Users/hckim/Documents/twi/docs/recent_agent_shortlist_20260412.json`
- 블로그 콘텐츠: `/Users/hckim/Documents/twi/blog/src/content/blog`
