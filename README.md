# twi2blog + Astro

트위터 아카이브를 Markdown으로 변환하고, Astro 블로그로 발행하는 프로젝트입니다.

## 1) 트윗 변환기 설치
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## 2) 트윗 아카이브를 블로그 글로 변환
`data/tweets.js`를 내려받아 둔 뒤 실행:

```bash
source .venv/bin/activate
twi2blog \
  --archive data/tweets.js \
  --out blog/src/content/blog \
  --min-likes 20 \
  --min-retweets 5
```

## 3) Astro 로컬 실행
```bash
cd blog
npm install
npm run dev
```

## 생성되는 글 포맷

```yaml
---
title: "제목"
description: "요약"
pubDate: 2025-01-01
source: twitter
tags:
  - twitter
---
```

## 배포
Cloudflare Pages 연결은 `blog/README.md`를 참고하세요.
