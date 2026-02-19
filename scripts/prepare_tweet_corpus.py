#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Tweet:
    id: str
    created_at: datetime
    text: str
    likes: int
    retweets: int
    reply_to: str | None
    urls: list[str]
    has_media: bool


def strip_js_prefix(raw: str) -> str:
    idx = raw.find("[")
    if idx == -1:
        raise ValueError("Could not parse archive payload")
    return raw[idx:]


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")


def to_int(value: str | int | None) -> int:
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def normalize_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def excerpt(text: str, limit: int = 120) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


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


def book_signal_info(text: str) -> tuple[int, float]:
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
        return 2, 2.4
    return 1, 1.2


def load_tweets(path: Path) -> list[Tweet]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            if "data/tweets.js" not in zf.namelist():
                raise FileNotFoundError("data/tweets.js not found in zip archive")
            raw = zf.read("data/tweets.js").decode("utf-8")
    else:
        raw = path.read_text(encoding="utf-8")

    payload = json.loads(strip_js_prefix(raw))
    tweets: list[Tweet] = []
    for item in payload:
        tw = item.get("tweet", {})
        text = tw.get("full_text") or tw.get("text") or ""
        if not text:
            continue
        if text.startswith("RT @"):
            continue
        entities = tw.get("entities", {})
        extended_entities = tw.get("extended_entities", {})
        urls = [u.get("expanded_url", "") for u in entities.get("urls", []) if u.get("expanded_url")]
        media_entities = entities.get("media", []) + extended_entities.get("media", [])
        tweet = Tweet(
            id=tw.get("id_str", ""),
            created_at=parse_dt(tw.get("created_at", "Wed Jan 01 00:00:00 +0000 1970")),
            text=text,
            likes=to_int(tw.get("favorite_count")),
            retweets=to_int(tw.get("retweet_count")),
            reply_to=tw.get("in_reply_to_status_id_str"),
            urls=urls,
            has_media=bool(media_entities),
        )
        if tweet.id:
            tweets.append(tweet)
    tweets.sort(key=lambda t: t.created_at)
    return tweets


def build_threads(tweets: list[Tweet]) -> list[list[Tweet]]:
    by_id = {t.id: t for t in tweets}
    children: dict[str, list[Tweet]] = {}

    for tweet in tweets:
        parent = tweet.reply_to
        if parent and parent in by_id:
            children.setdefault(parent, []).append(tweet)

    visited: set[str] = set()
    threads: list[list[Tweet]] = []
    for tweet in tweets:
        if tweet.id in visited:
            continue
        is_root = not tweet.reply_to or tweet.reply_to not in by_id
        if not is_root:
            continue

        chain = [tweet]
        visited.add(tweet.id)
        cursor = tweet
        while True:
            next_items = sorted(children.get(cursor.id, []), key=lambda t: t.created_at)
            if len(next_items) != 1:
                break
            nxt = next_items[0]
            if nxt.id in visited:
                break
            chain.append(nxt)
            visited.add(nxt.id)
            cursor = nxt
        threads.append(chain)
    return threads


def score_unit(text: str, likes: int, retweets: int, thread_size: int, has_media: bool) -> float:
    engagement = likes + (retweets * 2)
    engagement_score = math.log1p(engagement) * 1.2
    density_score = min(len(normalize_text(text)) / 280, 1.0) * 0.9
    thread_bonus = math.log2(thread_size + 1) * 0.8
    question_bonus = 0.25 if "?" in text or "왜" in text or "어떻게" in text else 0.0
    image_bonus = 1.2 if has_media else 0.0
    _, book_bonus = book_signal_info(text)
    return round(
        engagement_score + density_score + thread_bonus + question_bonus + book_bonus + image_bonus,
        4,
    )


def build_units(tweets: list[Tweet]) -> list[dict]:
    threads = build_threads(tweets)
    thread_root_ids = {thread[0].id for thread in threads if len(thread) >= 2}
    by_id = {t.id: t for t in tweets}
    units: list[dict] = []

    for thread in threads:
        root = thread[0]
        if len(thread) < 2:
            continue
        text = " ".join(normalize_text(t.text) for t in thread[:3])
        has_media = any(t.has_media for t in thread)
        book_signal_level, book_bonus = book_signal_info(text)
        image_bonus = 1.2 if has_media else 0.0
        likes = sum(t.likes for t in thread)
        retweets = sum(t.retweets for t in thread)
        units.append(
            {
                "unit_type": "thread",
                "tweet_ids": [t.id for t in thread],
                "date": root.created_at.strftime("%Y-%m-%d"),
                "score": score_unit(text, likes, retweets, len(thread), has_media),
                "likes": likes,
                "retweets": retweets,
                "headline": excerpt(root.text, 140),
                "snippets": [excerpt(t.text, 180) for t in thread[:3]],
                "urls": [f"https://x.com/i/web/status/{t.id}" for t in thread[:3]],
                "book_signal_level": book_signal_level,
                "book_bonus": book_bonus,
                "has_media": has_media,
                "image_bonus": image_bonus,
            }
        )

    for tweet in tweets:
        if tweet.id in thread_root_ids:
            continue
        text = normalize_text(tweet.text)
        book_signal_level, book_bonus = book_signal_info(text)
        if len(text) < 35 and not tweet.has_media and book_signal_level == 0:
            continue
        if (
            tweet.likes == 0
            and tweet.retweets == 0
            and len(text) < 90
            and not tweet.has_media
            and book_signal_level == 0
        ):
            continue
        image_bonus = 1.2 if tweet.has_media else 0.0
        units.append(
            {
                "unit_type": "single",
                "tweet_ids": [tweet.id],
                "date": tweet.created_at.strftime("%Y-%m-%d"),
                "score": score_unit(tweet.text, tweet.likes, tweet.retweets, 1, tweet.has_media),
                "likes": tweet.likes,
                "retweets": tweet.retweets,
                "headline": excerpt(tweet.text, 140),
                "snippets": [excerpt(tweet.text, 180)],
                "urls": [f"https://x.com/i/web/status/{tweet.id}"],
                "book_signal_level": book_signal_level,
                "book_bonus": book_bonus,
                "has_media": tweet.has_media,
                "image_bonus": image_bonus,
            }
        )

    units.sort(key=lambda u: (u["score"], u["likes"] + (u["retweets"] * 2)), reverse=True)
    return units


def write_outputs(
    units: list[dict],
    tweets: list[Tweet],
    out_dir: Path,
    max_items: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if max_items <= 0:
        selected = units
    else:
        selected = units[:max_items]

    lookup = {
        t.id: {
            "id": t.id,
            "date": t.created_at.strftime("%Y-%m-%d"),
            "created_at": t.created_at.isoformat(),
            "likes": t.likes,
            "retweets": t.retweets,
            "text": normalize_text(t.text),
            "url": f"https://x.com/i/web/status/{t.id}",
            "has_media": t.has_media,
        }
        for t in tweets
    }

    (out_dir / "tweet_lookup.json").write_text(
        json.dumps(lookup, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "tweet_corpus.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append("# Tweet Corpus For Codex Subagents")
    lines.append("")
    lines.append(f"- item_count: {len(selected)}")
    lines.append(
        "- note: score is engagement + narrative density + thread bonus + book-reading bonus + image bonus"
    )
    lines.append("")
    for idx, unit in enumerate(selected, start=1):
        lines.append(f"## ITEM {idx:03d}")
        lines.append(f"- unit_type: {unit['unit_type']}")
        lines.append(f"- tweet_ids: {', '.join(unit['tweet_ids'])}")
        lines.append(f"- date: {unit['date']}")
        lines.append(f"- score: {unit['score']}")
        lines.append(f"- book_signal_level: {unit.get('book_signal_level', 0)}")
        lines.append(f"- book_bonus: {unit.get('book_bonus', 0.0)}")
        lines.append(f"- has_media: {unit.get('has_media', False)}")
        lines.append(f"- image_bonus: {unit.get('image_bonus', 0.0)}")
        lines.append(f"- likes: {unit['likes']}")
        lines.append(f"- retweets: {unit['retweets']}")
        lines.append(f"- headline: {unit['headline']}")
        lines.append("- snippets:")
        for snippet in unit["snippets"]:
            lines.append(f"  - {snippet}")
        lines.append("- urls:")
        for url in unit["urls"]:
            lines.append(f"  - {url}")
        lines.append("")

    (out_dir / "tweet_corpus.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare tweet corpus for Codex subagents")
    parser.add_argument("--archive", type=Path, required=True, help="Twitter archive zip or tweets.js")
    parser.add_argument("--out-dir", type=Path, default=Path(".tmp/codex_pipeline"), help="Output directory")
    parser.add_argument("--max-items", type=int, default=320, help="Max corpus items")
    args = parser.parse_args()

    tweets = load_tweets(args.archive)
    units = build_units(tweets)
    write_outputs(units, tweets, args.out_dir, args.max_items)

    print(f"tweets_loaded={len(tweets)}")
    print(f"units_built={len(units)}")
    selected_count = len(units) if args.max_items <= 0 else min(len(units), args.max_items)
    print(f"selected={selected_count}")
    print(f"out_dir={args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
