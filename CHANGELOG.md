# Changelog

All notable changes to this package versus its upstream source,
[Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill)
(pinned commit `a2feb2104981a375ffd4f87ee04f4f5344ac43c6`, 2026-09-16).

## [Unreleased] — hardened 2026-10-27

### Fixed — bugs found by auditing all six tools

- `chapters.py`: draft chapter titles were **nondeterministic** — tied keywords were
  ordered by set iteration, so titles changed from run to run (proven: same input,
  different `PYTHONHASHSEED`, different titles). Ties now break alphabetically;
  output is identical across runs.
- `title.py`: an empty title was reported as a valid length ("0 characters, inside the
  cut"). It now reports an `empty` issue with score 0.
- `deadair.py`: duration came from the last cue in file order, so an out-of-order
  transcript gave a wrong runtime. Cues are now sorted by start time and duration is
  the maximum end time. Malformed JSON segments and unparseable timestamps are
  skipped with the rest of the file processed, instead of crashing the run.
- `deadair.py`: restart detection stripped digits, so "part 2" and "part 3" compared
  equal. Digits are now kept.
- `swipe.py`: a missing or non-numeric view count crashed the run. Such rows are now
  skipped and counted (`skipped_invalid` in JSON output, noted in text output).
  A non-list JSON payload crashed with a traceback; it now fails with a clean error.
  Formula patterns are compiled once at startup, so an invalid pattern fails fast
  with the file named instead of mid-run.
- All six tools: a flag with no value after it (`--hook` with nothing after it,
  `--min` with nothing after it, ...) crashed with an `IndexError` traceback, and a
  missing input file printed a traceback or — in `hookscore.py` — exited 0, looking
  like success. All tools now use `argparse`: bad usage exits 2 with usage text,
  unreadable input exits 1 with a one-line error on stderr.
- `retention.py`: a missing `--transcript` file was silently ignored, producing a
  report without the "what was said" column the user asked for. It now errors
  cleanly. The slide computation was rewritten readably with identical math.

### Changed — pro-level hardening, same behaviour on valid input

- Every tool is now a typed `argparse` CLI: `--help` works everywhere, `main()`
  returns an exit code, errors go to stderr with the tool's name. Python 3.10+,
  standard library only, explicit UTF-8 file handling, `pathlib` throughout.
- Scoring and linting math is unchanged. Verified by running the upstream tools and
  the hardened tools on identical inputs and diffing stdout: identical for every
  tool in text mode, except the two documented changes below.
- `hookscore.py --json` now includes the `matched` field (it was computed and shown
  in text output but dropped from JSON).
- `swipe.py --json` now includes `skipped_invalid` (additive; text output is
  unchanged when the count is zero).
- The shared transcript parser is resolved robustly: `chapters.py` and
  `retention.py` look for `deadair.py` next to themselves first, then in the
  sibling `../yt-edit/` directory, so a lone copied skill folder still works.
  `swipe.py` resolves `hooks.json` the same way (own folder, then `../yt-script/`).
- Tests added: `tests/` holds 28 `unittest` tests (standard library only) with
  fixtures, covering happy paths, CLI error paths, edge cases, and determinism.
  Run with `python3 -m unittest discover -s tests`.
- Docs added for the repo to explain itself: this file, a rewritten `README.md`
  (purpose, quickstart, structure, quality, limits), `pyproject.toml`, and
  `.gitignore`.

### Unchanged — deliberately

- All scoring, linting, ranking, and chapter-boundary math is identical to
  upstream. No heuristic was re-tuned.
- Zero third-party dependencies. No network access, no subprocesses, no
  environment or credential access. Tools read local files and print only.
- `hooks.json` (21 hook formulas), `templates/voice.md`, and `LICENSE` are
  byte-identical to upstream.
- Every tool still ends in output the user copies. Nothing publishes, nothing
  auto-runs a channel.
