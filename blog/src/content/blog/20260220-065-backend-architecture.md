---
title: "django의 prefetch_related는 디비부하를 줄일 수 있는 좋은 방법 중 하나지만 prefetch 해 온 결과물을 조..."
description: "django의 prefetch_related는 디비부하를 줄일 수 있는 좋은 방법 중 하나지만 prefetch 해 온 결과물을 조합하는 과정에서 cpu 자원을 많이 사용한다. 이걸 당연한 이야기인 것 같지만 캐시가..."
pubDate: 2024-12-03
source: twitter
originalTweetUrl: "https://x.com/i/web/status/1863775406018461985"
tags:
  - backend
  - architecture
  - python
---

django의 prefetch_related는 디비부하를 줄일 수 있는 좋은 방법 중 하나지만 prefetch 해 온 결과물을 조합하는 과정에서 cpu 자원을 많이 사용한다. 이걸 당연한 이야기인 것 같지만 캐시가 가득찬 어느 날 40대의 서버가 골골대는 걸 경험하고 새삼 느낌.
