#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TopicRule:
    topic_id: str
    label: str
    tags: tuple[str, ...]
    keywords: tuple[str, ...]


TOPIC_RULES: list[TopicRule] = [
    TopicRule(
        topic_id="ai-agent-automation",
        label="AI 에이전트/자동화 실전",
        tags=("ai", "automation", "agent"),
        keywords=("ai", "llm", "gpt", "prompt", "agent", "에이전트", "자동화", "rag", "모델", "클로드", "codex"),
    ),
    TopicRule(
        topic_id="code-quality-review",
        label="코드 품질/리뷰",
        tags=("code-quality", "review", "engineering"),
        keywords=("code review", "리뷰", "리팩토링", "품질", "테스트", "bug", "버그", "clean code", "설계", "pr"),
    ),
    TopicRule(
        topic_id="career-job-transition",
        label="커리어/이직 인사이트",
        tags=("career", "job-change", "growth"),
        keywords=("이직", "커리어", "면접", "채용", "리더", "성장", "팀문화", "경력", "팀장", "주니어", "시니어"),
    ),
    TopicRule(
        topic_id="team-productivity",
        label="팀 생산성/협업 방식",
        tags=("team", "productivity", "collaboration"),
        keywords=("생산성", "협업", "프로세스", "회의", "문서화", "우선순위", "일하는 방식", "온보딩", "페어"),
    ),
    TopicRule(
        topic_id="frontend-web",
        label="프론트엔드/웹 개발",
        tags=("frontend", "web", "javascript"),
        keywords=("frontend", "react", "astro", "javascript", "typescript", "css", "ui", "ux", "웹", "nextjs", "svelte"),
    ),
    TopicRule(
        topic_id="backend-architecture",
        label="백엔드/아키텍처",
        tags=("backend", "architecture", "python"),
        keywords=(
            "backend",
            "api",
            "python",
            "database",
            "sql",
            "cache",
            "infra",
            "아키텍처",
            "서버",
            "django",
            "postgres",
            "mongodb",
            "kafka",
            "iac",
        ),
    ),
    TopicRule(
        topic_id="debugging-incident",
        label="디버깅/장애 대응",
        tags=("debugging", "incident", "reliability"),
        keywords=("장애", "트러블슈팅", "debug", "디버깅", "원인", "해결", "incident", "latency"),
    ),
    TopicRule(
        topic_id="execution-mindset",
        label="실행력/의사결정",
        tags=("execution", "decision", "leadership"),
        keywords=("의사결정", "실행", "우선순위", "집중", "실험", "가설", "회고"),
    ),
    TopicRule(
        topic_id="book-reading-insights",
        label="독서/책 인용 인사이트",
        tags=("book", "reading", "insight"),
        keywords=(
            "책",
            "독서",
            "완독",
            "재독",
            "읽고",
            "읽은",
            "인용",
            "구절",
            "저자",
            "book",
            "reading",
            "author",
            "quote",
            "chapter",
        ),
    ),
]


def _strip_archive_prefix(raw: str) -> str:
    idx = raw.find("[")
    if idx == -1:
        raise ValueError("Could not find JSON array start '[' in archive file")
    return raw[idx:]


def _parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")


def _to_int(value: str | int | None) -> int:
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _normalize_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _excerpt(text: str, limit: int = 120) -> str:
    cleaned = _normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _safe_title_excerpt(text: str, requested: str, limit: int = 72) -> str:
    source = _normalize_text(text)
    if requested:
        candidate = _normalize_text(requested)
        if candidate and candidate in source:
            if len(candidate) <= limit:
                return candidate
            return f"{candidate[:limit].rstrip()}..."
    if len(source) <= limit:
        return source or "Twitter note"
    return f"{source[:limit].rstrip()}..."


def _keyword_match(haystack: str, keyword: str) -> bool:
    token = keyword.lower().strip()
    if not token:
        return False
    if re.fullmatch(r"[a-z0-9 ._+\-]+", token):
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        return re.search(pattern, haystack) is not None
    return token in haystack


def _topic_for(text: str, hashtags: list[str]) -> TopicRule:
    haystack = f"{text.lower()} {' '.join(hashtags).lower()}"
    best_rule = TOPIC_RULES[7]  # execution-mindset fallback
    best_count = 0
    for rule in TOPIC_RULES:
        count = sum(1 for keyword in rule.keywords if _keyword_match(haystack, keyword))
        if count > best_count:
            best_count = count
            best_rule = rule
    return best_rule


def _slugify(text: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "topic"


BOOK_SIGNAL_KEYWORDS = (
    "책",
    "독서",
    "완독",
    "재독",
    "읽고",
    "읽은",
    "인용",
    "구절",
    "저자",
    "book",
    "reading",
    "author",
    "chapter",
    "quote",
)


def _book_signal_level(text: str) -> int:
    lowered = text.lower()
    keyword_hits = sum(1 for keyword in BOOK_SIGNAL_KEYWORDS if keyword in lowered)
    quote_marker = bool(
        re.search(r"[《〈][^》〉]+[》〉]", text)
        or re.search(r"\b(?:p|pp)\.?\s*\d{1,4}\b", lowered)
        or re.search(r"\b\d{1,4}쪽\b", text)
    )

    if keyword_hits == 0 and not quote_marker:
        return 0
    if keyword_hits >= 2 or (keyword_hits >= 1 and quote_marker):
        return 2
    return 1


def load_archive_lookup(input_path: Path) -> dict[str, dict[str, Any]]:
    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path, "r") as zf:
            if "data/tweets.js" not in zf.namelist():
                raise FileNotFoundError("data/tweets.js not found in archive zip")
            raw = zf.read("data/tweets.js").decode("utf-8")
    else:
        raw = input_path.read_text(encoding="utf-8")

    payload = json.loads(_strip_archive_prefix(raw))
    lookup: dict[str, dict[str, Any]] = {}

    for item in payload:
        tw = item.get("tweet", {})
        tweet_id = tw.get("id_str", "")
        if not tweet_id:
            continue
        text = _normalize_text(tw.get("full_text") or tw.get("text") or "")
        if not text or text.startswith("RT @"):
            continue
        created_at = _parse_datetime(tw.get("created_at", "Wed Jan 01 00:00:00 +0000 1970"))
        entities = tw.get("entities", {})
        extended_entities = tw.get("extended_entities", {})
        hashtags = [tag.get("text", "") for tag in entities.get("hashtags", []) if tag.get("text")]
        media_entities = entities.get("media", []) + extended_entities.get("media", [])
        media_urls: list[str] = []
        for media in media_entities:
            media_url = media.get("media_url_https") or media.get("media_url")
            if media_url and media_url not in media_urls:
                media_urls.append(media_url)

        lookup[tweet_id] = {
            "tweet_id": tweet_id,
            "created_at": created_at.isoformat(),
            "date": created_at.strftime("%Y-%m-%d"),
            "favorite_count": _to_int(tw.get("favorite_count")),
            "retweet_count": _to_int(tw.get("retweet_count")),
            "in_reply_to_status_id": tw.get("in_reply_to_status_id_str"),
            "text": text,
            "excerpt": _excerpt(text, 120),
            "hashtags": hashtags,
            "has_media": bool(media_entities),
            "media_urls": media_urls,
            "url": f"https://x.com/i/web/status/{tweet_id}",
        }
    return lookup


def _build_reply_component_map(archive_lookup: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)

    for tweet_id, source in archive_lookup.items():
        parent_id = str(source.get("in_reply_to_status_id") or "").strip()
        if parent_id and parent_id in archive_lookup:
            adjacency[tweet_id].add(parent_id)
            adjacency[parent_id].add(tweet_id)

    component_map: dict[str, list[str]] = {}
    visited: set[str] = set()
    ordered_tweet_ids = sorted(archive_lookup.keys(), key=lambda item: str(archive_lookup[item].get("created_at", "")))

    for start_id in ordered_tweet_ids:
        if start_id in visited:
            continue

        stack = [start_id]
        component: list[str] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    stack.append(neighbor)

        if len(component) <= 1:
            continue

        component.sort(key=lambda item: str(archive_lookup[item].get("created_at", "")))
        for tweet_id in component:
            component_map[tweet_id] = component

    return component_map


def load_selection(selection_path: Path) -> list[dict[str, str]]:
    payload = json.loads(selection_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("selected") or payload.get("items") or []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        tweet_id = str(row.get("id", "")).strip()
        if not tweet_id or tweet_id in seen:
            continue
        seen.add(tweet_id)
        selected.append(
            {
                "id": tweet_id,
                "title_excerpt": _normalize_text(str(row.get("title_excerpt", "")).strip()),
                "reason": _normalize_text(str(row.get("reason", "")).strip()),
            }
        )
    return selected


def build_candidates(
    archive_lookup: dict[str, dict[str, Any]],
    selection: list[dict[str, str]],
    max_items: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    reply_component_map = _build_reply_component_map(archive_lookup)
    seen_components: set[tuple[str, ...]] = set()

    for row in selection:
        selected_source = archive_lookup.get(row["id"])
        if selected_source is None:
            continue
        component_ids = reply_component_map.get(row["id"], [row["id"]])
        component_key = tuple(component_ids)
        if component_key in seen_components:
            continue
        seen_components.add(component_key)

        sources = [archive_lookup[tweet_id] for tweet_id in component_ids if tweet_id in archive_lookup]
        if not sources:
            continue

        first_source = sources[0]
        topic_rule = _topic_for(first_source["text"], first_source["hashtags"])
        engagement = sum((source["favorite_count"] + (source["retweet_count"] * 2)) for source in sources)
        total_text_length = sum(min(len(source["text"]), 280) for source in sources)
        thumbnail_source = next((source for source in sources if source.get("media_urls")), first_source)
        source_book_levels = [_book_signal_level(source["text"]) for source in sources]
        book_signal_total = sum(source_book_levels)
        thread_bonus = max(len(sources) - 1, 0) * 2.4
        book_bonus = (book_signal_total * 1.7) + (2.0 if book_signal_total > 0 else 0.0)
        score_base = engagement / 10
        score_length = total_text_length / 100
        aggregate_score = round(score_base + score_length + thread_bonus + book_bonus, 3)

        candidates.append(
            {
                "topic_id": topic_rule.topic_id,
                "topic_label": topic_rule.label,
                "tags": list(topic_rule.tags),
                "suggested_title": _safe_title_excerpt(selected_source["text"], row.get("title_excerpt", "")),
                "selection_reason": row.get("reason", ""),
                "aggregate_score": aggregate_score,
                "engagement_sum": engagement,
                "tweet_count": len(sources),
                "tweet_ids": [source["tweet_id"] for source in sources],
                "sources": [
                    {
                        "tweet_id": source["tweet_id"],
                        "score": round((source["favorite_count"] + (source["retweet_count"] * 2)) / 10, 3),
                        "book_signal_level": source_book_levels[source_idx],
                        "book_bonus": round(source_book_levels[source_idx] * 1.7, 3),
                        "has_media": source["has_media"],
                        "image_bonus": 1.1 if source["has_media"] else 0.0,
                        "created_at": source["created_at"],
                        "favorite_count": source["favorite_count"],
                        "retweet_count": source["retweet_count"],
                        "excerpt": source["excerpt"],
                        "text": source["text"],
                        "hashtags": source["hashtags"],
                        "url": source["url"],
                        "media_urls": source["media_urls"],
                    }
                    for source_idx, source in enumerate(sources)
                ],
                "selected_tweet_id": selected_source["tweet_id"],
                "selected_tweet_url": selected_source["url"],
                "primary_tweet_id": first_source["tweet_id"],
                "primary_tweet_url": first_source["url"],
                "thumbnail_url": (thumbnail_source.get("media_urls") or [None])[0],
                "book_signal_total": book_signal_total,
                "thread_bonus": round(thread_bonus, 3),
                "book_bonus": round(book_bonus, 3),
            }
        )

    candidates.sort(
        key=lambda candidate: (
            float(candidate.get("aggregate_score", 0.0)),
            int(candidate.get("tweet_count", 1)),
            int(candidate.get("book_signal_total", 0)),
            int(candidate.get("engagement_sum", 0)),
        ),
        reverse=True,
    )
    if max_items > 0:
        candidates = candidates[:max_items]

    return candidates


def write_candidates_json(candidates: list[dict[str, Any]], archive_path: Path, selection_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input": str(archive_path),
        "selection_input": str(selection_path),
        "selection_method": "manual_parallel_agent_review",
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_candidates_markdown(candidates: list[dict[str, Any]], archive_path: Path, selection_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Curated Blog Topic Candidates (Manual Agent Review)")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Source archive: `{archive_path}`")
    lines.append(f"- Selection input: `{selection_path}`")
    lines.append(f"- Candidate count: `{len(candidates)}`")
    lines.append("")

    for idx, candidate in enumerate(candidates, start=1):
        source = candidate["sources"][0]
        lines.append(f"## {idx}. {candidate['suggested_title']}")
        lines.append("")
        lines.append(f"- Topic: `{candidate['topic_label']}`")
        lines.append(f"- Aggregate score: `{candidate.get('aggregate_score', 0)}`")
        lines.append(f"- Tweet count: `{candidate.get('tweet_count', 1)}`")
        lines.append(f"- Primary Tweet ID: `{source['tweet_id']}`")
        if candidate.get("selected_tweet_id") and candidate.get("selected_tweet_id") != source["tweet_id"]:
            lines.append(f"- Selected Tweet ID: `{candidate['selected_tweet_id']}`")
        lines.append(f"- Date: `{source['created_at'][:10]}`")
        lines.append(f"- Engagement(sum): `{candidate.get('engagement_sum', 0)}`")
        lines.append(f"- Book signal(sum): `{candidate.get('book_signal_total', 0)}`")
        lines.append(f"- URL: {source['url']}")
        if candidate.get("selection_reason"):
            lines.append(f"- Reason: {candidate['selection_reason']}")
        lines.append(f"- Excerpt: {candidate['sources'][0]['excerpt']}")
        lines.append("")

    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_drafts(candidates: list[dict[str, Any]], output_dir: Path, clean: bool) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        for old_file in output_dir.glob("*.md"):
            old_file.unlink()
        for old_file in output_dir.glob("*.mdx"):
            old_file.unlink()

    written_paths: list[Path] = []
    date_prefix = datetime.now().strftime("%Y%m%d")

    for idx, candidate in enumerate(candidates, start=1):
        sources = candidate["sources"]
        source = sources[0]
        title = str(candidate["suggested_title"]).replace('"', "'")
        description = str(source.get("excerpt", "")).replace('"', "'")
        pub_date = str(source.get("created_at", ""))[:10] or datetime.now().strftime("%Y-%m-%d")
        original_tweet_url = str(source.get("url", "")).replace('"', "'")
        tags_yaml = "\n".join(f"  - {tag}" for tag in candidate.get("tags", []))
        thumbnail_url = str(candidate.get("thumbnail_url") or "").strip()
        thumbnail_yaml = f'thumbnail: "{thumbnail_url}"\n' if thumbnail_url else ""

        body_sections: list[str] = []
        if len(sources) == 1:
            body_sections.append(str(source.get("text", "")).strip())
            for media_url in [str(url) for url in source.get("media_urls", []) if str(url).strip()]:
                body_sections.append(f'<img class="tweet-image-inline" src="{media_url}" alt="tweet image" />')
        else:
            body_sections.append(str(source.get("url", "")).strip())
            body_sections.append("")
            for section_idx, section_source in enumerate(sources, start=1):
                body_sections.append(f"### {section_idx}")
                body_sections.append(str(section_source.get("text", "")).strip())
                for media_url in [str(url) for url in section_source.get("media_urls", []) if str(url).strip()]:
                    body_sections.append(f'<img class="tweet-image-inline" src="{media_url}" alt="tweet image" />')
                body_sections.append("")
        body = "\n".join(line for line in body_sections if line is not None).strip()

        frontmatter_lines = [
            "---",
            f'title: "{title}"',
            f'description: "{description}"',
            f"pubDate: {pub_date}",
            "source: twitter",
            f'originalTweetUrl: "{original_tweet_url}"',
        ]
        if thumbnail_yaml:
            frontmatter_lines.append(thumbnail_yaml.rstrip("\n"))
        frontmatter_lines.extend(
            [
                "tags:",
                tags_yaml if tags_yaml else "  - twitter",
                "---",
            ]
        )

        content = "\n".join(frontmatter_lines) + "\n\n" + body + "\n"

        slug = _slugify(candidate["topic_id"])
        file_name = f"{date_prefix}-{idx:03d}-{slug}.md"
        path = output_dir / file_name
        path.write_text(content, encoding="utf-8")
        written_paths.append(path)
    return written_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent_curation_pipeline",
        description="Generate blog candidates and markdown drafts from manual agent selections.",
    )
    parser.add_argument("--archive", type=Path, required=True, help="Path to Twitter archive zip or tweets.js")
    parser.add_argument(
        "--selection-json",
        type=Path,
        default=Path("docs/manual_agent_selected_100.json"),
        help="Manual agent selection JSON path",
    )
    parser.add_argument("--candidate-json", type=Path, default=Path("docs/topic_candidates.json"), help="Output candidate JSON")
    parser.add_argument("--candidate-md", type=Path, default=Path("docs/topic_candidates.md"), help="Output candidate markdown")
    parser.add_argument("--draft-dir", type=Path, default=Path("blog/src/content/blog"), help="Output markdown folder")
    parser.add_argument("--max-items", type=int, default=0, help="Maximum selected items to write (0 = no limit)")
    parser.add_argument("--clean-draft-dir", action="store_true", help="Delete existing .md/.mdx files in draft-dir before writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.archive.exists():
        raise FileNotFoundError(f"Archive path not found: {args.archive}")
    if not args.selection_json.exists():
        raise FileNotFoundError(f"Selection JSON not found: {args.selection_json}")

    lookup = load_archive_lookup(args.archive)
    selection = load_selection(args.selection_json)
    candidates = build_candidates(lookup, selection, args.max_items)

    write_candidates_json(candidates, args.archive, args.selection_json, args.candidate_json)
    write_candidates_markdown(candidates, args.archive, args.selection_json, args.candidate_md)
    written = write_drafts(candidates, args.draft_dir, args.clean_draft_dir)

    print(f"lookup_size={len(lookup)}")
    print(f"selection_loaded={len(selection)}")
    print(f"candidates_written={len(candidates)}")
    print(f"candidate_json={args.candidate_json}")
    print(f"candidate_md={args.candidate_md}")
    print(f"drafts_written={len(written)}")
    print(f"draft_dir={args.draft_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
