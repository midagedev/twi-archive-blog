---
title: "서드파티API가 우리쪽 서버로 리퀘스트하는 형태인데 문서가 명확치 않아 작업지연."
description: "서드파티API가 우리쪽 서버로 리퀘스트하는 형태인데 문서가 명확치 않아 작업지연. 리퀘스트를 확인하고자 간이서버를 올려야되나 고민하다가 chatGPT에게 코드작성을 요청한후 lambda에 올리고 함수URL 만들고 이..."
pubDate: 2023-02-15
source: twitter
originalTweetUrl: "https://x.com/i/web/status/1625859546056126468"
thumbnail: "https://pbs.twimg.com/media/FpA1BlsacAAQM2h.png"
tags:
  - backend
  - architecture
  - python
---

서드파티API가 우리쪽 서버로 리퀘스트하는 형태인데 문서가 명확치 않아 작업지연. 리퀘스트를 확인하고자 간이서버를 올려야되나 고민하다가 chatGPT에게 코드작성을 요청한후 lambda에 올리고 함수URL 만들고 이걸로 요청을 받아서 CloudWatch에서 리퀘스트 상세내역을 확인할 수 있었다.

<img class="tweet-image-inline" src="https://pbs.twimg.com/media/FpA1BlsacAAQM2h.png" alt="tweet image" />
