# Provenance

## Upstream source

- Repository: https://github.com/Jakeschincariol/youtube-agent-skill
- Author: Jake Schincariol (https://opusjake.ai)
- Pinned commit: `a2feb2104981a375ffd4f87ee04f4f5344ac43c6` (the repository's only commit; created 2026-09-16)
- License: MIT (copied verbatim to `LICENSE` in this package root)
- Adapted: 2026-10-27, for Muse (the upstream pack targets Claude Code)
- Hardened: 2026-10-27 (bug fixes, typed `argparse` CLIs, tests — see `CHANGELOG.md`)

## What is byte-identical to upstream

- Data file: `skills/yt-script/hooks.json` (21 hook formulas)
- Template: `templates/voice.md`
- License: `LICENSE`

## What is adapted

- All six Python tools (`hookscore.py`, `title.py`, `deadair.py`, `chapters.py`,
  `retention.py`, `swipe.py`): hardened from the upstream versions. The scoring,
  linting, ranking, and chapter-boundary math is unchanged (verified by before/after
  output diffs on identical inputs); the hardening is bug fixes, typed `argparse`
  CLIs, robust file handling, deterministic output, and a test suite. The full
  list of fixes and deliberate output changes is in `CHANGELOG.md`.
- All eleven `skills/*/SKILL.md` files: rewritten for Muse. The upstream methods,
  tool commands, and the author's own honest limits are kept; Claude Code references
  (plugin install, `~/.claude/youtube/voice.md`) are replaced with Muse routing
  (read as `SKILL.md` playbooks, tools run with `python3`, voice profile kept at
  `templates/voice.md`); DIG's standing constraints are added where relevant
  (read-only Data API connector for channel/video data, no scraping, no login, no
  shared keys, no OAuth, nothing auto-publishes, retention only from a
  user-supplied Studio CSV export, shared 10,000 units/day quota kept small).
- All eleven `skills/*/skill.yaml` files: new, minimal (name, title, one-line
  description, `include_in_prompt: false`).
- `README.md`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `tests/`, and this
  `PROVENANCE.md`: new.
- The `skills/` directory layout is preserved exactly as upstream, so relative
  reads keep working: `chapters.py` and `retention.py` import the transcript parser
  from `../yt-edit/deadair.py`, and `swipe.py` reads the formulas from
  `../yt-script/hooks.json`. Each tool additionally checks its own folder first,
  so a lone copied skill folder still works.
- The two skills `yt-retention` and `yt-viral` were previously adopted singly into
  `~/workspace/custom-skills/`; their adapted playbook text was reused here,
  adjusted for this package's mirrored folder layout. The hardened tools were
  synced back into `~/workspace/custom-skills/` after hardening, so the live
  copies and this package match.

## What was excluded

- `.git/` (upstream history), `.claude-plugin/` (Claude Code marketplace manifests
  — not applicable to Muse), `.gitignore`, and any `__pycache__` build artifacts.
  No other files existed upstream.

## Safety audits (2026-10-27)

Two audits were run: one on the upstream code before adoption, one on the hardened
code after it. Both read every file and grepped the whole tree for network calls
(`requests`, `urllib`, `http.client`, `socket`), `subprocess`, `os.environ`,
`getpass`, API-key/secret/password/credential/token handling, `eval`/`exec`,
`pickle`, `os.system`, `shutil`, and file writes (all `open(` calls inspected).

Result, both times: clean. The only matches were benign:

- The word "credentials" in prose safety statements (a `skill.yaml` description,
  a `SKILL.md` line, the upstream README) — statements, not code.
- The word "secret" as entries in the vague-word lists inside `hookscore.py` and
  `title.py` — word-list data, not secret handling.
- All file opens are reads (input files and the bundled `hooks.json`); no tool
  writes any file.
- All imports across the six tools are Python standard library only: `argparse`,
  `csv`, `dataclasses`, `json`, `pathlib`, `re`, `statistics`, `sys`, `typing`.
  No third-party dependencies, no network access, no subprocesses, no environment
  or credential access.

The tools read local files you supply and print to stdout. They cannot publish, log
in, or reach the network. The `yt-viral` collection step is done by the agent
(read-only Data API connector in DIG's setup), not by `swipe.py` itself.

## Verification (2026-10-27)

- Before/after output diffs: the upstream tools and the hardened tools were run on
  identical synthetic inputs (hooks, titles, transcripts, retention CSV, collected
  JSON) and their stdout compared. Identical in every text-mode case; the only
  JSON-mode differences are the two documented additive changes (`matched` in
  `hookscore.py`, `skipped_invalid` in `swipe.py`). One genuine upstream bug was
  found this way: `chapters.py` draft titles changed between runs (set-order
  tiebreak); the hardened tool is deterministic across hash seeds.
- Test suite: `python3 -m unittest discover -s tests` — 28 tests, all passing.
  Covers happy paths, CLI error paths, edge cases, and determinism.
- Compile check: `python3 -m py_compile` passes on all six tools.
