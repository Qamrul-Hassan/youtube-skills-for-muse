#!/usr/bin/env python3
"""Tests for the six tools. Standard library only; run with:

    python3 -m unittest discover -s tests -v

from the repository root.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
SKILLS = ROOT / "skills"

sys.path.insert(0, str(SKILLS / "yt-edit"))
sys.path.insert(0, str(SKILLS / "yt-chapters"))

import deadair  # noqa: E402
from chapters import build_chapters  # noqa: E402

sys.path.insert(0, str(SKILLS / "yt-retention"))
from retention import analyze, load_csv  # noqa: E402

sys.path.insert(0, str(SKILLS / "yt-viral"))
from swipe import classify, coerce_views, load_formulas, rank  # noqa: E402

sys.path.insert(0, str(SKILLS / "yt-script"))
from hookscore import brevity, score  # noqa: E402

sys.path.insert(0, str(SKILLS / "yt-package"))
from title import check  # noqa: E402


def run_tool(tool: Path, *args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(tool), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class TestDeadair(unittest.TestCase):
    def test_load_srt_sorted(self) -> None:
        cues = deadair.load(FIXTURES / "transcript.srt")
        self.assertEqual(len(cues), 8)
        self.assertEqual(cues[0][2], "July seventeenth nineteen eighty one")
        starts = [cue[0] for cue in cues]
        self.assertEqual(starts, sorted(starts))

    def test_load_json(self) -> None:
        cues = deadair.load(FIXTURES / "whisper.json")
        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[1][2], "um")

    def test_parse_ts(self) -> None:
        self.assertAlmostEqual(deadair.parse_ts("00:01:02,500"), 62.5)
        self.assertAlmostEqual(deadair.parse_ts("01:02.5"), 62.5)
        self.assertAlmostEqual(deadair.parse_ts("90"), 90.0)
        with self.assertRaises(ValueError):
            deadair.parse_ts("not-a-time")

    def test_find_cuts_kinds(self) -> None:
        cues = deadair.load(FIXTURES / "transcript.srt")
        cuts, duration = deadair.find_cuts(cues, 0.45)
        self.assertEqual(duration, 48.0)
        kinds = {cut["kind"] for cut in cuts}
        self.assertEqual(kinds, {"FILLER", "DEAD", "REPEAT"})

    def test_norm_keeps_digits(self) -> None:
        self.assertNotEqual(deadair.norm("part 2 of the plan"), deadair.norm("part 3 of the plan"))

    def test_cli_errors(self) -> None:
        missing = run_tool(SKILLS / "yt-edit" / "deadair.py", "/nonexistent/transcript.srt")
        self.assertEqual(missing.returncode, 1)
        negative = run_tool(
            SKILLS / "yt-edit" / "deadair.py", str(FIXTURES / "transcript.srt"), "--floor", "-1"
        )
        self.assertEqual(negative.returncode, 2)

    def test_cli_json_shape(self) -> None:
        result = run_tool(
            SKILLS / "yt-edit" / "deadair.py", str(FIXTURES / "transcript.srt"), "--json"
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["duration"], 48.0)
        self.assertIn("cuts", payload)


class TestChapters(unittest.TestCase):
    def test_dense_transcript_valid(self) -> None:
        cues = deadair.load(FIXTURES / "dense.srt")
        chapters, valid = build_chapters(cues, 7)
        self.assertTrue(valid)
        self.assertGreaterEqual(len(chapters), 3)
        self.assertEqual(chapters[0]["start"], 0)
        self.assertTrue(all(float(chapter["seconds"]) >= 10 for chapter in chapters))

    def test_deterministic_titles_across_hash_seeds(self) -> None:
        tool = SKILLS / "yt-chapters" / "chapters.py"
        outputs = []
        for seed in ("1", "2"):
            result = run_tool(
                tool, str(FIXTURES / "dense.srt"), "--json", env_extra={"PYTHONHASHSEED": seed}
            )
            self.assertEqual(result.returncode, 0)
            outputs.append(result.stdout)
        self.assertEqual(outputs[0], outputs[1])

    def test_target_validation(self) -> None:
        result = run_tool(
            SKILLS / "yt-chapters" / "chapters.py",
            str(FIXTURES / "dense.srt"),
            "--target",
            "0",
        )
        self.assertEqual(result.returncode, 2)


class TestRetention(unittest.TestCase):
    def test_analyze_known_curve(self) -> None:
        rows = load_csv(FIXTURES / "retention.csv")
        # Duration 300s: the 30-second hook window is the first 10% of the axis,
        # so the 100 -> 70 drop at x=10 is inside it.
        report = analyze(rows, 300, None)
        self.assertEqual(report["points"], 11)
        self.assertEqual(report["hook_leak"], 30.0)
        self.assertEqual(report["cliffs"][0]["lost"], 30.0)
        self.assertEqual(report["slide_per_unit"], 0.2)

    def test_analyze_with_transcript_names_the_moment(self) -> None:
        rows = load_csv(FIXTURES / "retention.csv")
        report = analyze(rows, 660, str(FIXTURES / "transcript.srt"))
        self.assertIn("July", report["said"].get("0.0", ""))

    def test_cli_errors(self) -> None:
        missing = run_tool(SKILLS / "yt-retention" / "retention.py", "/nonexistent/retention.csv")
        self.assertEqual(missing.returncode, 1)
        with tempfile.TemporaryDirectory() as tmp:
            short = Path(tmp) / "short.csv"
            short.write_text("0,100\n10,90\n", encoding="utf-8")
            result = run_tool(SKILLS / "yt-retention" / "retention.py", str(short))
            self.assertEqual(result.returncode, 1)
        bad_duration = run_tool(
            SKILLS / "yt-retention" / "retention.py",
            str(FIXTURES / "retention.csv"),
            "--duration",
            "0",
        )
        self.assertEqual(bad_duration.returncode, 2)


class TestSwipe(unittest.TestCase):
    def test_rank_outlier(self) -> None:
        rows = json.loads((FIXTURES / "collected.json").read_text(encoding="utf-8"))
        formulas = load_formulas()
        outliers, thin, skipped = rank(rows, formulas, 2.0)
        self.assertEqual(len(outliers), 1)
        self.assertEqual(outliers[0]["multiple"], 3.0)
        self.assertEqual(outliers[0]["channel"], "Ch A")
        self.assertEqual(thin, [])
        self.assertEqual(skipped, 0)

    def test_thin_channel_skipped(self) -> None:
        rows = [
            {"channel": "Tiny", "title": "One", "views": 100, "url": ""},
            {"channel": "Tiny", "title": "Two", "views": 200, "url": ""},
        ]
        outliers, thin, _skipped = rank(rows, load_formulas(), 1.5)
        self.assertEqual(outliers, [])
        self.assertEqual(thin, [("Tiny", 2)])

    def test_invalid_views_skipped_and_counted(self) -> None:
        rows = [
            {"channel": "Ch", "title": "Good", "views": 100, "url": ""},
            {"channel": "Ch", "title": "Bad", "views": "not-a-number", "url": ""},
            {"channel": "Ch", "title": "Also good", "views": 100, "url": ""},
            {"channel": "Ch", "title": "Third", "views": 100, "url": ""},
        ]
        _outliers, _thin, skipped = rank(rows, load_formulas(), 1.5)
        self.assertEqual(skipped, 1)

    def test_coerce_views(self) -> None:
        self.assertEqual(coerce_views(412000), 412000.0)
        self.assertEqual(coerce_views("1,200"), 1200.0)
        self.assertIsNone(coerce_views("1.2M"))
        self.assertIsNone(coerce_views(None))
        self.assertIsNone(coerce_views(True))

    def test_classify_unclassified(self) -> None:
        self.assertEqual(classify("zzzz qq wwww", load_formulas()), "Unclassified")

    def test_cli_bad_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            result = run_tool(SKILLS / "yt-viral" / "swipe.py", str(bad))
            self.assertEqual(result.returncode, 1)


class TestHookscore(unittest.TestCase):
    def test_verdict_formula(self) -> None:
        formulas = [
            ("F", (re.compile("zzz", re.IGNORECASE),)),
        ]
        parts, verdict, _name, _hits = score("Why did this steel bridge fall down today?", formulas)
        self.assertTrue(all(0 <= value <= 100 for value in parts.values()))
        expected = round(0.6 * (sum(parts.values()) / len(parts)) + 0.4 * min(parts.values()))
        self.assertEqual(verdict, expected)

    def test_brevity_band(self) -> None:
        self.assertEqual(brevity(""), 0)
        self.assertEqual(brevity("one two three four five six seven eight nine ten eleven twelve"), 100)

    def test_cli_empty_hook_and_missing_file(self) -> None:
        empty = run_tool(SKILLS / "yt-script" / "hookscore.py", "--hook", "   ")
        self.assertEqual(empty.returncode, 2)
        missing = run_tool(SKILLS / "yt-script" / "hookscore.py", "/nonexistent/hooks.txt")
        self.assertEqual(missing.returncode, 1)

    def test_cli_json_includes_matched(self) -> None:
        result = run_tool(
            SKILLS / "yt-script" / "hookscore.py",
            "--hook",
            "Why did 114 people die when two walkways fell in 1981?",
            "--json",
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("matched", payload[0])


class TestTitle(unittest.TestCase):
    def test_empty_title_is_an_issue(self) -> None:
        report = check("   ")
        self.assertEqual(report["score"], 0)
        self.assertEqual(report["issues"][0][0], "empty")

    def test_duplicate_detection(self) -> None:
        report = check("The Bridge Fell Down", "BRIDGE FELL")
        self.assertTrue(any(key == "duplicate" for key, _message in report["issues"]))

    def test_no_duplicate_for_different_words(self) -> None:
        report = check("How Engineers Sunk a $350M Skyscraper", "BUILT ON MUD")
        self.assertFalse(any(key == "duplicate" for key, _message in report["issues"]))

    def test_cli_mutually_exclusive(self) -> None:
        result = run_tool(
            SKILLS / "yt-package" / "title.py",
            "--title",
            "Some title",
            str(FIXTURES / "titles.txt"),
        )
        self.assertEqual(result.returncode, 2)


class TestHooksJson(unittest.TestCase):
    def test_all_patterns_compile(self) -> None:
        data = json.loads((SKILLS / "yt-script" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["hooks"]), 21)
        for hook in data["hooks"]:
            self.assertTrue(hook["name"])
            self.assertTrue(hook["match"])
            for pattern in hook["match"]:
                re.compile(pattern)


if __name__ == "__main__":
    unittest.main()
