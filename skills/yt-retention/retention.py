#!/usr/bin/env python3
"""retention.py - read a YouTube Studio audience-retention export and find the leaks.

    python3 retention.py retention.csv --duration 600
    python3 retention.py retention.csv --transcript transcript.srt   # names what was said at each drop
    python3 retention.py retention.csv --json

Get the file from Studio: Analytics -> a video -> Engagement -> the audience-retention chart ->
the download icon -> "Audience retention". Two columns, a position (percent or seconds) and a
percentage still watching.

It reports three things, because they are three different problems with three different fixes:
  HOOK LEAK    what you lost in the first 30 seconds
  CLIFFS       single steep drops - a specific moment people left at
  SLIDE        the steady bleed rate across the flat middle

With --transcript it prints what you were saying at each cliff, which is the only version of this
report you can act on without scrubbing the video yourself.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import TypedDict

# The transcript parser lives in yt-edit/deadair.py. It is imported lazily, only when
# --transcript is used, and resolved from this file's own directory first, then from the
# package's sibling yt-edit directory.
_HERE = Path(__file__).resolve().parent

MIN_POINTS = 8
HOOK_WINDOW_SECONDS = 30.0
HOOK_HEALTHY_BELOW = 25.0
HOOK_SEVERE_AT = 40.0
CLIFF_MIN_DROP = 0.8

Cliff = TypedDict("Cliff", {"from": float, "to": float, "lost": float, "at_seconds": float | None})


class Report(TypedDict):
    points: int
    start: float
    hook_leak: float
    end: float
    cliffs: list[Cliff]
    slide_per_unit: float
    said: dict[str, str]


def load_csv(path: str | Path) -> list[tuple[float, float]]:
    """Read a two-column retention export: (position, percent still watching) per row."""
    rows: list[tuple[float, float]] = []
    with Path(path).open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for record in csv.reader(handle):
            numbers: list[float] = []
            for cell in record:
                cleaned = cell.strip().replace("%", "").replace(",", "")
                try:
                    numbers.append(float(cleaned))
                except ValueError:
                    numbers.append(float("nan"))
            values = [number for number in numbers if number == number]  # drop NaNs
            if len(values) >= 2:
                rows.append((values[0], values[1]))
    return rows


def _load_transcript_cues(path: str) -> list[tuple[float, float, str]]:
    for candidate in (_HERE, _HERE.parent / "yt-edit"):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    from deadair import load as load_cues

    return load_cues(path)


def analyze(
    rows: list[tuple[float, float]],
    duration: float | None,
    transcript: str | None,
) -> Report:
    """Compute hook leak, cliffs and slide from parsed retention rows."""
    xs = [row[0] for row in rows]
    ys = [row[1] for row in rows]
    percent_axis = max(xs) <= 100.5

    def at_seconds(position: float) -> float | None:
        if not percent_axis or duration:
            base = (position / 100.0 * duration) if (percent_axis and duration) else position
            return base
        return None

    start = ys[0] or 100.0
    # HOOK: the first 30 seconds, or the first 10% when the axis is a percentage and we
    # have no duration.
    if percent_axis:
        cutoff = (HOOK_WINDOW_SECONDS / duration * 100) if duration else 10.0
    else:
        cutoff = HOOK_WINDOW_SECONDS
    hook_end = min((y for x, y in rows if x <= cutoff), default=start)
    hook_leak = start - hook_end

    drops: list[tuple[float, float, float, float]] = []
    for i in range(1, len(rows)):
        drop = ys[i - 1] - ys[i]
        span = xs[i] - xs[i - 1] or 1
        drops.append((drop / span, xs[i - 1], xs[i], drop))
    drops.sort(reverse=True)
    cliffs: list[Cliff] = []
    for _rate, start_pos, end_pos, drop in drops[:5]:
        if drop <= CLIFF_MIN_DROP:
            continue
        at = at_seconds(start_pos)
        cliffs.append(
            {
                "from": round(start_pos, 2),
                "to": round(end_pos, 2),
                "lost": round(drop, 2),
                "at_seconds": round(at, 1) if at is not None else None,
            }
        )

    # SLIDE: the mean per-step loss rate across the middle (past the hook window).
    middle_rates = [rate for rate, x0, _x1, _drop in drops if x0 > cutoff]
    slide = sum(middle_rates) / len(middle_rates) if middle_rates else 0.0

    said: dict[str, str] = {}
    if transcript is not None:
        cues = _load_transcript_cues(transcript)
        for cliff in cliffs:
            at = cliff["at_seconds"]
            if at is None:
                continue
            moment = float(at)
            near = [text for cue_start, cue_end, text in cues if cue_start <= moment + 4 and cue_end >= moment - 4]
            said[str(cliff["from"])] = " ".join(near)[:140]
    return {
        "points": len(rows),
        "start": start,
        "hook_leak": round(hook_leak, 2),
        "end": ys[-1],
        "cliffs": cliffs,
        "slide_per_unit": round(slide, 3),
        "said": said,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find where viewers leave from a Studio audience-retention export.",
        epilog="Get the CSV from Studio: a video -> Analytics -> Engagement -> retention chart -> download.",
    )
    parser.add_argument("csv_file", help="retention export CSV (position, percent still watching)")
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="video length in seconds; needed to resolve percent-axis positions to seconds",
    )
    parser.add_argument(
        "--transcript",
        default=None,
        help="transcript (.srt/.vtt/.json) to name what was said at each cliff",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.duration is not None and args.duration <= 0:
        print("retention: --duration must be greater than 0", file=sys.stderr)
        return 2
    try:
        rows = load_csv(args.csv_file)
    except OSError as exc:
        print(f"retention: {exc}", file=sys.stderr)
        return 1
    if len(rows) < MIN_POINTS:
        print(
            f"retention: could not read at least {MIN_POINTS} data points from that CSV",
            file=sys.stderr,
        )
        return 1
    try:
        report = analyze(rows, args.duration, args.transcript)
    except (OSError, ValueError) as exc:
        print(f"retention: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=1))
        return 0
    ys = [row[1] for row in rows]
    hook_leak = report["hook_leak"]
    cliffs = report["cliffs"]
    said = report["said"]
    print(f"\n  {args.csv_file}   {len(rows)} points   {ys[0]:.1f}% -> {ys[-1]:.1f}%\n")
    verdict = (
        "healthy"
        if hook_leak < HOOK_HEALTHY_BELOW
        else "leaking"
        if hook_leak < HOOK_SEVERE_AT
        else "severe"
    )
    print(f"  HOOK LEAK   {hook_leak:.1f}% lost in the opening   [{verdict}]")
    print("              under 25 is healthy for this length. Fix the first line before anything else.\n")
    print("  CLIFFS      the moments people actually left")
    for cliff in cliffs:
        at = cliff["at_seconds"]
        where = f"{at:.0f}s" if at is not None else f"{cliff['from']}"
        quoted = f"   \"{said.get(str(cliff['from']), '')}\"" if said else ""
        print(f"    -{cliff['lost']:5.1f}%  at {where:>8}{quoted}")
    if not cliffs:
        print("    none steeper than 0.8% - the loss is all slide, not moments")
    print(f"\n  SLIDE       {report['slide_per_unit']:.3f}% per unit across the middle")
    print("              a flat slide is pacing, not content. Cut the middle, do not rewrite it.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
