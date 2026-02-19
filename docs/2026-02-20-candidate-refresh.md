# 2026-02-20 Candidate Refresh Log

## Goal

- Regenerate blog candidates from Twitter archive with practical volume.
- Combine existing mechanical filtering with one-time manually curated include IDs.
- Publish a browsable set in the local Astro blog for review.

## What Changed

### 1) Converter enhancement (`twi2blog`)

- Added support for force-include tweet IDs loaded from JSON.
- Kept original mechanical filtering logic unchanged.
- Added CLI option:
  - `--include-ids` (default: `docs/manual_include_tweet_ids.json`)

Files:

- `/Users/hckim/Documents/twi/src/twi2blog/convert.py`
- `/Users/hckim/Documents/twi/src/twi2blog/cli.py`
- `/Users/hckim/Documents/twi/docs/manual_include_tweet_ids.json`

## 2) One-time manual include set

- Curated manually from archive JSON with LLM-assisted review.
- Stored as fixed list for reuse.
- Current size: `20` tweet IDs.

File:

- `/Users/hckim/Documents/twi/docs/manual_include_tweet_ids.json`

## 3) Candidate regeneration for review

- Previous temporary review volumes tested: `50`, `80`.
- Final review set for today: `60`.
- Existing blog markdown in `blog/src/content/blog` was replaced by regenerated set as requested.

Files:

- `/Users/hckim/Documents/twi/blog/src/content/blog/*.md` (now 60 files)
- `/Users/hckim/Documents/twi/docs/topic_candidates.json` (candidate_count: 60)
- `/Users/hckim/Documents/twi/docs/topic_candidates.md`

## Commands Used (final state)

```bash
python3 scripts/agent_blog_pipeline.py \
  --archive twitter-2026-02-14-1222227abadceeb048d368042ea1c9a5fb39fa3bb74113fbf40e59755047273a.zip \
  --mode full \
  --max-topics 60 \
  --tweets-per-topic 8 \
  --min-score 2.2 \
  --draft-dir blog/src/content/blog \
  --candidate-json docs/topic_candidates.json \
  --candidate-md docs/topic_candidates.md \
  --workers 6
```

## Verification

- Content file count:
  - `/Users/hckim/Documents/twi/blog/src/content/blog` -> `60` markdown files
- Astro production build:
  - `cd blog && npm run build` passed
- Dev server:
  - `cd blog && npm run dev -- --host 0.0.0.0 --port 4321`
  - Port `4321` was occupied, server used `4322`

## Notes

- This refresh prioritizes fast review and selection quality over immediate publish readiness.
- Final publish should still include human editorial pass on title, description, and body quality.
