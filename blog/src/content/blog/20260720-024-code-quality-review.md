---
title: "깃헙셀프호스티드러너로 최근 두어달 온갖 실험을 해보고 있다. 모르던때에는 그냥 컨테이너안에서 도는거 아냐? 이랬는데 일종의 웹훅을..."
description: "깃헙셀프호스티드러너로 최근 두어달 온갖 실험을 해보고 있다. 모르던때에는 그냥 컨테이너안에서 도는거 아냐? 이랬는데 일종의 웹훅을 받아 온갖 기괴한 짓을 다 할수 있는 무한한 가능성이었음 지난 주말엔 사이드프로젝트의 리뷰용 러너를 vps에 설치하고 거기 Hermes한테 리뷰하게 구성해둠"
pubDate: 2026-06-02
source: twitter
originalTweetUrl: "https://x.com/i/web/status/2061605067581739349"
thumbnail: "/twitter-media/936d0a96c3-media-HJxK4Z7aYAAidxn.jpg"
tags:
  - code-quality
  - review
  - engineering
---

### 1
깃헙셀프호스티드러너로 최근 두어달 온갖 실험을 해보고 있다. 모르던때에는 그냥 컨테이너안에서 도는거 아냐? 이랬는데 일종의 웹훅을 받아 온갖 기괴한 짓을 다 할수 있는 무한한 가능성이었음
지난 주말엔 사이드프로젝트의 리뷰용 러너를 vps에 설치하고 거기 Hermes한테 리뷰하게 구성해둠

<p class="tweet-image-row"><img class="tweet-image-inline" src="/twitter-media/936d0a96c3-media-HJxK4Z7aYAAidxn.jpg" alt="tweet image" /></p>

### 2
러너는 네트워크 아웃바운드만 가능하면 어디든 설치해 쓸 수 있고(집에 노는 PC나 내 맥북에도!) 퍼미션관리가 별로 안빡빡하게 구성할 수 있다. 간단하게 컴퓨팅자원 풀을 구성해 쓸 수 있고 쉽게 트리거 시킬 수 있고.. 반면에 이래서 여기서 해킹사건이 늘 일어나는구나 싶기도 🥲

### 3
아.. 내 퍼블릭 레포에 해킹목적의 의존성을 추가한 PR을 올리면 ci 에서 테스트 돈다고 install하고 그럼 여기 vps서버에 있는 인증과 데이터가 다 털리는구나.. 권한많은 Hermes같은거에 리뷰 시키면 프롬프트 인젝션으로 내 개인정보를 쉽게 쓸수 있고 이렇게 맞아가며 배우는구나
