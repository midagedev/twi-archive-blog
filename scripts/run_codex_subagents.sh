#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <twitter-archive.zip|tweets.js>"
  exit 1
fi

ARCHIVE_PATH="$1"
if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Archive not found: $ARCHIVE_PATH"
  exit 1
fi

MODEL="${MODEL:-gpt-5.3-codex}"
WORK_DIR="${WORK_DIR:-$ROOT_DIR/.tmp/codex_pipeline}"
MAX_ITEMS="${MAX_ITEMS:-0}"                    # 0 means full corpus
MAX_TOPICS="${MAX_TOPICS:-80}"                 # number of output posts
WRITERS="${WRITERS:-6}"
MIN_THREAD_LEN="${MIN_THREAD_LEN:-2}"
MIN_THREAD_SCORE="${MIN_THREAD_SCORE:-0.0}"

PROMPT_DIR="$WORK_DIR/prompts"
LOG_DIR="$WORK_DIR/logs"
PACKET_DIR="$WORK_DIR/topic_packets"
OUT_DRAFT_DIR="$ROOT_DIR/drafts/codex"
STYLE_FEWSHOT="$ROOT_DIR/prompts/subagents/style_fewshot.md"

mkdir -p "$PROMPT_DIR" "$LOG_DIR" "$PACKET_DIR" "$OUT_DRAFT_DIR"

sanitize_draft() {
  local draft_path="$1"
  python3 - "$draft_path" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
if not path.exists():
    raise SystemExit(0)

text = path.read_text(encoding="utf-8")
lines = text.splitlines()
new_lines = []
skip_mode = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith("##") and ("원문 참고" in stripped or "참고" == stripped.replace("#", "").strip()):
        skip_mode = True
        continue
    if skip_mode:
        if stripped.startswith("## "):
            skip_mode = False
        else:
            continue
    if "x.com/i/web/status/" in stripped:
        continue
    if re.search(r"https?://x\.com/", stripped):
        continue
    if stripped.startswith("## "):
        continue
    new_lines.append(line)

cleaned = "\n".join(new_lines)
cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip() + "\n"
path.write_text(cleaned, encoding="utf-8")
PY
}

enforce_source_title() {
  local packet_path="$1"
  local draft_path="$2"
  python3 - "$packet_path" "$draft_path" <<'PY'
import pathlib
import re
import sys

packet_path = pathlib.Path(sys.argv[1])
draft_path = pathlib.Path(sys.argv[2])
if not packet_path.exists() or not draft_path.exists():
    raise SystemExit(0)

packet_text = packet_path.read_text(encoding="utf-8")
match = re.search(r"^- source_title:\s*(.+)$", packet_text, flags=re.MULTILINE)
if not match:
    raise SystemExit(0)

source_title = match.group(1).strip().replace('"', "'")
if not source_title:
    raise SystemExit(0)

text = draft_path.read_text(encoding="utf-8")
frontmatter_match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.DOTALL)
if not frontmatter_match:
    raise SystemExit(0)

frontmatter = frontmatter_match.group(1)
if re.search(r"^title:\s*.*$", frontmatter, flags=re.MULTILINE):
    frontmatter = re.sub(
        r"^title:\s*.*$",
        f'title: "{source_title}"',
        frontmatter,
        count=1,
        flags=re.MULTILINE,
    )
else:
    frontmatter = f'title: "{source_title}"\n' + frontmatter

rewritten = f"---\n{frontmatter}\n---\n" + text[frontmatter_match.end():]
draft_path.write_text(rewritten, encoding="utf-8")
PY
}

run_writer_job() {
  local priority="$1"
  local topic_id="$2"
  local packet_path="$3"
  local draft_path="$4"
  local log_path="$5"

  local composed_prompt="$PROMPT_DIR/writer-${priority}-${topic_id}.md"
  {
    cat "$ROOT_DIR/prompts/subagents/writer.md"
    echo
    if [[ -f "$STYLE_FEWSHOT" ]]; then
      cat "$STYLE_FEWSHOT"
      echo
    fi
    echo "# TOPIC PACKET"
    cat "$packet_path"
  } > "$composed_prompt"

  codex exec \
    --skip-git-repo-check \
    --sandbox workspace-write \
    --model "$MODEL" \
    --output-last-message "$draft_path" \
    - < "$composed_prompt" > "$log_path" 2>&1

  sanitize_draft "$draft_path"
  enforce_source_title "$packet_path" "$draft_path"
}

echo "[1/4] Prepare tweet corpus"
python3 "$ROOT_DIR/scripts/prepare_tweet_corpus.py" \
  --archive "$ARCHIVE_PATH" \
  --out-dir "$WORK_DIR" \
  --max-items "$MAX_ITEMS"

echo "[2/4] Build strict thread shortlist (no cross-thread merge)"
python3 - "$WORK_DIR" "$ROOT_DIR" "$MAX_TOPICS" "$MIN_THREAD_LEN" "$MIN_THREAD_SCORE" <<'PY'
import datetime
import json
import math
import pathlib
import re
import sys

work_dir = pathlib.Path(sys.argv[1])
root_dir = pathlib.Path(sys.argv[2])
max_topics = int(sys.argv[3])
min_thread_len = int(sys.argv[4])
min_thread_score = float(sys.argv[5])

corpus = json.loads((work_dir / "tweet_corpus.json").read_text(encoding="utf-8"))
lookup = json.loads((work_dir / "tweet_lookup.json").read_text(encoding="utf-8"))


def source_title_from_text(text: str, limit: int = 72) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"@[A-Za-z0-9_]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^[-,:;./)\]]+\s*", "", cleaned)
    cleaned = re.sub(r"\s+([,.:;!?])", r"\1", cleaned)
    if not cleaned:
        return "제목 없음"
    first = re.split(r"(?<=[.!?。！？])\s+", cleaned, maxsplit=1)[0].strip()
    if len(first) <= limit:
        return first
    return first[:limit].rstrip()


def slugify(text: str) -> str:
    value = text.lower().strip()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "thread"

candidates = []
for unit in corpus:
    if unit.get("unit_type") != "thread":
        continue

    tweet_ids = [tid for tid in unit.get("tweet_ids", []) if tid in lookup]
    if len(tweet_ids) < min_thread_len:
        continue

    root = lookup[tweet_ids[0]]
    root_text = (root.get("text") or "").strip()
    if not root_text:
        continue
    # Skip pure reply-opening threads for better standalone readability.
    if root_text.startswith("@"):
        continue

    unit_score = float(unit.get("score", 0.0) or 0.0)
    if unit_score < min_thread_score:
        continue

    thread_len = len(tweet_ids)
    engagement = int(unit.get("likes", 0) or 0) + int(unit.get("retweets", 0) or 0) * 2
    priority_score = unit_score + (math.log2(thread_len + 1) * 1.2)

    candidates.append(
        {
            "tweet_ids": tweet_ids,
            "thread_len": thread_len,
            "priority_score": round(priority_score, 4),
            "unit_score": unit_score,
            "engagement": engagement,
            "source_title": source_title_from_text(root_text),
        }
    )

candidates.sort(
    key=lambda x: (x["priority_score"], x["thread_len"], x["engagement"]),
    reverse=True,
)

if max_topics > 0:
    candidates = candidates[:max_topics]

packet_dir = work_dir / "topic_packets"
packet_dir.mkdir(parents=True, exist_ok=True)
for old in packet_dir.glob("*.md"):
    old.unlink()

jobs_tsv = work_dir / "writer_jobs.tsv"
job_lines = []

shortlist_topics = []
md_lines = ["# Topic Shortlist", ""]
md_lines.append(f"- generated_at: {datetime.datetime.now().isoformat()}")
md_lines.append(f"- topic_count: {len(candidates)}")
md_lines.append("- policy: one post per thread (no cross-thread merge)")
md_lines.append("")

today = datetime.date.today().strftime("%Y%m%d")
for idx, cand in enumerate(candidates, start=1):
    tweet_ids = cand["tweet_ids"]
    source_rows = [lookup[tid] for tid in tweet_ids]
    source_title = cand["source_title"]
    topic_id = f"thread-{idx:02d}-{slugify(source_title)[:42]}".strip("-")

    canonical_pub_date = min((row.get("created_at") or row.get("date", "")) for row in source_rows)

    packet_path = packet_dir / f"{idx:02d}-{topic_id}.md"
    draft_path = root_dir / "drafts" / "codex" / f"{today}-{idx:02d}-{topic_id}.md"
    log_path = work_dir / "logs" / f"writer-{idx:02d}-{topic_id}.log"

    packet_lines = []
    packet_lines.append(f"# Topic Packet {idx}")
    packet_lines.append("")
    packet_lines.append(f"- topic_id: {topic_id}")
    packet_lines.append(f"- title: {source_title}")
    packet_lines.append(f"- source_title: {source_title}")
    packet_lines.append("- angle: 한 개 스레드의 맥락 안에서만 사실을 정리한다.")
    packet_lines.append("- rationale: 서로 다른 스레드를 합치지 않는다.")
    packet_lines.append(f"- canonical_pub_date: {canonical_pub_date}")
    packet_lines.append(f"- thread_len: {cand['thread_len']}")
    packet_lines.append(f"- priority_score: {cand['priority_score']}")
    packet_lines.append("")
    packet_lines.append("## Source Tweets")
    packet_lines.append("")
    for tid in tweet_ids:
        tw = lookup[tid]
        packet_lines.append(f"- id: {tid}")
        packet_lines.append(f"  - date: {tw['date']}")
        packet_lines.append(f"  - created_at: {tw.get('created_at', tw['date'])}")
        packet_lines.append(f"  - likes: {tw['likes']}, retweets: {tw['retweets']}")
        packet_lines.append(f"  - url: {tw['url']}")
        packet_lines.append(f"  - text: {tw['text']}")
    packet_lines.append("")
    packet_path.write_text("\n".join(packet_lines), encoding="utf-8")

    job_lines.append("\t".join([str(idx), topic_id, str(packet_path), str(draft_path), str(log_path)]))

    shortlist_topics.append(
        {
            "priority": idx,
            "topic_id": topic_id,
            "title": source_title,
            "tweet_ids": tweet_ids,
            "thread_len": cand["thread_len"],
            "priority_score": cand["priority_score"],
            "unit_score": cand["unit_score"],
            "engagement": cand["engagement"],
        }
    )

    md_lines.append(f"## {idx}. {source_title}")
    md_lines.append("")
    md_lines.append(f"- topic_id: `{topic_id}`")
    md_lines.append(f"- tweet_count: {len(tweet_ids)}")
    md_lines.append(f"- priority_score: {cand['priority_score']}")
    md_lines.append("")

jobs_tsv.write_text("\n".join(job_lines) + ("\n" if job_lines else ""), encoding="utf-8")

(root_dir / "docs").mkdir(parents=True, exist_ok=True)
(root_dir / "docs" / "topic_shortlist.json").write_text(
    json.dumps({"generated_at": datetime.datetime.now().isoformat(), "topics": shortlist_topics}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
(root_dir / "docs" / "topic_shortlist.md").write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")

print(f"thread_candidates={len(candidates)}")
print(f"jobs_file={jobs_tsv}")
PY

echo "[3/4] Run writer agents in parallel"
if [[ ! -s "$WORK_DIR/writer_jobs.tsv" ]]; then
  echo "No writer jobs found."
  exit 1
fi

export ROOT_DIR MODEL PROMPT_DIR STYLE_FEWSHOT
export -f run_writer_job sanitize_draft enforce_source_title

tr '\t' ' ' < "$WORK_DIR/writer_jobs.tsv" \
  | xargs -n 5 -P "$WRITERS" bash -lc 'run_writer_job "$@"' _

echo "[4/4] Done"
echo "- shortlist: $ROOT_DIR/docs/topic_shortlist.md"
echo "- shortlist json: $ROOT_DIR/docs/topic_shortlist.json"
echo "- source packets(for later reference): $WORK_DIR/topic_packets"
echo "- drafts: $OUT_DRAFT_DIR"
