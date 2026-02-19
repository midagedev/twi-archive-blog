# Midage Dev Notes - Repository Guide

`/Users/hckim/Documents/twi`는 X/Twitter 아카이브에서 고신호 글을 선별해 블로그 포스트로 전환하는 저장소입니다.

## 현재 운영 방식 (에이전트 선별 전용)

- 선별은 규칙 기반이 아니라 병렬 에이전트 리뷰 결과(`manual_agent_selected_100.json`)를 기준으로 진행합니다.
- 생성은 `scripts/agent_curation_pipeline.py` 단일 스크립트로 수행합니다.
- 제목은 별도 생성하지 않고 본문 발췌를 사용합니다.

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

## 콘텐츠 생성 (100개 기준)

```bash
cd /Users/hckim/Documents/twi
python3 scripts/agent_curation_pipeline.py \
  --archive twitter-2026-02-14-1222227abadceeb048d368042ea1c9a5fb39fa3bb74113fbf40e59755047273a.zip \
  --selection-json docs/manual_agent_selected_100.json \
  --candidate-json docs/topic_candidates.json \
  --candidate-md docs/topic_candidates.md \
  --draft-dir blog/src/content/blog \
  --max-items 100 \
  --clean-draft-dir
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
- 수동 선별 ID: `/Users/hckim/Documents/twi/docs/manual_agent_selected_100.json`
- 후보 결과: `/Users/hckim/Documents/twi/docs/topic_candidates.json`
- 블로그 콘텐츠: `/Users/hckim/Documents/twi/blog/src/content/blog`
