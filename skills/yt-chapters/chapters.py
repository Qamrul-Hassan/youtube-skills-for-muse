#!/usr/bin/env python3
"""chapters.py - YouTube chapters from a timestamped transcript.

    python3 chapters.py transcript.srt            # or .vtt / whisper .json
    python3 chapters.py transcript.srt --target 8 --json

Prints a description block you can paste straight under a video. YouTube's own rules, enforced
here rather than assumed: the list must start at 00:00, needs at least three entries, and each
chapter must be at least 10 seconds long. A block that breaks any of those silently does not
become chapters, which is why this checks instead of trusting.

Boundaries come from the gaps - the pauses you actually took between sections - scored by how
long the pause was and how much the vocabulary changes across it. It is a first draft you
retitle, not a summariser.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The transcript parser lives in yt-edit/deadair.py: one implementation, shared by every tool
# that reads transcripts. Look next to this file first (a copied skill folder), then in the
# package's sibling yt-edit directory.
_HERE = Path(__file__).resolve().parent
for _candidate in (_HERE, _HERE.parent / "yt-edit"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
from deadair import Cue, load  # noqa: E402

STOP = set(
    "the a an of for to in on and or is are was were be been with this that it as at by from "
    "you your i my we our they them he she but so if then than there here what which who how "
    "when where why not no yes do does did just really very like about into over out up down "
    "can could will would should have has had get got make made go going went one two".split()
)

MIN_CHAPTER_SECONDS = 10.0
DEFAULT_TARGET = 7
CONTEXT_CUES = 12
GAP_WEIGHT = 1.6
SHIFT_WEIGHT = 3.2


def keywords(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z']{4,}", text.lower()) if word not in STOP}


def mmss(seconds: float) -> str:
    total = int(seconds)
    hours, minutes, secs = total // 3600, (total % 3600) // 60, total % 60
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def build_chapters(cues: list[Cue], target: int) -> tuple[list[dict[str, object]], bool]:
    """Pick chapter boundaries from pause gaps and vocabulary shifts.

    Returns (chapters, valid): ``valid`` is True only when YouTube's rules hold - at least
    three chapters, the first starting at 0, every chapter at least 10 seconds.
    """
    duration = max((end for _start, end, _text in cues), default=0.0)
    candidates: list[tuple[float, float, int]] = []
    for i in range(1, len(cues)):
        gap = cues[i][0] - cues[i - 1][1]
        before = " ".join(cue[2] for cue in cues[max(0, i - CONTEXT_CUES) : i])
        after = " ".join(cue[2] for cue in cues[i : i + CONTEXT_CUES])
        words_before, words_after = keywords(before), keywords(after)
        union = words_before | words_after
        shift = 1 - (len(words_before & words_after) / len(union)) if union else 0
        candidates.append((gap * GAP_WEIGHT + shift * SHIFT_WEIGHT, cues[i][0], i))
    candidates.sort(reverse=True)
    picked = [0.0]
    for _score, start, _index in candidates:
        if len(picked) >= target:
            break
        if all(abs(start - other) >= MIN_CHAPTER_SECONDS for other in picked) and (
            duration - start >= MIN_CHAPTER_SECONDS
        ):
            picked.append(start)
    picked.sort()
    chapters: list[dict[str, object]] = []
    for n, start in enumerate(picked):
        end = picked[n + 1] if n + 1 < len(picked) else duration
        text = " ".join(cue[2] for cue in cues if cue[0] >= start and cue[1] <= end)
        # Deterministic order: most frequent first, ties broken alphabetically. (Sorting
        # a set by count alone made tied titles change from run to run.)
        lowered = text.lower()
        ranked = sorted(keywords(text), key=lambda word: (-lowered.count(word), word))
        title = " ".join(word.capitalize() for word in ranked[:3]) or "Section"
        chapters.append(
            {
                "start": round(start, 2),
                "label": mmss(start),
                "draft_title": title,
                "seconds": round(end - start, 2),
            }
        )
    valid = (
        len(chapters) >= 3
        and float(chapters[0]["start"]) == 0
        and all(float(chapter["seconds"]) >= MIN_CHAPTER_SECONDS for chapter in chapters)
    )
    return chapters, valid


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draft YouTube chapters from a transcript, validated against YouTube's rules.",
        epilog="Input: .srt, .vtt, or Whisper .json. Retitle every line before pasting.",
    )
    parser.add_argument("transcript", help="transcript file (.srt, .vtt or Whisper .json)")
    parser.add_argument(
        "--target",
        type=int,
        default=DEFAULT_TARGET,
        help=f"maximum chapters to draft (default: {DEFAULT_TARGET})",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.target < 1:
        print("chapters: --target must be at least 1", file=sys.stderr)
        return 2
    try:
        cues = load(args.transcript)
    except (OSError, ValueError) as exc:
        print(f"chapters: {exc}", file=sys.stderr)
        return 1
    if len(cues) < 6:
        print("chapters: too few cues to chapter", file=sys.stderr)
        return 1
    chapters, valid = build_chapters(cues, args.target)
    if args.json:
        print(json.dumps({"valid": valid, "chapters": chapters}, indent=1))
        return 0
    print()
    for chapter in chapters:
        print(f"  {chapter['label']} {chapter['draft_title']}")
    print(
        f"\n  {len(chapters)} chapters"
        f"{'' if valid else '  -- INVALID: YouTube needs 3+, a 00:00 first entry and 10s minimum each'}"
    )
    print("  Retitle every line before pasting. These are the topic words, not your words.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
