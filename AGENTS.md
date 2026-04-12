# Repository Guidelines

## Project Goal
- Preserve high-signal X/Twitter posts as curated engineering notes that improve career visibility during job transitions.
- Prioritize real engineering decisions, tradeoffs, and outcomes over generic commentary.
- Keep the author's original short-form voice. Do not expand notes into generic long-form essays by default.
- Exclude very short standalone tweets by default; one-line notes need a clear reason to be published.

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
- Use AI for curation, grouping, tagging, and light cleanup. Do not ask AI to pad tweets into polished essays unless explicitly requested.
- Avoid generic AI phrasing (for example, “In today’s fast-paced world”).
- Preserve the tweet's original judgment, rhythm, and rough edges when they carry signal.
- Prefer short note posts sourced from selected tweets. Longer synthesis posts should be rare and manually reviewed.

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
