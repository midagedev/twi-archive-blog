from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Tweet:
    id: str
    created_at: datetime
    full_text: str
    favorite_count: int
    retweet_count: int
    in_reply_to_status_id: Optional[str]
    in_reply_to_user_id: Optional[str]
    hashtags: List[str]
    urls: List[str]
    has_media: bool


def _strip_archive_prefix(raw: str) -> str:
    # Twitter archive files often begin with JS assignment text.
    idx = raw.find("[")
    if idx == -1:
        raise ValueError("Could not find JSON array start '[' in archive file")
    return raw[idx:]


def _parse_datetime(value: str) -> datetime:
    # Example: "Wed Oct 10 20:19:24 +0000 2018"
    return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")


def _to_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_tweets(archive_path: Path) -> List[Tweet]:
    raw = archive_path.read_text(encoding="utf-8")
    payload = json.loads(_strip_archive_prefix(raw))

    tweets: List[Tweet] = []
    for item in payload:
        tw = item.get("tweet", {})
        entities = tw.get("entities", {})
        extended_entities = tw.get("extended_entities", {})
        hashtags = [tag.get("text", "") for tag in entities.get("hashtags", []) if tag.get("text")]
        urls = [u.get("expanded_url", "") for u in entities.get("urls", []) if u.get("expanded_url")]
        media_entities = entities.get("media", []) + extended_entities.get("media", [])
        text = tw.get("full_text") or tw.get("text") or ""

        tweets.append(
            Tweet(
                id=tw.get("id_str", ""),
                created_at=_parse_datetime(tw.get("created_at", "Wed Jan 01 00:00:00 +0000 1970")),
                full_text=text,
                favorite_count=_to_int(tw.get("favorite_count", "0")),
                retweet_count=_to_int(tw.get("retweet_count", "0")),
                in_reply_to_status_id=tw.get("in_reply_to_status_id_str"),
                in_reply_to_user_id=tw.get("in_reply_to_user_id_str"),
                hashtags=hashtags,
                urls=urls,
                has_media=bool(media_entities),
            )
        )

    tweets = [t for t in tweets if t.id and not t.full_text.startswith("RT @")]
    tweets.sort(key=lambda t: t.created_at)
    return tweets


def _normalize_title(text: str, fallback: str) -> str:
    cleaned = re.sub(r"https?://\S+", "", text)
    cleaned = re.sub(r"[#@]\w+", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = fallback
    cleaned = cleaned[:64].strip()
    return cleaned


def _safe_slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-") or "post"


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


def _strip_media_trailing_tco(text: str, has_media: bool) -> str:
    if not has_media:
        return text
    return re.sub(r"\s+https://t\.co/[A-Za-z0-9]+/?\s*$", "", text).strip()


def _build_threads(tweets: List[Tweet]) -> List[List[Tweet]]:
    by_id: Dict[str, Tweet] = {t.id: t for t in tweets}
    children: Dict[str, List[Tweet]] = {}

    for tweet in tweets:
        parent_id = tweet.in_reply_to_status_id
        if parent_id and parent_id in by_id:
            children.setdefault(parent_id, []).append(tweet)

    visited = set()
    threads: List[List[Tweet]] = []

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


def _render_post(title: str, tweets: List[Tweet], tags: List[str]) -> str:
    date_str = tweets[0].created_at.strftime("%Y-%m-%d")
    description = _normalize_title(tweets[0].full_text, "Twitter note")
    body_lines = [f"https://x.com/i/web/status/{tweets[0].id}", ""]
    for idx, tw in enumerate(tweets, start=1):
        body_lines.append(f"### {idx}")
        body_lines.append(_strip_media_trailing_tco(tw.full_text, tw.has_media))
        body_lines.append("")

    tag_yaml = "\n".join([f"  - {tag}" for tag in sorted(set(tags))]) if tags else "  - twitter"
    return (
        "---\n"
        f"title: \"{title}\"\n"
        f"description: \"{description}\"\n"
        f"pubDate: {date_str}\n"
        "source: twitter\n"
        "tags:\n"
        f"{tag_yaml}\n"
        "---\n\n"
        "## 원문\n\n"
        + "\n".join(body_lines).strip()
        + "\n"
    )


def export_markdown(
    tweets: List[Tweet],
    output_dir: Path,
    min_likes: int,
    min_retweets: int,
) -> Dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    thread_count = 0
    single_count = 0

    used_ids = set()
    threads = _build_threads(tweets)
    for thread in threads:
        title = _normalize_title(thread[0].full_text, "Twitter Thread")
        slug = _safe_slug(title)
        tags = [tag for t in thread for tag in t.hashtags]
        content = _render_post(title, thread, tags)
        path = output_dir / f"{thread[0].created_at.strftime('%Y%m%d')}-{thread[0].id}-{slug}.md"
        path.write_text(content, encoding="utf-8")

        written += 1
        thread_count += 1
        for t in thread:
            used_ids.add(t.id)

    for tweet in tweets:
        if tweet.id in used_ids:
            continue
        if (
            tweet.favorite_count < min_likes
            and tweet.retweet_count < min_retweets
            and _book_signal_level(tweet.full_text) == 0
            and not tweet.has_media
        ):
            continue

        title = _normalize_title(tweet.full_text, "Twitter Post")
        slug = _safe_slug(title)
        content = _render_post(title, [tweet], tweet.hashtags)
        path = output_dir / f"{tweet.created_at.strftime('%Y%m%d')}-{tweet.id}-{slug}.md"
        path.write_text(content, encoding="utf-8")

        written += 1
        single_count += 1

    return {
        "written": written,
        "threads": thread_count,
        "singles": single_count,
    }
