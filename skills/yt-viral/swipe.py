#!/usr/bin/env python3
"""swipe.py - rank collected videos by how far each beat its OWN channel, then name the formula.

    python3 swipe.py collected.json
    python3 swipe.py collected.json --min 2.0 --json

Input is a list you collected - one object per video:

    [{"channel":"Some Channel","title":"...","views":412000,"url":"...","duration":613}, ...]

Raw view counts rank channel size, not ideas. A 400k video on a 2M-subscriber channel is a normal
Tuesday; a 400k video on a channel whose median is 30k is the thing worth studying. So every video
is scored as a MULTIPLE OF ITS OWN CHANNEL'S MEDIAN, which needs at least four videos per channel
to mean anything - the tool says so rather than quietly ranking on noise.

The formula comes from skills/yt-script/hooks.json, matched against the TITLE. It is a judgement
about the words on screen, not a claim about why the video worked.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_VIDEOS_PER_CHANNEL = 4
DEFAULT_MIN_MULTIPLE = 1.5
MAX_TEXT_ROWS = 25
MAX_THIN_CHANNELS_SHOWN = 6


@dataclass(frozen=True)
class Formula:
    name: str
    patterns: tuple[re.Pattern[str], ...]


def load_formulas() -> list[Formula]:
    """Load the 21 title formulas, compiling every pattern once up front.

    Looks next to this file first (a copied skill folder), then in the package's sibling
    yt-script directory. An invalid pattern fails here, with the file named, instead of
    halfway through a run.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here / "hooks.json", here.parent / "yt-script" / "hooks.json"):
        if candidate.exists():
            path = candidate
            break
    else:
        raise FileNotFoundError("hooks.json not found next to swipe.py or in ../yt-script/")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        hooks = data["hooks"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"{path}: invalid hooks file: {exc}") from exc
    formulas: list[Formula] = []
    for item in hooks:
        try:
            patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in item["match"])
        except re.error as exc:
            raise ValueError(f"{path}: invalid pattern in formula {item.get('name')!r}: {exc}") from exc
        formulas.append(Formula(name=str(item["name"]), patterns=patterns))
    return formulas


def classify(title: str, formulas: list[Formula]) -> str:
    """Name the formula whose patterns match the title most. Ties break alphabetically.

    This judges the words on screen only - never a claim about why the video worked.
    """
    scored = [
        (sum(1 for pattern in formula.patterns if pattern.search(title)), formula.name)
        for formula in formulas
    ]
    scored = [(hits, name) for hits, name in scored if hits]
    if not scored:
        return "Unclassified"
    return max(scored)[1]


def coerce_views(value: object) -> float | None:
    """Coerce a view count to float. Returns None for missing or non-numeric values."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def load_collected(path: str | Path) -> list[dict[str, object]]:
    """Read collected videos: a JSON list, or a dict with a ``videos`` list."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("videos", [])
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list of videos")
    rows = [row for row in data if isinstance(row, dict)]
    if len(rows) != len(data):
        raise ValueError(f"{path}: every video must be a JSON object")
    return rows


def rank(
    rows: list[dict[str, object]], formulas: list[Formula], minimum: float
) -> tuple[list[dict[str, object]], list[tuple[str, int]], int]:
    """Rank videos by multiple of their own channel's median.

    Returns (outliers, thin_channels, skipped_invalid): channels with fewer than
    MIN_VIDEOS_PER_CHANNEL videos are reported as thin, never ranked; rows with
    unusable view counts are skipped and counted.
    """
    by_channel: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        channel = str(row.get("channel") or "?")
        by_channel.setdefault(channel, []).append(row)
    outliers: list[dict[str, object]] = []
    thin: list[tuple[str, int]] = []
    skipped_invalid = 0
    for channel, videos in by_channel.items():
        views: list[float] = []
        usable: list[dict[str, object]] = []
        for video in videos:
            parsed = coerce_views(video.get("views", 0))
            if parsed is None:
                skipped_invalid += 1
                continue
            views.append(parsed)
            usable.append(video)
        if len(videos) < MIN_VIDEOS_PER_CHANNEL:
            thin.append((channel, len(videos)))
            continue
        median = statistics.median(views) if views else 0.0
        for video, view_count in zip(usable, views):
            multiple = (view_count / median) if median else 0.0
            if multiple < minimum:
                continue
            title = str(video.get("title") or "")
            outliers.append(
                {
                    "channel": channel,
                    "title": title,
                    "views": int(view_count),
                    "median": int(median),
                    "multiple": round(multiple, 2),
                    "formula": classify(title, formulas),
                    "url": str(video.get("url") or ""),
                }
            )
    outliers.sort(key=lambda row: -float(row["multiple"]))
    return outliers, thin, skipped_invalid


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank collected videos by multiple of their own channel's median.",
        epilog="Input JSON: a list of {channel, title, views, url, duration}. At least 4 videos per channel.",
    )
    parser.add_argument("collected", help="collected.json file")
    parser.add_argument(
        "--min",
        type=float,
        default=DEFAULT_MIN_MULTIPLE,
        help=f"only show videos at or above this multiple (default: {DEFAULT_MIN_MULTIPLE})",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.min < 0:
        print("swipe: --min must not be negative", file=sys.stderr)
        return 2
    try:
        formulas = load_formulas()
    except (OSError, ValueError) as exc:
        print(f"swipe: {exc}", file=sys.stderr)
        return 1
    try:
        rows = load_collected(args.collected)
    except (OSError, ValueError) as exc:
        print(f"swipe: {exc}", file=sys.stderr)
        return 1
    outliers, thin, skipped_invalid = rank(rows, formulas, args.min)
    channel_count = len({str(row.get("channel") or "?") for row in rows})
    if args.json:
        print(
            json.dumps(
                {
                    "outliers": outliers,
                    "skipped_thin_channels": thin,
                    "skipped_invalid": skipped_invalid,
                },
                indent=1,
            )
        )
        return 0
    print(f"\n  {len(rows)} videos across {channel_count} channels, outliers at {args.min}x or better\n")
    for row in outliers[:MAX_TEXT_ROWS]:
        print(
            f"    {float(row['multiple']):5.2f}x  {int(row['views']):>9,}  vs {int(row['median']):>9,} median"
            f"   {str(row['channel'])[:22]:<22} {str(row['title'])[:52]}"
        )
        print(f"            {row['formula']}")
    if not outliers:
        print("    nothing cleared the threshold - collect more per channel or lower --min")
    if thin:
        print(f"\n  skipped {len(thin)} channel(s) with under 4 videos collected - a median off one or")
        print(
            "  two videos is not a median: "
            + ", ".join(f"{channel} ({count})" for channel, count in thin[:MAX_THIN_CHANNELS_SHOWN])
        )
    if skipped_invalid:
        print(f"  skipped {skipped_invalid} video(s) with missing or non-numeric view counts")
    counts: dict[str, int] = {}
    for row in outliers:
        formula = str(row["formula"])
        counts[formula] = counts.get(formula, 0) + 1
    if counts:
        print("\n  formulas among the outliers")
        for formula, count in sorted(counts.items(), key=lambda item: -item[1]):
            print(f"    {count:2d}x  {formula}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
