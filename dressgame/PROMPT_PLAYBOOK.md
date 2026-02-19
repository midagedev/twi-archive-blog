# Dress Room Prompt Playbook (fal.ai)

## 목표
- 이미지 생성 시 스타일 흔들림을 줄이고, 같은 게임 세계관처럼 보이게 만든다.
- 키 비주얼, 아바타, 의상, 배경이 한 세트처럼 맞물리게 만든다.

## 1) 일관성 5원칙
- 모델 고정: 한 단계에서는 같은 모델만 사용한다.
- 문장 순서 고정: 프롬프트 블록 순서를 매번 동일하게 유지한다.
- 스타일 앵커 고정: 색감/조명/재질/카메라 표현을 반복한다.
- 시드 고정: 같은 카테고리는 같은 시드 정책을 적용한다.
- QA 게이트: 기준 미달 이미지는 바로 폐기하고 재생성한다.

## 1.5) 체형 고정 규칙 (Body Lock)
- 기본 아바타는 `무조건` 단색 바디수트(또는 단순 베이스웨어)만 입힌다.
- 기본 아바타에 티셔츠/청바지/치마 같은 실의상 디테일을 넣지 않는다.
- 의상 파츠는 같은 체형 팩에서만 사용한다. (예: body_a 전용)
- 체형이 다른 팩끼리는 섞어 입히지 않는다.

## 1.6) 비율 고정 규칙 (Proportion Lock)
- 기본 비율은 `슬림 치비 3.5~4등신`으로 고정한다.
- 캐릭터 높이 대비 머리 높이 비율은 약 `1:3.5~1:4`를 목표로 한다.
- 실루엣은 슬림하게 유지한다. (좁은 어깨/엉덩이, 가는 팔/다리)
- 파츠 생성 시 같은 비율 규칙을 유지한다.
- 나이 표현은 특정하지 않고, `age-ambiguous anime character`로 고정한다.

## 2) 권장 생성 파이프라인
1. 스타일 마스터 1장 생성 (`key visual master`).
2. 같은 스타일로 파생 이미지를 생성:
- 가능하면 `image-to-image`/reference 기반 모델 사용.
- 텍스트만 쓸 때는 동일한 스타일 앵커 + 시드 정책 유지.
3. QA 체크 후 통과본만 채택.

### 원샷 스프라이트시트 전략 (일관성 우선)
- 한 장에 `아바타 + 착용 파츠`를 동시에 생성한다.
- 장점: 라인/색/비율이 자동으로 통일되어 스타일 흔들림이 줄어든다.
- 단점: 파츠 누락/불필요 조각이 생길 수 있어 후처리(크롭/정렬)가 필요하다.
- 권장: 첫 배치 에셋을 빠르게 확보할 때 사용하고, 이후 부족 파츠만 보강 생성.

### 모델 권장 분리
- 키 비주얼: `fal-ai/flux/dev` 또는 `fal-ai/recraft/v3/text-to-image`
- 파츠(아바타/의상): 텍스트 단독보다 reference 편집 모델 우선
- 이유: 텍스트 단독은 다중 인물, 블러, 원근감 흔들림이 자주 발생
- 원샷 스프라이트시트: `fal-ai/flux-pro/v1.1-ultra` 우선 검토 (고해상도 확보)
- 슬림 치비 체형 고정이 중요할 때: `fal-ai/qwen-image-max/text-to-image`도 우선 테스트

## 3) 프롬프트 블록 구조 (고정 템플릿)
아래 순서를 바꾸지 않는다.

1. `STYLE_LOCK`
2. `QUALITY_LOCK`
3. `ASSET_LOCK` (키비주얼/아바타/의상/배경별)
4. `SUBJECT`
5. `SCENE`
6. `COMPOSITION`
7. `COLOR`
8. `OUTPUT`
9. `NEGATIVE_LOCK`

## 4) 공통 앵커 문구 (Anime 2D Lock)

### STYLE_LOCK
`2D anime-style dress-up game illustration, slim chibi 3.5-to-4-head proportion, flat cel shading, clean line art, front-facing character design, orthographic-like view, soft pastel palette, high readability, family-friendly, no edgy mood`

### QUALITY_LOCK
`high quality, crisp outlines, clear silhouette separation, balanced composition, production-ready game art, consistent line weight, minimal gradient, no blur, no noise`

### PARTS_COMPAT_LOCK
`paper-doll compatible design, strict front view, neutral pose, symmetrical body alignment, separated readable shapes for hair/top/bottom/dress/shoes/accessory layers, no perspective distortion`

### BODY_LOCK
`base avatar wears plain tight bodysuit only, no built-in fashion clothing details, clothing parts must match exact base-body proportions and anchor alignment`

### PROPORTION_LOCK
`slim chibi 3.5-to-4-head proportion only, slightly larger head with slender torso/legs, keep the same ratio across avatar and all wearable parts`

### NEGATIVE_LOCK
`3d render, cgi, clay, doll-like figurine, toy plastic, octane render, unreal engine look, photorealistic, realistic skin pores, strong depth of field, cinematic bokeh, harsh volumetric light, gritty texture, horror, dark moody lighting, painterly brush strokes, heavy grain, blurry, low resolution, distorted anatomy, extra limbs, cropped head, text, logo, watermark`

## 5) 에셋 타입별 ASSET_LOCK

### Key Visual
`hero key visual for browser dress-up game, center focus, clear empty space for UI title, decorative but uncluttered background`

### Avatar Base
`full-body front-facing avatar base for layered dress-up system, neutral A-pose, transparent background, no clothes details that block overlays`

### Clothing Item
`single clothing item for dress-up layer system, front view, centered, transparent background, no mannequin, no body parts, clean silhouette`

### Accessory
`single accessory icon for dress-up layer system, front view, centered, transparent background, no mannequin, no text`

### Background
`dress-up game stage background only, no character, no text, clean center area for avatar placement`

## 6) 시드/파라미터 정책
- `image_size`:
- 키 비주얼: `landscape_16_9`
- 아이템/아바타: `square_hd`
- `num_images`: `1` (품질 선별형 워크플로우)
- `seed`:
- 스타일 마스터용 고정 시드 1개 선택 (예: `424242`)
- 파생 에셋은 카테고리별 고정 시드 사용
- 예: hair `10101`, top `20202`, bottom `30303`, dress `40404`, shoes `50505`, accessory `60606`, bg `70707`

### 텍스트 길이 제한 주의
- 일부 모델은 프롬프트 길이 제한이 있으므로 1000자 이내로 유지한다.
- 긴 설명보다 핵심 제약어(정면/2D/셀셰이딩/No 3D)를 우선 배치한다.
- `fal-ai/qwen-image-max/text-to-image`는 프롬프트 800자 제한에 맞춘다.

## 7) 품질 게이트 (통과 기준)
- 스타일 일치: 파스텔 톤/재질/조명이 기존 마스터와 맞는다.
- 실루엣 선명도: 축소 썸네일에서 구분 가능하다.
- 레이어 안전성: 의상/소품 외형이 겹침에 유리하다.
- UI 친화성: 배경이 복잡하지 않아 중앙 아바타가 잘 보인다.
- 금지 요소 없음: 텍스트/워터마크/왜곡 없음.
- 3D 징후 없음: 플라스틱 질감, 렌더링형 하이라이트, 과한 원근감이 없어야 한다.
- 바디 락 통과: 기본 아바타에 실의상(티/바지/치마)이 포함되지 않아야 한다.
- 체형 일치: 상의/하의/원피스 파츠 폭과 길이가 기본 체형과 맞아야 한다.
- 비율 통과: 슬림 치비(3.5~4등신) 느낌을 유지하고, 과도하게 통통한 비율을 피해야 한다.

## 8) 재생성 규칙
- 1회 생성 후 아래 항목 중 1개라도 실패하면 즉시 재생성:
- 얼굴/손/다리 왜곡
- 의상 경계가 흐림
- 지나친 광원 대비
- 색온도 이탈 (너무 회색/탁함)
- 3D 질감 또는 피규어 느낌 발생

## 9) 운영 팁
- 프롬프트 길이를 너무 길게 늘리지 말고, 고정 블록 + 변수 블록 중심으로 유지한다.
- 변경은 한 번에 1축만 바꾼다 (색감만, 구도만 등).
- 좋은 결과 프롬프트/시드는 파일로 기록해 재사용한다.
- 파츠 생성은 가능하면 아래 순서로 진행:
- 1) 기준 아바타 베이스 1장 확정
- 2) 같은 베이스를 reference로 의상만 편집
- 3) 배경제거/정렬 후 레이어 에셋으로 저장
