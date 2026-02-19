# 2026-02-20 Candidate Refresh Log

## Goal

- Keep only the agent-based curation flow.
- Remove old rule-based/manual-include selection code and artifacts.
- Regenerate 100 blog posts from manually reviewed IDs.

## What Changed

### 1) Agent-only pipeline fixed as source of truth

- Manual selection file fixed to `docs/manual_agent_selected_100.json` (100 IDs).
- `scripts/agent_curation_pipeline.py` used for:
  - archive loading
  - topic/tag inference
  - candidate JSON/MD report generation
  - markdown post writing

### 2) Legacy selection path removed

- Deleted scripts:
  - `/Users/hckim/Documents/twi/scripts/prepare_tweet_corpus.py`
  - `/Users/hckim/Documents/twi/scripts/run_codex_subagents.sh`
  - `/Users/hckim/Documents/twi/scripts/agent_blog_pipeline.py`
- Deleted old artifacts:
  - `/Users/hckim/Documents/twi/docs/manual_include_tweet_ids.json`
  - `/Users/hckim/Documents/twi/docs/topic_shortlist.json`
  - `/Users/hckim/Documents/twi/docs/topic_shortlist.md`
  - `/Users/hckim/Documents/twi/docs/topic_candidates_manual_agent80.json`
  - `/Users/hckim/Documents/twi/docs/manual_agent_selected_80_ids.json`
- Removed old include-ID option from:
  - `/Users/hckim/Documents/twi/src/twi2blog/cli.py`
  - `/Users/hckim/Documents/twi/src/twi2blog/convert.py`

### 3) Regenerated outputs

- Candidate files:
  - `/Users/hckim/Documents/twi/docs/topic_candidates.json`
  - `/Users/hckim/Documents/twi/docs/topic_candidates.md`
- Blog markdown:
  - `/Users/hckim/Documents/twi/blog/src/content/blog/*.md` (thread dedupe applied)

### 4) Quality-oriented curation update

- Duplicate selections within the same reply-connected thread are deduplicated.
- A single post now includes the full thread component instead of only one tweet.
- Candidate ranking is quality-first:
  - longer thread and longer text are preferred
  - engagement is reflected
  - book/reading signals are boosted to include more reading-oriented posts

## Command Used

```bash
python3 scripts/agent_curation_pipeline.py \
  --archive twitter-2026-02-14-1222227abadceeb048d368042ea1c9a5fb39fa3bb74113fbf40e59755047273a.zip \
  --selection-json docs/manual_agent_selected_100.json \
  --candidate-json docs/topic_candidates.json \
  --candidate-md docs/topic_candidates.md \
  --draft-dir blog/src/content/blog \
  --max-items 0 \
  --clean-draft-dir
```

## Verification

- Pipeline output:
  - `selection_loaded=100`
  - `candidates_written=100`
  - `drafts_written=100`

## Notes

- Selection is one-time manual+agent curation. Runtime selection is no longer rule-extended.
- Final publish still requires human editorial pass for tone and narrative completeness.
