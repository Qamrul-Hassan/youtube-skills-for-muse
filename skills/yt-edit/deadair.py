#!/usr/bin/env python3
"""deadair.py - an edit decision list from a timestamped transcript.

    python3 deadair.py transcript.srt            # or .vtt, or whisper .json
    python3 deadair.py transcript.srt --floor 0.35 --json

Finds three things and prints the cuts as a list you can act on, newest problem first:
  DEAD    gaps between spoken cues longer than the floor
  FILLER  cues that are only filler ("um", "so yeah", "basically")
  REPEAT  a sentence restarted - the second take of the same opening

WHAT IT DOES NOT DO. It does not cut the file. It prints an EDL, the total it would remove, and
the runtime you would land on, and you apply it in whatever editor you use. Nothing here touches
media.

Robustness notes: cues are returned sorted by start time (transcripts are time-ordered by
definition, so this only repairs out-of-order input); a cue whose timestamp cannot be parsed, or
a JSON segment without numeric start/end, is skipped instead of crashing the whole run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A cue is (start_seconds, end_seconds, text). This parser is the single implementation shared
# by chapters.py and retention.py: they import load() from here.
Cue = tuple[float, float, str]

FILLER_ONLY = re.compile(
    r"^[\s,.-]*((um+|uh+|er+|ah+|so|okay|ok|right|yeah|like|anyway|basically|"
    r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$",
    re.IGNORECASE,
)
_TIMESTAMP_RE = re.compile(r"\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)")

DEFAULT_FLOOR = 0.45


def parse_ts(value: str) -> float:
    """Parse ``H:MM:SS``, ``MM:SS`` or bare seconds (``.`` or ``,`` decimals) to seconds."""
    text = value.strip().replace(",", ".")
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes = int(parts[0]), int(parts[1])
            return hours * 3600 + minutes * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    raise ValueError(f"unparseable timestamp: {value!r}")


def _load_json_cues(data: object, source: str) -> list[Cue]:
    """Extract cues from a Whisper-style JSON payload (``{"segments": [...]}`` or a bare list)."""
    if isinstance(data, dict):
        segments = data.get("segments", [])
    else:
        segments = data
    if not isinstance(segments, list):
        raise ValueError(f"{source}: expected a JSON list of segments")
    cues: list[Cue] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError):
            continue
        text = str(segment.get("text") or "").strip()
        if text:
            cues.append((start, end, text))
    return cues


def _load_text_cues(text: str) -> list[Cue]:
    """Extract cues from SRT/VTT text: timestamp lines start a cue, following lines are its text."""
    cues: list[Cue] = []
    start = end = 0.0
    words: list[str] = []
    open_cue = False

    def flush() -> None:
        nonlocal open_cue
        if open_cue and words:
            cues.append((start, end, " ".join(words)))
        open_cue = False

    for line in text.splitlines():
        match = _TIMESTAMP_RE.match(line)
        if match:
            flush()
            try:
                start = parse_ts(match.group(1))
                end = parse_ts(match.group(2))
            except ValueError:
                continue
            words = []
            open_cue = True
        elif open_cue and line.strip() and not line.strip().isdigit():
            words.append(line.strip())
    flush()
    return cues


def load(path: str | Path) -> list[Cue]:
    """Read a transcript file (.srt, .vtt or Whisper .json) into time-sorted cues.

    Raises OSError for unreadable files and ValueError for malformed JSON.
    """
    source = Path(path)
    raw = source.read_text(encoding="utf-8", errors="replace")
    if source.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source}: invalid JSON: {exc}") from exc
        cues = _load_json_cues(data, str(source))
    else:
        cues = _load_text_cues(raw)
    cues.sort(key=lambda cue: cue[0])
    return cues


def norm(text: str) -> list[str]:
    """Lowercase words, keeping letters and digits: ``part 2`` must not equal ``part 3``."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).split()


def find_cuts(cues: list[Cue], floor: float) -> tuple[list[dict[str, object]], float]:
    """Find DEAD / FILLER / REPEAT cuts. Returns (cuts, duration_seconds)."""
    duration = max((end for _start, end, _text in cues), default=0.0)
    cuts: list[dict[str, object]] = []
    for i, (start, end, text) in enumerate(cues):
        if FILLER_ONLY.match(text):
            cuts.append({"kind": "FILLER", "start": start, "end": end, "why": text.strip()[:48]})
        if i:
            gap = start - cues[i - 1][1]
            if gap > floor:
                keep = floor / 2
                cuts.append(
                    {
                        "kind": "DEAD",
                        "start": round(cues[i - 1][1] + keep, 3),
                        "end": round(start - keep, 3),
                        "why": f"{gap:.2f}s gap",
                    }
                )
        # A restart is compared against the last cue that was actually SPEECH. Comparing
        # against the literal previous cue misses every retake with an "um" between the two
        # attempts, which is most of them.
        if text.strip() and not FILLER_ONLY.match(text):
            j = i - 1
            while j >= 0 and (FILLER_ONLY.match(cues[j][2]) or not cues[j][2].strip()):
                j -= 1
            if j >= 0:
                previous = norm(cues[j][2])[:5]
                current = norm(text)[:5]
                if len(previous) >= 3 and previous == current:
                    cuts.append(
                        {
                            "kind": "REPEAT",
                            "start": cues[j][0],
                            "end": cues[j][1],
                            "why": f'restart of "{" ".join(previous)}"',
                        }
                    )
    cuts = [cut for cut in cuts if float(cut["end"]) > float(cut["start"])]
    cuts.sort(key=lambda cut: float(cut["start"]))
    return cuts, duration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print an edit decision list (dead air, filler, retakes) from a transcript.",
        epilog="Input: .srt, .vtt, or Whisper .json. Output is a cut list only - no media is touched.",
    )
    parser.add_argument("transcript", help="transcript file (.srt, .vtt or Whisper .json)")
    parser.add_argument(
        "--floor",
        type=float,
        default=DEFAULT_FLOOR,
        help=f"gaps longer than this many seconds count as dead air (default: {DEFAULT_FLOOR})",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.floor < 0:
        print("deadair: --floor must not be negative", file=sys.stderr)
        return 2
    try:
        cues = load(args.transcript)
    except (OSError, ValueError) as exc:
        print(f"deadair: {exc}", file=sys.stderr)
        return 1
    if not cues:
        print(
            "deadair: no cues found - is this an .srt, .vtt or Whisper .json file?",
            file=sys.stderr,
        )
        return 1
    cuts, duration = find_cuts(cues, args.floor)
    removed = sum(float(cut["end"]) - float(cut["start"]) for cut in cuts)
    if args.json:
        print(
            json.dumps(
                {
                    "source": args.transcript,
                    "duration": duration,
                    "cuts": cuts,
                    "removed": round(removed, 3),
                    "out": round(duration - removed, 3),
                },
                indent=1,
            )
        )
        return 0
    print(f"\n  {args.transcript}   {duration:.2f}s in, {len(cues)} cues, dead-air floor {args.floor}s\n")
    for cut in cuts:
        start, end = float(cut["start"]), float(cut["end"])
        print(
            f"    {cut['kind']:<7} {start:8.2f} -> {end:8.2f}   {end - start:5.2f}s   {cut['why']}"
        )
    percent = (removed / duration * 100) if duration else 0.0
    print(
        f"\n  {len(cuts)} cuts, {removed:.2f}s removed, {duration - removed:.2f}s out "
        f"({percent:.1f}% shorter)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
