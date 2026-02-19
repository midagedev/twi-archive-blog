#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
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


@dataclass
class Tweet:
    id: str
    created_at: datetime
    full_text: str
    favorite_count: int
    retweet_count: int
    in_reply_to_status_id: str | None
    hashtags: list[str]
    urls: list[str]
    media_urls: list[str]
    has_media: bool


TOPIC_RULES: list[TopicRule] = [
    TopicRule(
        topic_id="ai-agent-automation",
        label="AI 에이전트/자동화 실전",
        tags=("ai", "automation", "agent"),
        keywords=("ai", "llm", "gpt", "prompt", "agent", "에이전트", "자동화", "rag", "모델"),
    ),
    TopicRule(
        topic_id="code-quality-review",
        label="코드 품질/리뷰",
        tags=("code-quality", "review", "engineering"),
        keywords=(
            "code review",
            "리뷰",
            "리팩토링",
            "품질",
            "테스트",
            "bug",
            "버그",
            "clean code",
            "설계",
        ),
    ),
    TopicRule(
        topic_id="career-job-transition",
        label="커리어/이직 인사이트",
        tags=("career", "job-change", "growth"),
        keywords=("이직", "커리어", "면접", "채용", "리더", "성장", "팀문화", "경력"),
    ),
    TopicRule(
        topic_id="team-productivity",
        label="팀 생산성/협업 방식",
        tags=("team", "productivity", "collaboration"),
        keywords=("생산성", "협업", "프로세스", "회의", "문서화", "우선순위", "일하는 방식"),
    ),
    TopicRule(
        topic_id="frontend-web",
        label="프론트엔드/웹 개발",
        tags=("frontend", "web", "javascript"),
        keywords=("frontend", "react", "astro", "javascript", "typescript", "css", "ui", "ux", "웹"),
    ),
    TopicRule(
        topic_id="backend-architecture",
        label="백엔드/아키텍처",
        tags=("backend", "architecture", "python"),
        keywords=("backend", "api", "python", "database", "sql", "cache", "infra", "아키텍처", "서버"),
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


def _excerpt(text: str, limit: int = 90) -> str:
    cleaned = _normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _keyword_match(haystack: str, keyword: str) -> bool:
    token = keyword.lower().strip()
    if not token:
        return False

    # For Latin keywords, avoid substring false positives like "ai" in "variable".
    if re.fullmatch(r"[a-z0-9 ._+\-]+", token):
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        return re.search(pattern, haystack) is not None
    return token in haystack


BOOK_SIGNAL_KEYWORDS = (
    "책",
    "독서",
    "완독",
    "재독",
    "읽고",
    "읽은",
    "읽는",
    "인용",
    "구절",
    "저자",
    "book",
    "reading",
    "author",
    "chapter",
    "quote",
)


def _book_signal_info(text: str) -> tuple[int, float]:
    lowered = text.lower()
    keyword_hits = sum(1 for keyword in BOOK_SIGNAL_KEYWORDS if keyword in lowered)
    quote_marker = bool(
        re.search(r"[《〈][^》〉]+[》〉]", text)
        or re.search(r"\b(?:p|pp)\.?\s*\d{1,4}\b", lowered)
        or re.search(r"\b\d{1,4}쪽\b", text)
    )

    if keyword_hits == 0 and not quote_marker:
        return 0, 0.0
    if keyword_hits >= 2 or (keyword_hits >= 1 and quote_marker):
        return 2, 2.2
    return 1, 1.1


def load_tweets_from_input(input_path: Path) -> list[Tweet]:
    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path, "r") as zf:
            if "data/tweets.js" not in zf.namelist():
                raise FileNotFoundError("data/tweets.js not found in archive zip")
            raw = zf.read("data/tweets.js").decode("utf-8")
    else:
        raw = input_path.read_text(encoding="utf-8")

    payload = json.loads(_strip_archive_prefix(raw))
    tweets: list[Tweet] = []

    for item in payload:
        tw = item.get("tweet", {})
        entities = tw.get("entities", {})
        extended_entities = tw.get("extended_entities", {})
        hashtags = [tag.get("text", "") for tag in entities.get("hashtags", []) if tag.get("text")]
        urls = [u.get("expanded_url", "") for u in entities.get("urls", []) if u.get("expanded_url")]
        media_entities = entities.get("media", []) + extended_entities.get("media", [])
        media_urls: list[str] = []
        for media in media_entities:
            media_url = media.get("media_url_https") or media.get("media_url")
            if media_url and media_url not in media_urls:
                media_urls.append(media_url)
        text = tw.get("full_text") or tw.get("text") or ""

        tweet = Tweet(
            id=tw.get("id_str", ""),
            created_at=_parse_datetime(tw.get("created_at", "Wed Jan 01 00:00:00 +0000 1970")),
            full_text=text,
            favorite_count=_to_int(tw.get("favorite_count")),
            retweet_count=_to_int(tw.get("retweet_count")),
            in_reply_to_status_id=tw.get("in_reply_to_status_id_str"),
            hashtags=hashtags,
            urls=urls,
            media_urls=media_urls,
            has_media=bool(media_entities),
        )
        if not tweet.id:
            continue
        if tweet.full_text.startswith("RT @"):
            continue
        tweets.append(tweet)

    tweets.sort(key=lambda t: t.created_at)
    return tweets


def _build_threads(tweets: list[Tweet]) -> list[list[Tweet]]:
    by_id: dict[str, Tweet] = {t.id: t for t in tweets}
    children: dict[str, list[Tweet]] = {}

    for tweet in tweets:
        parent_id = tweet.in_reply_to_status_id
        if parent_id and parent_id in by_id:
            children.setdefault(parent_id, []).append(tweet)

    visited: set[str] = set()
    threads: list[list[Tweet]] = []

    for tweet in tweets:
        if tweet.id in visited:
            continue
        is_root = not tweet.in_reply_to_status_id or tweet.in_reply_to_status_id not in by_id
        if not is_root:
            continue

        chain = [tweet]
        visited.add(tweet.id)
        cursor = tweet

        while True:
            next_candidates = sorted(children.get(cursor.id, []), key=lambda t: t.created_at)
            if len(next_candidates) != 1:
                break
            nxt = next_candidates[0]
            if nxt.id in visited:
                break
            chain.append(nxt)
            visited.add(nxt.id)
            cursor = nxt

        if len(chain) >= 2:
            threads.append(chain)

    return threads


def _topic_hits(text: str, hashtags: list[str]) -> list[tuple[TopicRule, int]]:
    haystack = f"{text.lower()} {' '.join(hashtags).lower()}"
    hits: list[tuple[TopicRule, int]] = []
    for rule in TOPIC_RULES:
        count = sum(1 for keyword in rule.keywords if _keyword_match(haystack, keyword))
        if count > 0:
            hits.append((rule, count))
    hits.sort(key=lambda item: item[1], reverse=True)
    return hits


def _score_tweet(tweet: Tweet, keyword_hits: int, thread_size: int) -> float:
    cleaned = _normalize_text(tweet.full_text)
    if len(cleaned) < 35:
        return 0.0

    engagement = tweet.favorite_count + (tweet.retweet_count * 2)
    engagement_score = math.log1p(engagement) * 0.9
    length_score = min(len(cleaned) / 260, 1.0) * 0.8
    keyword_score = min(keyword_hits, 4) * 0.5
    thread_bonus = min(thread_size, 6) * 0.15
    question_bonus = 0.25 if "?" in cleaned or "왜" in cleaned or "어떻게" in cleaned else 0.0
    image_bonus = 1.1 if tweet.has_media else 0.0
    _, book_bonus = _book_signal_info(cleaned)
    return (
        engagement_score
        + length_score
        + keyword_score
        + thread_bonus
        + question_bonus
        + book_bonus
        + image_bonus
    )


def _slugify(text: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "topic"


def _suggest_title(rule: TopicRule, top_tweet: Tweet) -> str:
    base = _excerpt(top_tweet.full_text, 54)
    if not base:
        return f"{rule.label}에서 배운 점"
    return f"{rule.label}: {base}"


def _tweet_url(tweet_id: str) -> str:
    return f"https://x.com/i/web/status/{tweet_id}"


def _is_blog_worthy(tweet: Tweet) -> bool:
    text = _normalize_text(tweet.full_text)
    book_signal_level, _ = _book_signal_info(text)

    if len(text) < 20:
        return False
    if len(text) < 35 and book_signal_level == 0 and not tweet.has_media:
        return False
    if not text.replace(" ", ""):
        return False
    if (
        tweet.favorite_count == 0
        and tweet.retweet_count == 0
        and len(text) < 90
        and book_signal_level == 0
        and not tweet.has_media
    ):
        return False
    return True


def select_topic_candidates(
    tweets: list[Tweet],
    max_topics: int,
    tweets_per_topic: int,
    min_score: float,
) -> list[dict[str, Any]]:
    threads = _build_threads(tweets)
    used_ids: set[str] = set()
    units: list[list[Tweet]] = []

    # Strict policy:
    # - One candidate post per contiguous thread chain.
    # - No cross-thread merge.
    for thread in threads:
        units.append(thread)
        for tweet in thread:
            used_ids.add(tweet.id)

    for tweet in tweets:
        if tweet.id not in used_ids:
            units.append([tweet])

    source_limit = max(1, tweets_per_topic)
    candidates: list[dict[str, Any]] = []

    for unit in units:
        if not unit:
            continue
        if not any(_is_blog_worthy(tweet) for tweet in unit):
            continue

        unit_text = " ".join(_normalize_text(tweet.full_text) for tweet in unit[:3])
        unit_hashtags = [tag for tweet in unit for tag in tweet.hashtags]
        hits = _topic_hits(unit_text, unit_hashtags)
        if not hits:
            continue
        best_rule, hit_count = hits[0]

        selected_tweets = unit[:source_limit]
        sources: list[dict[str, Any]] = []
        for tweet in selected_tweets:
            per_tweet_score = _score_tweet(tweet, hit_count, len(unit))
            book_signal_level, book_bonus = _book_signal_info(tweet.full_text)
            image_bonus = 1.1 if tweet.has_media else 0.0
            sources.append(
                {
                    "tweet_id": tweet.id,
                    "score": round(per_tweet_score, 3),
                    "book_signal_level": book_signal_level,
                    "book_bonus": round(book_bonus, 3),
                    "has_media": tweet.has_media,
                    "image_bonus": round(image_bonus, 3),
                    "created_at": tweet.created_at.isoformat(),
                    "favorite_count": tweet.favorite_count,
                    "retweet_count": tweet.retweet_count,
                    "excerpt": _excerpt(tweet.full_text, 120),
                    "text": _normalize_text(tweet.full_text),
                    "hashtags": tweet.hashtags,
                    "url": _tweet_url(tweet.id),
                    "media_urls": tweet.media_urls,
                }
            )

        aggregate_score = round(sum(source["score"] for source in sources) / len(sources), 3)
        if len(unit) > 1:
            aggregate_score = round(aggregate_score + min(len(unit), 8) * 0.08, 3)
        if aggregate_score < min_score:
            continue

        engagement_sum = sum(tweet.favorite_count + (tweet.retweet_count * 2) for tweet in unit)
        root_tweet = unit[0]
        candidates.append(
            {
                "topic_id": best_rule.topic_id,
                "topic_label": best_rule.label,
                "tags": list(best_rule.tags),
                "suggested_title": _suggest_title(best_rule, root_tweet),
                "aggregate_score": aggregate_score,
                "engagement_sum": engagement_sum,
                "tweet_count": len(unit),
                "tweet_ids": [tweet.id for tweet in unit],
                "sources": sources,
            }
        )

    candidates.sort(
        key=lambda item: (item["aggregate_score"], item["engagement_sum"], item["tweet_count"]),
        reverse=True,
    )
    return candidates[:max_topics]


def write_candidates_json(
    candidates: list[dict[str, Any]],
    input_path: Path,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input": str(input_path),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_candidates_markdown(
    candidates: list[dict[str, Any]],
    input_path: Path,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Curated Blog Topic Candidates")
    lines.append("")
    lines.append(
        f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    lines.append(f"- Source: `{input_path}`")
    lines.append(f"- Topic count: `{len(candidates)}`")
    lines.append("")
    lines.append(
        "선별 기준: 기술/커리어 관련성, 반응(Like/RT), 문장 밀도, 스레드 맥락, 독서/책 인용 가중치, 이미지 가중치"
    )
    lines.append("")

    for idx, candidate in enumerate(candidates, start=1):
        lines.append(f"## {idx}. {candidate['topic_label']}")
        lines.append("")
        lines.append(f"- Topic ID: `{candidate['topic_id']}`")
        lines.append(f"- Suggested title: `{candidate['suggested_title']}`")
        lines.append(f"- Aggregate score: `{candidate['aggregate_score']}`")
        lines.append(f"- Total engagement proxy: `{candidate['engagement_sum']}`")
        lines.append(f"- Tags: `{', '.join(candidate['tags'])}`")
        lines.append("- Source tweets:")
        for source in candidate["sources"][:5]:
            lines.append(
                f"  - {source['created_at'][:10]} | ❤ {source['favorite_count']} / RT {source['retweet_count']} | "
                f"[{source['tweet_id']}]({source['url']}) | {source['excerpt']} "
                f"(book_signal={source.get('book_signal_level', 0)}, book_bonus={source.get('book_bonus', 0.0)}, "
                f"has_media={source.get('has_media', False)}, image_bonus={source.get('image_bonus', 0.0)})"
            )
        lines.append("")

    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _build_draft_body(candidate: dict[str, Any]) -> str:
    title = candidate["suggested_title"].replace('"', "'")
    description = candidate["sources"][0]["excerpt"].replace('"', "'")
    tags_yaml = "\n".join(f"  - {tag}" for tag in candidate["tags"])
    first_source = candidate["sources"][0]
    created_at = str(first_source.get("created_at", ""))
    pub_date = (created_at[:10] if len(created_at) >= 10 else datetime.now().strftime("%Y-%m-%d"))
    original_tweet_url = str(first_source.get("url", "")).replace('"', "'")
    first_media_urls = [str(url) for url in first_source.get("media_urls", []) if str(url).strip()]
    thumbnail_yaml = f'thumbnail: "{first_media_urls[0]}"\n' if first_media_urls else ""

    source_blocks: list[str] = []
    for src in candidate["sources"][:8]:
        source_text = str(src.get("text", "")).strip()
        source_text = source_text if source_text else str(src.get("excerpt", "")).strip()
        media_urls = [str(url) for url in src.get("media_urls", []) if str(url).strip()]
        if media_urls:
            source_text = re.sub(r"\s+https://t\.co/[A-Za-z0-9]+/?\s*$", "", source_text).strip()
        block_lines: list[str] = [source_text]
        for media_url in media_urls:
            block_lines.append("")
            block_lines.append(f'<img class="tweet-image-inline" src="{media_url}" alt="tweet image" />')
        source_blocks.append("\n".join(block_lines).strip())

    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "{description}"\n'
        f"pubDate: {pub_date}\n"
        "source: twitter\n"
        f'originalTweetUrl: "{original_tweet_url}"\n'
        f"{thumbnail_yaml}"
        "tags:\n"
        f"{tags_yaml}\n"
        "---\n\n"
        + "\n\n".join(source_blocks).strip()
        + "\n"
    )


def _write_one_draft(candidate: dict[str, Any], output_dir: Path, index: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(candidate["topic_id"])
    file_name = f"{datetime.now().strftime('%Y%m%d')}-{index:02d}-{slug}.md"
    path = output_dir / file_name
    path.write_text(_build_draft_body(candidate), encoding="utf-8")
    return path


def write_drafts_parallel(
    candidates: list[dict[str, Any]],
    output_dir: Path,
    workers: int,
) -> list[Path]:
    results: list[Path] = []
    workers = max(1, workers)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_write_one_draft, candidate, output_dir, idx): candidate["topic_id"]
            for idx, candidate in enumerate(candidates, start=1)
        }
        for future in as_completed(futures):
            path = future.result()
            results.append(path)

    results.sort()
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent_blog_pipeline",
        description="Select blog-worthy topics from X archive, then generate parallel draft files.",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="Path to Twitter archive zip or tweets.js file",
    )
    parser.add_argument(
        "--mode",
        choices=("select", "write", "full"),
        default="full",
        help="select: topic list only, write: drafts from existing JSON, full: both",
    )
    parser.add_argument(
        "--candidate-json",
        type=Path,
        default=Path("docs/topic_candidates.json"),
        help="Output/input path for candidate JSON",
    )
    parser.add_argument(
        "--candidate-md",
        type=Path,
        default=Path("docs/topic_candidates.md"),
        help="Output path for human-readable candidate list",
    )
    parser.add_argument(
        "--draft-dir",
        type=Path,
        default=Path("drafts/curated"),
        help="Output folder for draft markdown files",
    )
    parser.add_argument("--max-topics", type=int, default=10, help="Number of topic candidates")
    parser.add_argument("--tweets-per-topic", type=int, default=8, help="Source tweets per topic")
    parser.add_argument("--min-score", type=float, default=2.2, help="Minimum score per tweet")
    parser.add_argument("--workers", type=int, default=4, help="Parallel writer agents")
    return parser.parse_args()


def _load_candidates_from_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("candidates", [])


def main() -> int:
    args = parse_args()

    if not args.archive.exists():
        raise FileNotFoundError(f"Archive path not found: {args.archive}")

    if args.mode in ("select", "full"):
        tweets = load_tweets_from_input(args.archive)
        candidates = select_topic_candidates(
            tweets=tweets,
            max_topics=args.max_topics,
            tweets_per_topic=args.tweets_per_topic,
            min_score=args.min_score,
        )
        write_candidates_json(candidates, args.archive, args.candidate_json)
        write_candidates_markdown(candidates, args.archive, args.candidate_md)
        print(f"[selector-agent] tweets loaded: {len(tweets)}")
        print(f"[selector-agent] candidates written: {len(candidates)}")
        print(f"[selector-agent] json -> {args.candidate_json}")
        print(f"[selector-agent] markdown -> {args.candidate_md}")
    else:
        candidates = _load_candidates_from_json(args.candidate_json)
        print(f"[selector-agent] loaded candidates from {args.candidate_json}: {len(candidates)}")

    if args.mode in ("write", "full"):
        paths = write_drafts_parallel(candidates, args.draft_dir, args.workers)
        print(f"[writer-agents] workers: {max(1, args.workers)}")
        print(f"[writer-agents] drafts written: {len(paths)}")
        print(f"[writer-agents] output dir: {args.draft_dir}")
        if paths:
            print("[writer-agents] sample:")
            for path in paths[:5]:
                print(f"  - {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
