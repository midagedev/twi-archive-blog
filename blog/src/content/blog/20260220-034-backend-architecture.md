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

https://x.com/i/web/status/1863775406018461985

### 1
django의 prefetch_related는 디비부하를 줄일 수 있는 좋은 방법 중 하나지만 prefetch 해 온 결과물을 조합하는 과정에서 cpu 자원을 많이 사용한다. 이걸 당연한 이야기인 것 같지만 캐시가 가득찬 어느 날 40대의 서버가 골골대는 걸 경험하고 새삼 느낌.

### 2
select_related(db단 Join)가 prefetch_related에 비해 장점이 뭐가 있는지 잘 몰랐었는데(심지어 팀내에 select_related를 지양하는 가이드가 있기도) 적당한 곳에 잘 쓰면 이 부하를 이런걸 더 잘 처리하는 db에 넘길 수 있다는 장점이 있다는 걸 알았다. 물론 캐시를 잘쓰는게 젤 좋은 것 같긴 하다

### 3
이걸 보고 프리패치를 조심해서 써야 하나 생각을 하시는 분이 있을까봐 사족 이게 부담이 되었던건 주요 쿼리셋에 프리패치하는 모델이 20개 가량 되고 요청빈도가 높은데 캐시에 문제가 생겼기 때문 그리고 디비는 스케일아웃하기 힘들지만 앱서버는 쉽다. 그냥 프리패치 잘쓰자
