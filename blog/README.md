# Blog App (Astro)

실제 사용자에게 노출되는 블로그 앱입니다.

## 로컬 개발
```bash
cd blog
npm install
npm run dev
```

## 빌드
```bash
cd blog
SITE_URL=https://blog.midagedev.com npm run build
```

## 배포

수동 `wrangler` 배포 대신 GitHub Actions에서 Cloudflare Pages 자동 배포를 사용합니다.

- PR/푸시 시 CI: `.github/workflows/ci.yml`
- `main` 머지 시 배포: `.github/workflows/deploy-cloudflare-pages.yml`

필요 시 GitHub Actions에서 `Deploy Cloudflare Pages`를 수동 실행할 수 있습니다.

## 참고 문서

- 전체 설정: `docs/SETUP.md`
- 배포 런북: `docs/DEPLOYMENT.md`
- 콘텐츠 운영: `docs/WORKFLOW.md`
