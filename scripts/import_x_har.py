#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from agent_curation_pipeline import _safe_title_excerpt, _slugify, _topic_for


STATUS_ID_RE = re.compile(r"/status/(\d+)")
TWITTER_EPOCH_MS = 1288834974657


@dataclass
class Tweet:
    id: str
    created_at: datetime
    text: str
    author_screen_name: str
    favorite_count: int
    retweet_count: int
    in_reply_to_status_id: str | None
    in_reply_to_screen_name: str | None
    conversation_id: str | None
    hashtags: list[str]
    media_urls: list[str]

    @property
    def url(self) -> str:
        return f"https://x.com/i/web/status/{self.id}"


def _to_int(value: Any) -> int:
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _normalize_handle(value: str) -> str:
    return value.strip().lstrip("@").lower()


def _tweet_datetime_from_id(tweet_id: str) -> datetime | None:
    try:
        timestamp_ms = (int(tweet_id) >> 22) + TWITTER_EPOCH_MS
    except ValueError:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def _parse_twitter_datetime(value: Any, tweet_id: str = "") -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return _tweet_datetime_from_id(tweet_id)
    raw = str(value).strip()
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(raw.replace("Z", "+0000"), fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return _tweet_datetime_from_id(tweet_id)


def _normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _excerpt(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _unwrap_result(value: Any) -> Any:
    current = value
    while isinstance(current, dict):
        if set(current.keys()) == {"result"}:
            current = current["result"]
            continue
        if "tweet" in current and current.get("__typename") == "TweetWithVisibilityResults":
            current = current["tweet"]
            continue
        break
    return current


def _screen_name_from_user_result(value: Any) -> str:
    current = _unwrap_result(value)
    if not isinstance(current, dict):
        return ""

    legacy = current.get("legacy")
    if isinstance(legacy, dict) and legacy.get("screen_name"):
        return str(legacy["screen_name"])

    core = current.get("core")
    if isinstance(core, dict) and core.get("screen_name"):
        return str(core["screen_name"])

    if current.get("screen_name"):
        return str(current["screen_name"])

    user_results = current.get("user_results")
    if isinstance(user_results, dict):
        return _screen_name_from_user_result(user_results.get("result"))

    return ""


def _author_screen_name(node: dict[str, Any]) -> str:
    core = node.get("core")
    if isinstance(core, dict):
        user_results = core.get("user_results")
        if isinstance(user_results, dict):
            screen_name = _screen_name_from_user_result(user_results.get("result"))
            if screen_name:
                return screen_name

    user_results = node.get("user_results")
    if isinstance(user_results, dict):
        screen_name = _screen_name_from_user_result(user_results.get("result"))
        if screen_name:
            return screen_name

    user = node.get("user")
    if isinstance(user, dict):
        screen_name = _screen_name_from_user_result(user)
        if screen_name:
            return screen_name

    legacy = node.get("legacy")
    if isinstance(legacy, dict) and legacy.get("screen_name"):
        return str(legacy["screen_name"])

    return ""


def _url_entities(*entity_sets: Any) -> list[dict[str, Any]]:
    urls: list[dict[str, Any]] = []
    for entity_set in entity_sets:
        if not isinstance(entity_set, dict):
            continue
        for row in entity_set.get("urls", []) or []:
            if isinstance(row, dict):
                urls.append(row)
    return urls


def _replace_tco_urls(text: str, urls: list[dict[str, Any]]) -> str:
    result = text
    for row in urls:
        short_url = str(row.get("url") or "").strip()
        expanded_url = str(row.get("expanded_url") or row.get("expanded") or "").strip()
        if short_url and expanded_url:
            result = result.replace(short_url, expanded_url)
    return result


def _hashtags_from_entities(*entity_sets: Any) -> list[str]:
    tags: list[str] = []
    for entity_set in entity_sets:
        if not isinstance(entity_set, dict):
            continue
        for row in entity_set.get("hashtags", []) or []:
            if isinstance(row, dict) and row.get("text"):
                tags.append(str(row["text"]))
    return _unique(tags)


def _media_urls_from_entities(*entity_sets: Any) -> list[str]:
    media_urls: list[str] = []
    for entity_set in entity_sets:
        if not isinstance(entity_set, dict):
            continue
        for row in entity_set.get("media", []) or []:
            if not isinstance(row, dict):
                continue
            media_url = str(row.get("media_url_https") or row.get("media_url") or "").strip()
            if media_url:
                media_urls.append(media_url)
    return _unique(media_urls)


def _note_tweet(node: dict[str, Any]) -> dict[str, Any]:
    note_tweet = node.get("note_tweet")
    if not isinstance(note_tweet, dict):
        return {}
    note_results = note_tweet.get("note_tweet_results")
    if not isinstance(note_results, dict):
        return {}
    note_result = note_results.get("result")
    return note_result if isinstance(note_result, dict) else {}


def _tweet_from_node(node: dict[str, Any], user_by_id: dict[str, str] | None = None) -> Tweet | None:
    node = _unwrap_result(node)
    if not isinstance(node, dict):
        return None

    legacy = node.get("legacy")
    if not isinstance(legacy, dict):
        legacy = node

    tweet_id = str(node.get("rest_id") or legacy.get("id_str") or node.get("id_str") or "").strip()
    if not tweet_id:
        return None

    note = _note_tweet(node)
    note_entities = note.get("entity_set") if isinstance(note, dict) else {}
    legacy_entities = legacy.get("entities") if isinstance(legacy, dict) else {}
    extended_entities = legacy.get("extended_entities") if isinstance(legacy, dict) else {}

    legacy_text = str(legacy.get("full_text") or legacy.get("text") or "").strip()
    note_text = str(note.get("text") or "").strip() if isinstance(note, dict) else ""
    text = note_text if len(note_text) > len(legacy_text) else legacy_text
    if not text:
        return None

    created_at = _parse_twitter_datetime(legacy.get("created_at") or node.get("created_at"), tweet_id)
    if created_at is None:
        return None

    author = _author_screen_name(node)
    if not author and user_by_id:
        user_id = str(legacy.get("user_id_str") or legacy.get("user_id") or "").strip()
        author = user_by_id.get(user_id, "")

    media_urls = _media_urls_from_entities(legacy_entities, extended_entities, note_entities)
    text = _replace_tco_urls(text, _url_entities(legacy_entities, note_entities))
    if media_urls:
        text = re.sub(r"\s+https://t\.co/[A-Za-z0-9]+/?\s*$", "", text).strip()

    return Tweet(
        id=tweet_id,
        created_at=created_at,
        text=_normalize_text(text),
        author_screen_name=author,
        favorite_count=_to_int(legacy.get("favorite_count")),
        retweet_count=_to_int(legacy.get("retweet_count")),
        in_reply_to_status_id=(
            str(legacy.get("in_reply_to_status_id_str") or legacy.get("in_reply_to_status_id") or "").strip() or None
        ),
        in_reply_to_screen_name=(
            str(legacy.get("in_reply_to_screen_name") or "").strip().lstrip("@") or None
        ),
        conversation_id=(str(legacy.get("conversation_id_str") or "").strip() or None),
        hashtags=_hashtags_from_entities(legacy_entities, note_entities),
        media_urls=media_urls,
    )


def _global_object_tweets(payload: dict[str, Any]) -> list[Tweet]:
    global_objects = payload.get("globalObjects")
    if not isinstance(global_objects, dict):
        return []

    users = global_objects.get("users") if isinstance(global_objects.get("users"), dict) else {}
    user_by_id = {
        str(user_id): str(user.get("screen_name") or "")
        for user_id, user in users.items()
        if isinstance(user, dict) and user.get("screen_name")
    }

    tweets = global_objects.get("tweets") if isinstance(global_objects.get("tweets"), dict) else {}
    parsed: list[Tweet] = []
    for row in tweets.values():
        if not isinstance(row, dict):
            continue
        tweet = _tweet_from_node(row, user_by_id)
        if tweet:
            parsed.append(tweet)
    return parsed


def _walk_json(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _tweets_from_payload(payload: Any) -> list[Tweet]:
    tweets: dict[str, Tweet] = {}
    for node in _walk_json(payload):
        if not isinstance(node, dict):
            continue

        for tweet in _global_object_tweets(node):
            tweets[tweet.id] = _merge_tweets(tweets.get(tweet.id), tweet)

        candidate = node
        if "tweet_results" in node and isinstance(node["tweet_results"], dict):
            candidate = node["tweet_results"].get("result")
        tweet = _tweet_from_node(candidate)
        if tweet:
            tweets[tweet.id] = _merge_tweets(tweets.get(tweet.id), tweet)

    return list(tweets.values())


def _merge_tweets(existing: Tweet | None, incoming: Tweet) -> Tweet:
    if existing is None:
        return incoming
    if len(incoming.text) > len(existing.text):
        base = incoming
        other = existing
    else:
        base = existing
        other = incoming
    return Tweet(
        id=base.id,
        created_at=base.created_at,
        text=base.text,
        author_screen_name=base.author_screen_name or other.author_screen_name,
        favorite_count=max(base.favorite_count, other.favorite_count),
        retweet_count=max(base.retweet_count, other.retweet_count),
        in_reply_to_status_id=base.in_reply_to_status_id or other.in_reply_to_status_id,
        in_reply_to_screen_name=base.in_reply_to_screen_name or other.in_reply_to_screen_name,
        conversation_id=base.conversation_id or other.conversation_id,
        hashtags=_unique([*base.hashtags, *other.hashtags]),
        media_urls=_unique([*base.media_urls, *other.media_urls]),
    )


def _decode_har_content(content: dict[str, Any]) -> str:
    text = content.get("text")
    if not isinstance(text, str) or not text:
        return ""
    if content.get("encoding") == "base64":
        try:
            return base64.b64decode(text).decode("utf-8", "replace")
        except ValueError:
            return ""
    return text


def _json_from_response_body(body: str) -> Any | None:
    stripped = body.strip()
    if stripped.startswith("for (;;);"):
        stripped = stripped[len("for (;;);") :].strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def load_tweets_from_har(har_path: Path) -> tuple[list[Tweet], int, int]:
    payload = json.loads(har_path.read_text(encoding="utf-8"))
    entries = payload.get("log", {}).get("entries", []) if isinstance(payload, dict) else []
    if isinstance(payload, list):
        entries = payload
    if not isinstance(entries, list):
        raise ValueError("HAR file does not contain log.entries")

    tweets_by_id: dict[str, Tweet] = {}
    json_payload_count = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        response = entry.get("response")
        if not isinstance(response, dict):
            continue
        content = response.get("content")
        if not isinstance(content, dict):
            continue

        body = _decode_har_content(content)
        json_payload = _json_from_response_body(body)
        if json_payload is None:
            continue
        json_payload_count += 1

        for tweet in _tweets_from_payload(json_payload):
            tweets_by_id[tweet.id] = _merge_tweets(tweets_by_id.get(tweet.id), tweet)

    return list(tweets_by_id.values()), len(entries), json_payload_count


def collect_existing_tweet_ids(content_dir: Path, candidate_json: Path | None = None) -> set[str]:
    existing: set[str] = set()
    if content_dir.exists():
        for path in content_dir.glob("*.md*"):
            text = path.read_text(encoding="utf-8")
            existing.update(STATUS_ID_RE.findall(text))

    if candidate_json and candidate_json.exists():
        payload = json.loads(candidate_json.read_text(encoding="utf-8"))
        candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            for tweet_id in candidate.get("tweet_ids", []) or []:
                existing.add(str(tweet_id))
            for source in candidate.get("sources", []) or []:
                if isinstance(source, dict) and source.get("tweet_id"):
                    existing.add(str(source["tweet_id"]))
    return existing


def infer_latest_pub_date(content_dir: Path) -> date | None:
    latest: date | None = None
    if not content_dir.exists():
        return None
    for path in content_dir.glob("*.md*"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^pubDate:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.MULTILINE)
        if not match:
            continue
        current = date.fromisoformat(match.group(1))
        if latest is None or current > latest:
            latest = current
    return latest


def resolve_since_date(value: str, content_dir: Path) -> date | None:
    normalized = value.strip().lower()
    if normalized in {"auto", ""}:
        return infer_latest_pub_date(content_dir)
    if normalized in {"none", "all"}:
        return None
    return date.fromisoformat(value)


def select_new_tweets(
    tweets: list[Tweet],
    *,
    handle: str,
    since_date: date | None,
    existing_ids: set[str],
    include_replies: bool,
    min_likes: int,
    min_retweets: int,
) -> list[Tweet]:
    expected_handle = _normalize_handle(handle)
    selected: list[Tweet] = []
    for tweet in tweets:
        author = _normalize_handle(tweet.author_screen_name)
        if expected_handle and author != expected_handle:
            continue
        if tweet.id in existing_ids:
            continue
        if since_date and tweet.created_at.date() < since_date:
            continue
        if tweet.text.startswith("RT @"):
            continue
        if tweet.favorite_count < min_likes and tweet.retweet_count < min_retweets:
            continue
        if not include_replies and tweet.in_reply_to_status_id:
            reply_to_self = _normalize_handle(tweet.in_reply_to_screen_name or "") == expected_handle
            if not reply_to_self:
                continue
        selected.append(tweet)

    selected.sort(key=lambda item: (item.created_at, int(item.id)))
    return selected


def build_post_groups(tweets: list[Tweet]) -> list[list[Tweet]]:
    by_id = {tweet.id: tweet for tweet in tweets}
    adjacency: dict[str, set[str]] = {tweet.id: set() for tweet in tweets}

    for tweet in tweets:
        parent_id = tweet.in_reply_to_status_id
        if parent_id and parent_id in by_id:
            adjacency[tweet.id].add(parent_id)
            adjacency[parent_id].add(tweet.id)

    visited: set[str] = set()
    groups: list[list[Tweet]] = []

    for tweet in tweets:
        if tweet.id in visited:
            continue
        stack = [tweet.id]
        component_ids: list[str] = []
        while stack:
            current_id = stack.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            component_ids.append(current_id)
            stack.extend(sorted(adjacency.get(current_id, set()) - visited))
        groups.append(sorted((by_id[tweet_id] for tweet_id in component_ids), key=lambda item: item.created_at))

    groups.sort(key=lambda group: (group[0].created_at, int(group[0].id)))
    return groups


def _next_file_index(output_dir: Path, date_prefix: str) -> int:
    highest = 0
    pattern = re.compile(rf"^{re.escape(date_prefix)}-(\d{{3}})-")
    for path in output_dir.glob(f"{date_prefix}-*.md"):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def _render_media(media_urls: list[str]) -> list[str]:
    lines: list[str] = []
    for media_url in media_urls:
        lines.append("")
        lines.append(f'<p class="tweet-image-row"><img class="tweet-image-inline" src="{media_url}" alt="tweet image" /></p>')
    return lines


def render_markdown(group: list[Tweet]) -> str:
    primary = group[0]
    topic_rule = _topic_for(primary.text, primary.hashtags)
    title = _safe_title_excerpt(primary.text, "", 72).replace('"', "'")
    description = _excerpt(primary.text, 180).replace('"', "'")
    thumbnail = next((tweet.media_urls[0] for tweet in group if tweet.media_urls), "")
    tags = list(topic_rule.tags)
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags) if tags else "  - twitter"

    frontmatter_lines = [
        "---",
        f"title: {_yaml_string(title)}",
        f"description: {_yaml_string(description)}",
        f"pubDate: {primary.created_at.date().isoformat()}",
        "source: twitter",
        f"originalTweetUrl: {_yaml_string(primary.url)}",
    ]
    if thumbnail:
        frontmatter_lines.append(f"thumbnail: {_yaml_string(thumbnail)}")
    frontmatter_lines.extend(["tags:", tags_yaml, "---"])

    body_lines: list[str] = []
    if len(group) == 1:
        body_lines.append(primary.text)
        body_lines.extend(_render_media(primary.media_urls))
    else:
        for index, tweet in enumerate(group, start=1):
            body_lines.append(f"### {index}")
            body_lines.append(tweet.text)
            body_lines.extend(_render_media(tweet.media_urls))
            body_lines.append("")

    return "\n".join(frontmatter_lines) + "\n\n" + "\n".join(body_lines).strip() + "\n"


def write_posts(groups: list[list[Tweet]], output_dir: Path, dry_run: bool) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_prefix = datetime.now().strftime("%Y%m%d")
    next_index = _next_file_index(output_dir, date_prefix)
    written: list[Path] = []

    for group in groups:
        topic_rule = _topic_for(group[0].text, group[0].hashtags)
        file_name = f"{date_prefix}-{next_index:03d}-{_slugify(topic_rule.topic_id)}.md"
        next_index += 1
        path = output_dir / file_name
        if not dry_run:
            path.write_text(render_markdown(group), encoding="utf-8")
        written.append(path)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="import_x_har",
        description="Import public X/Twitter posts captured in a browser HAR into Astro blog markdown.",
    )
    parser.add_argument("--har", type=Path, required=True, help="Path to a HAR file saved with response content")
    parser.add_argument("--out-dir", type=Path, default=Path("blog/src/content/blog"), help="Markdown output directory")
    parser.add_argument(
        "--existing-candidate-json",
        type=Path,
        default=Path("docs/topic_candidates.json"),
        help="Existing candidate JSON with tweet_ids to skip",
    )
    parser.add_argument("--handle", default="midagedev", help="X/Twitter handle to import, with or without @")
    parser.add_argument(
        "--since-date",
        default="auto",
        help="Only import tweets on/after YYYY-MM-DD. Use 'auto' to infer latest existing pubDate, or 'none' for all.",
    )
    parser.add_argument("--include-replies", action="store_true", help="Include replies to other accounts")
    parser.add_argument("--min-likes", type=int, default=0, help="Minimum likes for standalone import")
    parser.add_argument("--min-retweets", type=int, default=0, help="Minimum retweets for standalone import")
    parser.add_argument("--limit", type=int, default=0, help="Maximum post groups to write after filtering")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without creating files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.har.exists():
        raise FileNotFoundError(f"HAR path not found: {args.har}")

    since_date = resolve_since_date(args.since_date, args.out_dir)
    existing_ids = collect_existing_tweet_ids(args.out_dir, args.existing_candidate_json)
    tweets, entry_count, json_payload_count = load_tweets_from_har(args.har)
    selected_tweets = select_new_tweets(
        tweets,
        handle=args.handle,
        since_date=since_date,
        existing_ids=existing_ids,
        include_replies=args.include_replies,
        min_likes=args.min_likes,
        min_retweets=args.min_retweets,
    )
    groups = build_post_groups(selected_tweets)
    if args.limit > 0:
        groups = groups[: args.limit]

    paths = write_posts(groups, args.out_dir, args.dry_run)

    print(f"har_entries={entry_count}")
    print(f"json_payloads_scanned={json_payload_count}")
    print(f"tweets_found={len(tweets)}")
    print(f"existing_tweet_ids={len(existing_ids)}")
    print(f"since_date={since_date.isoformat() if since_date else 'none'}")
    print(f"selected_tweets={len(selected_tweets)}")
    print(f"post_groups={len(groups)}")
    print(f"dry_run={args.dry_run}")
    for path, group in zip(paths, groups):
        first = group[0]
        title = _excerpt(first.text, 84)
        print(f"{path} <- {first.created_at.date().isoformat()} {first.id} {title}")

    if json_payload_count == 0:
        print("No JSON response bodies were found. Save the HAR with response content enabled.")
    elif tweets and not selected_tweets:
        print("Tweets were found, but none matched the handle/date/reply/duplicate filters.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
