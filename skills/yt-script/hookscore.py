#!/usr/bin/env python3
"""hookscore.py - score a YouTube hook before you waste a take on it.

Five properties, 0-100 each, and a verdict that is 60% the mean and 40% the weakest one. The
weakest-link weighting is deliberate: a hook with four strong properties and one dead one is a
hook that leaks at the dead one, and averaging hides that.

    python3 hookscore.py hooks.txt            # one hook per line, ranked
    python3 hookscore.py --hook "one line"    # score a single hook
    python3 hookscore.py --json hooks.txt     # machine-readable

WHAT THIS CAN AND CANNOT TELL YOU. Measured against 74 real short-form hooks (first 15 seconds
of auto-captions, top-8 and bottom-8 by views across five channels): it separates deliberately
bad hooks from real ones well, and it separates a creator's own hits from their own misses
barely at all. Treat a low score as a reason to look again, never a high score as a promise.

The scoring constants below are that calibration. Do not tune them without re-measuring.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- Calibration constants (measured, not tuned) -------------------------------------------
VERDICT_MEAN_WEIGHT = 0.6
VERDICT_WEAKEST_WEIGHT = 0.4
STRONG_AT = 72
WORKABLE_AT = 55
BREVITY_IDEAL_MIN_WORDS = 9
BREVITY_IDEAL_MAX_WORDS = 24

FILLER = {
    "basically", "actually", "literally", "just", "really", "very", "so", "kind", "sort",
    "like", "guys", "hey", "welcome", "today", "video", "subscribe", "channel",
}
VAGUE = {
    "amazing", "incredible", "insane", "crazy", "huge", "massive", "game", "changer",
    "secret", "powerful", "ultimate", "best", "revolutionary", "mind", "blowing",
    "unbelievable",
}
CONCRETE = re.compile(
    r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b",
    re.IGNORECASE,
)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b", re.IGNORECASE)
STAKE = re.compile(
    r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b",
    re.IGNORECASE,
)
CURIOSITY = re.compile(
    r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b",
    re.IGNORECASE,
)
CLOSED = re.compile(r"\b(because|so that|which means)\b", re.IGNORECASE)

FIX = {
    "SPECIFICITY": "swap one adjective for a number, a name or a date",
    "ADDRESS": "say 'you' in the first six words",
    "STAKES": "name what it costs them to keep doing it the current way",
    "CURIOSITY": "cut the half of the sentence that answers itself",
    "BREVITY": "9 to 24 words. Read it out loud and stop where you run out of breath",
}


def load_formulas() -> list[tuple[str, tuple[re.Pattern[str], ...]]]:
    """Load the 21 hook formulas, compiling every pattern once up front."""
    path = Path(__file__).resolve().parent / "hooks.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        hooks = data["hooks"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"{path}: invalid hooks file: {exc}") from exc
    formulas: list[tuple[str, tuple[re.Pattern[str], ...]]] = []
    for item in hooks:
        try:
            patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in item["match"])
        except re.error as exc:
            raise ValueError(f"{path}: invalid pattern in formula {item.get('name')!r}: {exc}") from exc
        formulas.append((str(item["name"]), patterns))
    return formulas


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9'%$.]+", text.lower())


def specificity(text: str) -> int:
    found = words(text)
    if not found:
        return 0
    numbers = len(CONCRETE.findall(text))
    vague = sum(1 for word in found if word in VAGUE)
    filler = sum(1 for word in found if word in FILLER)
    score = 34 + numbers * 22 - vague * 16 - filler * 5
    # Proper nouns that are not sentence-initial read as named things.
    score += min(18, 6 * sum(1 for word in text.split()[1:] if word[:1].isupper()))
    return max(0, min(100, score))


def address(text: str) -> int:
    count = len(YOU.findall(text))
    first = 30 if YOU.search(" ".join(text.split()[:6])) else 0
    return max(0, min(100, 26 + count * 20 + first))


def stakes(text: str) -> int:
    count = len(STAKE.findall(text))
    return max(0, min(100, 22 + count * 26 + (14 if CONCRETE.search(text) else 0)))


def curiosity(text: str) -> int:
    count = len(CURIOSITY.findall(text))
    question = 18 if text.strip().endswith("?") else 0
    # A hook that resolves itself has no gap left.
    closed = -18 if CLOSED.search(text) else 0
    return max(0, min(100, 24 + count * 17 + question + closed))


def brevity(text: str) -> int:
    count = len(words(text))
    if count == 0:
        return 0
    # 9-24 words is the band a spoken hook lands in at ~150wpm inside 10 seconds.
    if BREVITY_IDEAL_MIN_WORDS <= count <= BREVITY_IDEAL_MAX_WORDS:
        return 100
    if count < BREVITY_IDEAL_MIN_WORDS:
        return max(30, 100 - (BREVITY_IDEAL_MIN_WORDS - count) * 11)
    return max(10, 100 - (count - BREVITY_IDEAL_MAX_WORDS) * 7)


PROPS = [
    ("SPECIFICITY", specificity),
    ("ADDRESS", address),
    ("STAKES", stakes),
    ("CURIOSITY", curiosity),
    ("BREVITY", brevity),
]


def classify(text: str, formulas: list[tuple[str, tuple[re.Pattern[str], ...]]]) -> tuple[str, int]:
    """Name the best-matching formula. Ties keep the first formula in hooks.json order."""
    best: str | None = None
    hits = 0
    for name, patterns in formulas:
        count = sum(1 for pattern in patterns if pattern.search(text))
        if count > hits:
            best, hits = name, count
    return (best if best is not None else "Unclassified"), hits


def score(text: str, formulas: list[tuple[str, tuple[re.Pattern[str], ...]]]) -> tuple[dict[str, int], int, str, int]:
    parts = {name: fn(text) for name, fn in PROPS}
    values = list(parts.values())
    verdict = round(VERDICT_MEAN_WEIGHT * (sum(values) / len(values)) + VERDICT_WEAKEST_WEIGHT * min(values))
    name, hits = classify(text, formulas)
    return parts, verdict, name, hits


def band(verdict: int) -> str:
    return "STRONG" if verdict >= STRONG_AT else "WORKABLE" if verdict >= WORKABLE_AT else "WEAK"


def report(text: str, parts: dict[str, int], verdict: int, name: str, hits: int) -> None:
    print(f"\n  {text.strip()}")
    print(f"  {'-' * min(72, max(20, len(text.strip())))}")
    for key, value in parts.items():
        print(f"    {key:<12} {value:3d}  {'#' * (value // 5)}")
    print(f"    {'VERDICT':<12} {verdict:3d}  {band(verdict)}")
    print(
        f"    formula      {name}"
        + (
            f"  ({hits} pattern{'s' if hits != 1 else ''} matched)"
            if hits
            else "  (no formula matched - that is usually a summary, not a hook)"
        )
    )
    weakest = min(parts, key=parts.get)
    print(f"    weakest      {weakest} - {FIX[weakest]}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score YouTube hooks on five properties. A low score means look again; a high score is not a promise.",
        epilog="Give one hook with --hook, or a file with one hook per line.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--hook", help="score this single hook line")
    group.add_argument("hooks_file", nargs="?", help="file with one hook per line")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        formulas = load_formulas()
    except (OSError, ValueError) as exc:
        print(f"hookscore: {exc}", file=sys.stderr)
        return 1
    if args.hook is not None:
        lines = [args.hook]
    else:
        try:
            lines = [
                line
                for line in Path(args.hooks_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError as exc:
            print(f"hookscore: {exc}", file=sys.stderr)
            return 1
    if args.hook is not None and not args.hook.strip():
        print("hookscore: --hook must not be empty", file=sys.stderr)
        return 2
    scored = []
    for text in lines:
        parts, verdict, name, hits = score(text, formulas)
        scored.append(
            {
                "hook": text.strip(),
                "properties": parts,
                "verdict": verdict,
                "band": band(verdict),
                "formula": name,
                "matched": hits,
            }
        )
    scored.sort(key=lambda row: -row["verdict"])
    if args.json:
        print(json.dumps(scored, indent=1))
        return 0
    for row in scored:
        report(row["hook"], row["properties"], row["verdict"], row["formula"], row["matched"])
    if len(scored) > 1:
        print(f"\n  winner: {scored[0]['hook'].strip()}  ({scored[0]['verdict']}, {scored[0]['band']})\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
