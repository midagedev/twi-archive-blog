from __future__ import annotations

import argparse
from pathlib import Path

from .convert import export_markdown, load_tweets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="twi2blog",
        description="Convert your Twitter archive into Markdown blog drafts.",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("data/tweets.js"),
        help="Path to Twitter archive file (default: data/tweets.js)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("drafts"),
        help="Directory for markdown output (default: drafts)",
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        default=20,
        help="Include standalone tweets when likes >= this threshold (default: 20)",
    )
    parser.add_argument(
        "--min-retweets",
        type=int,
        default=5,
        help="Include standalone tweets when retweets >= this threshold (default: 5)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.archive.exists():
        parser.error(f"Archive file not found: {args.archive}")

    tweets = load_tweets(args.archive)
    summary = export_markdown(
        tweets=tweets,
        output_dir=args.out,
        min_likes=args.min_likes,
        min_retweets=args.min_retweets,
    )

    print(
        "Done: "
        f"{summary['written']} posts written "
        f"({summary['threads']} threads, {summary['singles']} single tweets)"
    )
    print(f"Output directory: {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
