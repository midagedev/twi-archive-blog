# Blog App (Astro)

실제 사용자에게 노출되는 블로그 앱입니다.

## 로컬 개발
```bash
cd /Users/hckim/Documents/twi/blog
npm install
npm run dev
```

## 빌드
```bash
cd /Users/hckim/Documents/twi/blog
SITE_URL=https://blog.midagedev.com npm run build
```

## 배포
```bash
cd /Users/hckim/Documents/twi/blog
wrangler pages deploy dist --project-name blog --branch main
```

## 참고 문서

- 전체 설정: `/Users/hckim/Documents/twi/docs/SETUP.md`
- 콘텐츠 운영: `/Users/hckim/Documents/twi/docs/WORKFLOW.md`
