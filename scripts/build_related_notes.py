#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


STATUS_ID_RE = re.compile(r"/status/(\d+)")
TOKEN_RE = re.compile(r"[\w가-힣]+", re.UNICODE)
HTML_RE = re.compile(r"<[^>]+>")
IMAGE_ROW_RE = re.compile(r'<p class="tweet-image-row">.*?</p>', re.DOTALL)
HEADING_INDEX_RE = re.compile(r"^#+\s*\d+\s*$", re.MULTILINE)
URL_RE = re.compile(r"https?://\S+")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

STOPWORDS = {
    "것",
    "것이",
    "게",
    "수",
    "좀",
    "더",
    "때",
    "듯",
    "중",
    "내",
    "그",
    "이",
    "저",
    "나",
    "너",
    "우리",
    "요즘",
    "오늘",
    "이번",
    "정도",
    "정말",
    "너무",
    "그냥",
    "계속",
    "이제",
    "하는",
    "하고",
    "했다",
    "하면",
    "해서",
    "되는",
    "되면",
    "있는",
    "있다",
    "있었다",
    "없는",
    "안되는",
    "같다",
    "같은",
    "아니",
    "내가",
    "나는",
    "거의",
    "결국",
    "특히",
    "없이",
    "제대로",
    "어떻게",
    "좋다",
    "좋겠다",
    "고민을",
    "개발자",
    "작업이",
    "코드의",
    "부분이",
    "보고",
    "이걸",
    "없다",
    "아마",
    "with",
    "that",
    "this",
    "from",
    "then",
    "than",
    "have",
    "there",
    "their",
    "about",
}


@dataclass(frozen=True)
class Note:
    path: Path
    slug: str
    title: str
    description: str
    pub_date: str
    tags: tuple[str, ...]
    text: str
    tokens: Counter[str]


def _split_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    _, frontmatter, body = raw.split("---", 2)
    return _parse_frontmatter(frontmatter), body


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError:
            return value.strip('"')
    return value


def _parse_frontmatter(frontmatter: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_list: str | None = None

    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if current_list and line.startswith("  - "):
            values = data.setdefault(current_list, [])
            if isinstance(values, list):
                values.append(_parse_scalar(line[4:]))
            continue
        current_list = None

        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
            current_list = key
            continue
        data[key] = _parse_scalar(value)

    return data


def _clean_text(value: str) -> str:
    value = IMAGE_ROW_RE.sub(" ", value)
    value = HTML_RE.sub(" ", value)
    value = HEADING_INDEX_RE.sub(" ", value)
    value = URL_RE.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokenize(value: str) -> Counter[str]:
    tokens: list[str] = []
    for token in TOKEN_RE.findall(value.lower()):
        if len(token) < 2 or token in STOPWORDS:
            continue
        if token.isdigit():
            continue
        tokens.append(token)
    return Counter(tokens)


def _post_slug(path: Path, data: dict[str, object]) -> str:
    pub_date = str(data.get("pubDate") or "")
    date_slug = pub_date.replace("-", "") if DATE_RE.match(pub_date) else path.stem[:8]
    original_tweet_url = str(data.get("originalTweetUrl") or "")
    tweet_id_match = STATUS_ID_RE.search(original_tweet_url)
    if tweet_id_match:
        return f"{date_slug}-{tweet_id_match.group(1)}"
    fallback = re.sub(r"^\d{8}-", "", path.stem)
    return f"{date_slug}-{fallback}"


def load_notes(content_dir: Path) -> list[Note]:
    notes: list[Note] = []
    for path in sorted(content_dir.glob("*.md*")):
        raw = path.read_text(encoding="utf-8")
        data, body = _split_frontmatter(raw)
        pub_date = str(data.get("pubDate") or "")
        if not pub_date:
            continue
        title = str(data.get("title") or path.stem)
        description = str(data.get("description") or "")
        tags = tuple(str(tag) for tag in data.get("tags", []) if str(tag))
        text = _clean_text(f"{title} {description} {body}")
        notes.append(
            Note(
                path=path,
                slug=_post_slug(path, data),
                title=title,
                description=description,
                pub_date=pub_date,
                tags=tags,
                text=text,
                tokens=_tokenize(text),
            )
        )
    return notes


def _date_distance(left: str, right: str) -> float:
    try:
        left_date = datetime.fromisoformat(left)
        right_date = datetime.fromisoformat(right)
    except ValueError:
        return 3650.0
    return abs((left_date - right_date).days)


def _date_sort_value(value: str) -> int:
    try:
        return datetime.fromisoformat(value).toordinal()
    except ValueError:
        return 0


def _score(left: Note, right: Note) -> tuple[float, list[str]]:
    shared_tags = sorted(set(left.tags) & set(right.tags))
    shared_tokens = [token for token, _ in (left.tokens & right.tokens).most_common(8)]
    days_apart = _date_distance(left.pub_date, right.pub_date)
    recency_bonus = max(0.0, 4.0 - math.log1p(days_apart))

    score = len(shared_tags) * 14.0 + min(len(shared_tokens), 8) * 2.2 + recency_bonus
    reasons: list[str] = []
    if shared_tags:
        reasons.append("같은 주제: " + ", ".join(f"#{tag}" for tag in shared_tags[:4]))
    if shared_tokens:
        reasons.append("겹치는 단서: " + ", ".join(shared_tokens[:4]))
    return score, reasons


def build_relations(notes: list[Note], limit: int, min_score: float) -> dict[str, list[dict[str, object]]]:
    relations: dict[str, list[dict[str, object]]] = {}
    for note in notes:
        ranked: list[tuple[float, Note, list[str]]] = []
        for candidate in notes:
            if candidate.slug == note.slug:
                continue
            score, reasons = _score(note, candidate)
            if score < min_score:
                continue
            ranked.append((score, candidate, reasons))

        ranked.sort(key=lambda row: (-row[0], -_date_sort_value(row[1].pub_date), row[1].slug))
        relations[note.slug] = [
            {
                "slug": candidate.slug,
                "score": round(score, 2),
                "title": candidate.title,
                "reasons": reasons[:2],
            }
            for score, candidate, reasons in ranked[:limit]
        ]
    return relations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_related_notes",
        description="Build a stored related-note graph for Astro blog posts.",
    )
    parser.add_argument("--content-dir", type=Path, default=Path("blog/src/content/blog"))
    parser.add_argument("--out", type=Path, default=Path("blog/src/data/related-notes.json"))
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=14.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notes = load_notes(args.content_dir)
    relations = build_relations(notes, args.limit, args.min_score)
    payload = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "scripts/build_related_notes.py",
        "contentDir": str(args.content_dir),
        "limit": args.limit,
        "minScore": args.min_score,
        "noteCount": len(notes),
        "relations": relations,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linked = sum(1 for rows in relations.values() if rows)
    edges = sum(len(rows) for rows in relations.values())
    print(f"notes={len(notes)}")
    print(f"linked_notes={linked}")
    print(f"edges={edges}")
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
