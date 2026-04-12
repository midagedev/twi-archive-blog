---
title: "조금만 복잡한 서비스만 되어도 이런 전략이 필수인걸 요즘 많이 느낀다. 리뷰에이전트에 컨트롤러 변경시 expand and cont..."
description: "https://martinfowler.com/bliki/ParallelChange.html 조금만 복잡한 서비스만 되어도 이런 전략이 필수인걸 요즘 많이 느낀다. 리뷰에이전트에 컨트롤러 변경시 expand and contract가 충분히 고려되어 있는지 확인하라는 인스트럭션을 추가했다. 이걸 반년을 고생하고서야 체감하네"
pubDate: 2026-04-10
source: twitter
originalTweetUrl: "https://x.com/i/web/status/2042592969061208091"
tags:
  - ai
  - automation
  - agent
---

### 1
https://martinfowler.com/bliki/ParallelChange.html
조금만 복잡한 서비스만 되어도 이런 전략이 필수인걸 요즘 많이 느낀다. 리뷰에이전트에 컨트롤러 변경시 expand and contract가 충분히 고려되어 있는지 확인하라는 인스트럭션을 추가했다. 이걸 반년을 고생하고서야 체감하네

### 2
이걸 강조하고 팀원 하나가 약간은 아쉬운 코드의 PR 메세지에 인터페이스에 파라메터를 추가한 부분이 expand 단계라고 명시적으로 쓴걸 보고 흐뭇했다. 이걸 다음 배포에 잊지말고 contract하는 작업이 이어지도록 잘 장치를 마련해봐야겠다.
