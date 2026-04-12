#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PBS_URL_RE = re.compile(r"https://pbs\.twimg\.com/[^\s\"<>]+")
EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def _media_filename(url: str, content_type: str = "") -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    stem = path.replace("/", "-")
    suffix = Path(parsed.path).suffix

    if not suffix:
        query_format = parse_qs(parsed.query).get("format", [""])[0]
        suffix = f".{query_format}" if query_format else EXT_BY_CONTENT_TYPE.get(content_type.split(";")[0], "")
    if suffix and not stem.endswith(suffix):
        stem = f"{stem}{suffix}"

    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{digest}-{stem}"


def _local_media_url(url: str, output_dir: Path, content_type: str = "") -> tuple[Path, str]:
    filename = _media_filename(url, content_type)
    return output_dir / filename, f"/twitter-media/{filename}"


def _force_ipv4_dns() -> None:
    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo_ipv4(*args, **kwargs):
        return [
            result
            for result in original_getaddrinfo(*args, **kwargs)
            if result[0] == socket.AF_INET
        ]

    socket.getaddrinfo = getaddrinfo_ipv4


def _download(url: str, output_dir: Path, retries: int) -> str:
    existing_path, existing_url = _local_media_url(url, output_dir)
    if existing_path.exists():
        return existing_url

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                content_type = response.headers.get("content-type", "")
                data = response.read()
            break
        except (OSError, urllib.error.URLError) as error:
            last_error = error
            if attempt == retries:
                raise
            time.sleep(min(2 ** attempt, 8))
    else:
        raise RuntimeError(f"Failed to download {url}: {last_error}")

    if not content_type.startswith("image/"):
        raise ValueError(f"Unexpected content type for {url}: {content_type}")

    output_path, local_url = _local_media_url(url, output_dir, content_type)
    output_path.write_bytes(data)
    return local_url


def collect_urls(content_dir: Path) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for path in sorted(content_dir.glob("*.md*")):
        for url in PBS_URL_RE.findall(path.read_text(encoding="utf-8")):
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
    return urls


def rewrite_markdown(content_dir: Path, replacements: dict[str, str], dry_run: bool) -> int:
    changed = 0
    for path in sorted(content_dir.glob("*.md*")):
        original = path.read_text(encoding="utf-8")
        updated = original
        for src, dst in replacements.items():
            updated = updated.replace(src, dst)
        if updated == original:
            continue
        changed += 1
        if not dry_run:
            path.write_text(updated, encoding="utf-8")
    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="localize_tweet_media",
        description="Download pbs.twimg.com media referenced by Markdown and rewrite it to local public assets.",
    )
    parser.add_argument("--content-dir", type=Path, default=Path("blog/src/content/blog"))
    parser.add_argument("--media-dir", type=Path, default=Path("blog/public/twitter-media"))
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--allow-ipv6", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.media_dir.mkdir(parents=True, exist_ok=True)
    if not args.allow_ipv6:
        _force_ipv4_dns()

    urls = collect_urls(args.content_dir)
    replacements: dict[str, str] = {}
    for url in urls:
        local_url = _download(url, args.media_dir, args.retries)
        replacements[url] = local_url

    changed_files = rewrite_markdown(args.content_dir, replacements, args.dry_run)

    print(f"urls_found={len(urls)}")
    print(f"markdown_files_changed={changed_files}")
    print(f"media_dir={args.media_dir}")
    for src, dst in replacements.items():
        print(f"{src} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
