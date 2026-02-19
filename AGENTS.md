# Repository Guidelines

## Project Goal
- Turn high-signal past X/Twitter posts into blog articles that improve career visibility during job transitions.
- Prioritize real engineering decisions, tradeoffs, and outcomes over generic commentary.

## Project Structure & Module Organization
- `src/twi2blog/`: Python converter package (`cli.py`, `convert.py`).
- `data/`: local X/Twitter archive inputs.
- `drafts/`: generated Markdown drafts.
- `blog/`: Astro site (`blog/src`, `blog/src/content/blog`, `blog/public`).
- `dressgame/`: standalone browser prototype.
- `docs/`: operational docs (`docs/SETUP.md`, `docs/WORKFLOW.md`).

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e .`: set up Python CLI.
- `twi2blog --archive data/sample_tweets.js --out drafts`: generate draft posts.
- `cd blog && npm install`: install Astro dependencies.
- `cd blog && npm run dev`: run local blog server.
- `cd blog && SITE_URL=https://blog.midagedev.com npm run build`: production build.
- `cd blog && npm run preview`: preview built output.
- `git push origin main`: deploy to Cloudflare Pages via Actions (`.github/workflows/deploy-cloudflare-pages.yml`).

## Coding Style & Naming Conventions
- Python: follow PEP 8, 4-space indentation, type hints, and `snake_case`.
- Astro/TypeScript: follow existing `blog/src` style (tabs and single quotes); components use `PascalCase`.
- Frontmatter keys should match `blog/src/content.config.ts` (`title`, `description`, `pubDate`, `tags`, etc.).
- Generated post filenames follow `YYYYMMDD-<tweet_id>-<slug>.md`.
- In `dressgame/`, keep item IDs descriptive (for example, `top_hoodie_mint`).

## Content Voice & AI Usage
- Base tone on recent X posts: concise, practical, first-person, and specific.
- Use AI for outlining/editing only; final copy must read as personal writing.
- Avoid generic AI phrasing (for example, “In today’s fast-paced world”).
- Expand tweet ideas with structure: `problem -> decision -> execution -> result -> takeaway`.
- Target roughly 600-1200 words per post unless intentionally brief.

## Testing Guidelines
- CI runs `twi2blog` smoke conversion and `blog` production build on PR/push.
- Before merge: run converter on sample data and inspect Markdown output.
- Run `cd blog && npm run build` to catch Astro/content schema issues.
- Manually check `/`, `/blog`, one post page, and `rss.xml` in preview.
- If adding tests, place Python tests under `tests/` with `test_*.py` names.

## Commit & Pull Request Guidelines
- Keep commit subjects short, imperative, and specific (matches existing history).
- Prefer one logical change per commit.
- PRs should include purpose, affected paths, verification commands/results, and screenshots for UI changes in `blog/` or `dressgame/`.

## Security & Configuration Tips
- Do not commit personal archives, local build outputs, or dependency folders.
- Keep API keys/secrets in environment variables, never in frontend JavaScript.
