# TWI Archive Blog (Astro)

트윗 기반 Markdown 글을 정적 사이트로 배포하는 Astro 블로그입니다.

## 로컬 개발
```bash
cd blog
npm install
npm run dev
```

## 빌드
```bash
cd blog
SITE_URL=https://your-domain.com npm run build
```

## Cloudflare Pages 배포

Cloudflare DNS를 이미 사용 중이라면 아래 순서가 가장 단순합니다.

1. GitHub 저장소 생성 후 코드 push
2. Cloudflare Dashboard > Workers & Pages > Create > Pages > Connect to Git
3. 저장소 선택 후 빌드 설정 입력

빌드 설정:
- Framework preset: `Astro`
- Build command: `npm run build`
- Build output directory: `dist`
- Root directory: `blog`

환경 변수:
- `SITE_URL` = 실제 운영 도메인 (`https://blog.your-domain.com` 등)

## 커스텀 도메인 연결
1. Cloudflare Pages 프로젝트 > Custom domains > Set up a custom domain
2. 도메인 입력 (예: `blog.your-domain.com`)
3. 같은 Cloudflare 계정에서 DNS 관리 중이면 레코드가 자동 생성됩니다.

## 발행 워크플로
1. `twi2blog`로 `src/content/blog` 업데이트
2. 내용 다듬기
3. GitHub push
4. Cloudflare Pages 자동 배포
