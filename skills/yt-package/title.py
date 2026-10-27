#!/usr/bin/env python3
"""title.py - lint a YouTube title and thumbnail pairing before you publish it.

    python3 title.py --title "..." --thumb "AI RAN IT"
    python3 title.py titles.txt            # one per line, ranked
    python3 title.py --title "..." --json

The pairing is the unit, not the title. A title that repeats the thumbnail text wastes half
the click surface, and that is the single most common mistake this checks for.

Length: YouTube truncates around 60 characters on desktop search and around 40 on a mobile home
feed. Both limits are reported because they are different failures - a desktop truncation loses
the tail, a mobile one can lose the subject.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TypedDict

DESKTOP, MOBILE, HARD = 60, 40, 100
ISSUE_PENALTY = 14
GOOD_BONUS = 4
MAX_CAPS_WORDS = 2
MAX_THUMB_WORDS = 4
VAGUE = {
    "amazing", "incredible", "insane", "crazy", "huge", "massive", "ultimate", "best",
    "powerful", "secret", "revolutionary", "mindblowing", "epic", "perfect", "complete",
    "everything",
}
STOP = {
    "the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "is", "are", "with",
    "your", "you", "my", "i", "this", "that", "it", "how", "what", "why",
}


class TitleReport(TypedDict):
    title: str
    chars: int
    score: int
    issues: list[tuple[str, str]]
    good: list[str]


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def check(title: str, thumb: str | None = None) -> TitleReport:
    text = title.strip()
    length = len(text)
    issues: list[tuple[str, str]] = []
    good: list[str] = []
    if not text:
        issues.append(("empty", "the title is empty - YouTube needs a title"))
        return {"title": text, "chars": 0, "score": 0, "issues": issues, "good": good}
    if length > HARD:
        issues.append(("length", f"{length} characters - YouTube's hard limit is {HARD}"))
    elif length > DESKTOP:
        issues.append(("length", f"{length} characters - desktop search cuts near {DESKTOP}"))
    else:
        good.append(f"{length} characters, inside the {DESKTOP}-character desktop cut")
    if length > MOBILE:
        head = text[:MOBILE].rsplit(" ", 1)[0]
        issues.append(
            ("mobile", f'a mobile feed shows about "{head}..." - check the subject survives')
        )
    caps = [word for word in text.split() if len(word) > 2 and word.isupper()]
    if len(caps) > MAX_CAPS_WORDS:
        issues.append(
            ("shouting", f"{len(caps)} all-caps words - two is the ceiling before it reads as spam")
        )
    elif caps:
        good.append(f"{len(caps)} all-caps word for emphasis")
    vague = [word for word in words(text) if word in VAGUE]
    if vague:
        issues.append(("vague", f"{', '.join(sorted(set(vague)))} - swap for a number, a name or a date"))
    numbers = re.findall(r"\d[\d,.]*%?", text)
    if numbers:
        good.append(f"carries a concrete figure ({', '.join(numbers[:3])})")
    else:
        issues.append(("no-number", "no number, date or name - the most reliable single fix"))
    if text.endswith("?"):
        good.append("open question in the title")
    front = [word for word in words(text)[:3] if word not in STOP]
    if not front:
        issues.append(("front-load", "the first three words are all filler - move the subject forward"))
    if thumb:
        title_words = set(words(text)) - STOP
        thumb_words = set(words(thumb)) - STOP
        shared = title_words & thumb_words
        if shared:
            issues.append(
                (
                    "duplicate",
                    f"thumbnail repeats the title on {', '.join(sorted(shared))} - "
                    "the thumbnail should say what the title does not",
                )
            )
        else:
            good.append("thumbnail and title carry different words")
        if len(words(thumb)) > MAX_THUMB_WORDS:
            issues.append(
                (
                    "thumb-length",
                    f"{len(words(thumb))} words on the thumbnail - three is the ceiling at feed size",
                )
            )
    score = max(0, min(100, 100 - ISSUE_PENALTY * len(issues) + GOOD_BONUS * len(good)))
    return {"title": text, "chars": length, "score": score, "issues": issues, "good": good}


def show(result: TitleReport) -> None:
    print(f'\n  "{result["title"]}"')
    print(f"  {result['chars']} chars   score {result['score']}/100")
    for key, message in result["issues"]:
        print(f"    x  {key:<12} {message}")
    for message in result["good"]:
        print(f"    ok              {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lint a YouTube title and thumbnail pairing before publishing.",
        epilog="Give one title with --title, or a file with one title per line.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", help="lint this single title")
    group.add_argument("titles_file", nargs="?", help="file with one title per line")
    parser.add_argument("--thumb", default=None, help="thumbnail on-image text to check against the title")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.title is not None:
        rows = [check(args.title, args.thumb)]
    else:
        try:
            lines = [
                line
                for line in Path(args.titles_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError as exc:
            print(f"title: {exc}", file=sys.stderr)
            return 1
        rows = [check(line, args.thumb) for line in lines]
    rows.sort(key=lambda row: -row["score"])
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    for row in rows:
        show(row)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
