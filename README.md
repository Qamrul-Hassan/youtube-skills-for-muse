# YouTube Skills for Muse

> **What this is:** eleven ready-to-use agent skills plus six small Python tools that help
> plan, script, package, and review YouTube videos — built for the Muse agent. No signup,
> no API key, no login. **Nothing here publishes anything.** You read the output, you decide,
> you upload.

If you opened this repo wondering what it is for: it makes a Muse agent useful on a YouTube
channel on day one. Each skill is a `SKILL.md` playbook the agent reads, plus — where a
judgement needs arithmetic — a local Python tool that does the arithmetic. That is the whole
idea: prompts where judgement lives, code where counting lives.

## Who this is for

- A creator running a YouTube channel (talking-head, faceless, documentary — any format)
  with a Muse agent helping them.
- An agent (like DIG) that needs repeatable, checkable YouTube workflows instead of
  re-inventing them per video.

It is **not** an uploader, autoposter, analytics dashboard, or growth hack. It cannot publish,
log in, or reach the network. See [Honest limits](#honest-limits).

## Quickstart (60 seconds)

Requirements: Python 3.10 or newer. Nothing to install — standard library only.

```bash
# 1. Score a hook line (5 properties, weakest-link verdict):
python3 skills/yt-script/hookscore.py --hook "Why did 114 people die when two walkways fell in 1981?"

# 2. Lint a title against its thumbnail text (the pairing is the unit):
python3 skills/yt-package/title.py --title "How Engineers Sunk a $350M Skyscraper" --thumb "BUILT ON MUD"

# 3. Read a Studio retention export (CSV you download from YouTube Studio):
python3 skills/yt-retention/retention.py retention.csv --duration 660
```

Sample output (real run of command 1):

```
  Why did 114 people die when two walkways fell in 1981?
  ------------------------------------------------------
    SPECIFICITY   78  ###############
    ADDRESS       26  #####
    STAKES        62  ############
    CURIOSITY     59  ###########
    BREVITY      100  ####################
    VERDICT       49  WEAK
    formula      The Question  (2 patterns matched)
    weakest      ADDRESS - say 'you' in the first six words
```

To adopt a skill into your own Muse workspace, copy its folder into
`~/workspace/custom-skills/` — or just use the skills in place from this directory.
Then spend ten minutes on `templates/voice.md`: fill in the channel's voice profile
(the script and comment skills read it), or hand the agent three of your videos and ask
it to write the profile from them.

## The eleven skills

| Skill | Input | What you get back |
| --- | --- | --- |
| `yt-script` | One idea | Five hooks from 21 formulas, scored, then the spoken script with retention beats marked |
| `yt-package` | Title + thumbnail text | The pairing linted as one unit: truncation, duplication, vagueness |
| `yt-edit` | Transcript (.srt/.vtt/Whisper .json) | Edit decision list: dead air, filler cues, retakes, with timecodes |
| `yt-comment` | Comment section | Triaged into four piles, replies in your voice, which one to pin |
| `yt-plan` | Hours you actually have | A week that fits: one anchor, one cheap one, three Shorts |
| `yt-viral` | Collected video list (.json) | Niche outliers ranked by multiple over each channel's own median |
| `yt-retention` | Studio retention export (.csv) | Hook leak, cliffs, slide — the single biggest leak and one change |
| `yt-shorts` | Long video + transcript | The Shorts already inside it, each with a new first line |
| `yt-seo` | Video topic | Description, the tags worth having, the three queries to win |
| `yt-chapters` | Transcript | Chapters validated against YouTube's rules (00:00 start, 3+, 10s minimum) |
| `yt-audit` | Whole channel | One fix, not twenty |

## The six tools

Every tool runs on a clean Python 3 with no dependencies, reads only local files you supply,
and prints to stdout. They are the reason the skills are not just prompts.

```bash
python3 skills/yt-script/hookscore.py --hook "one line"        # 5-property hook panel
python3 skills/yt-package/title.py --title "..." --thumb "..." # title + thumbnail linter
python3 skills/yt-edit/deadair.py transcript.srt               # edit decision list
python3 skills/yt-chapters/chapters.py transcript.srt          # validated chapters
python3 skills/yt-retention/retention.py retention.csv         # where they left, and why
python3 skills/yt-viral/swipe.py collected.json --min 2.0      # outliers by own-channel multiple
```

Every tool also takes `--json` for machine-readable output, and `--help` for its full usage.
Keep the `skills/` layout intact: `chapters.py` and `retention.py` find the transcript
parser in `../yt-edit`, and `swipe.py` reads the formulas from `../yt-script/hooks.json`
(each also checks its own folder first, so a lone copied skill folder still works).
Moving a tool out of its folder without its neighbours breaks those reads.

## Project structure

```
.
├── LICENSE                    # MIT (upstream licence)
├── README.md                  # this file
├── CHANGELOG.md               # what changed vs upstream, and why
├── PROVENANCE.md              # upstream source, pinned commit, verbatim/adapted list, audits
├── pyproject.toml             # project metadata, Python >= 3.10
├── skills/                    # the eleven skills (SKILL.md + skill.yaml + tools)
│   ├── yt-script/             # hookscore.py + hooks.json (21 hook formulas)
│   ├── yt-package/            # title.py
│   ├── yt-edit/               # deadair.py (shared transcript parser)
│   ├── yt-comment/
│   ├── yt-plan/
│   ├── yt-viral/              # swipe.py
│   ├── yt-retention/          # retention.py
│   ├── yt-shorts/
│   ├── yt-seo/
│   ├── yt-chapters/           # chapters.py
│   └── yt-audit/
├── templates/
│   └── voice.md               # voice profile template — fill this in first
└── tests/                     # stdlib-only tests + fixtures (see below)
```

## Code quality

- **Python 3.10+**, standard library only. No third-party packages, no network, no
  subprocesses. If it cannot run on a clean `python3`, it is a bug.
- **Typed, documented, CLI-standard:** every tool uses `argparse` (`--help` works),
  typed signatures, named constants instead of magic numbers, errors on stderr with
  the tool's name and a non-zero exit code (2 for bad usage, 1 for bad input).
  Scoring and linting math is unchanged from upstream — verified by before/after
  output diffs on identical inputs (see `CHANGELOG.md`).
- **Tested:** `tests/` holds 28 `unittest` tests (standard library only) with small
  fixtures, covering happy paths, CLI error paths, edge cases, and output
  determinism (chapter titles no longer depend on hash seed). Run them with:

```bash
python3 -m unittest discover -s tests -v
```

## Safety

The tools read local files and print. They cannot publish, log in, or reach the network —
verified by reading every file and grepping the whole tree (see `PROVENANCE.md` for the
audit record). Channel and video data for `yt-viral` / `yt-audit` is collected by the
agent through a read-only YouTube Data API connection — never by scraping, never with
the user's credentials. Retention data only ever comes from a Studio CSV export the
user supplies; the Data API cannot see retention.

## Honest limits

The part most packs leave out — kept from the upstream author:

- **It does not publish.** YouTube's Data API would allow publishing with your own OAuth.
  It is still not built here: every skill ends in a block you copy and a question —
  ship it, or change it? Anything that claims to run your channel unattended should be
  read with that distinction in mind.
- **`hookscore.py` is a heuristic, not a predictor.** The panel was built and calibrated
  against 74 real short-form hooks (the first 15 seconds of auto-captions, top-8 and
  bottom-8 by views across five channels). It separates deliberately bad hooks from real
  ones well. It separates a given creator's hits from their own misses barely at all.
  A low score is a reason to look again; a high score is not a promise.
- **The formula classifier is about the words, not the result.** When `yt-viral` says a
  title used The Statistic, that is a judgement about the title you can see, not a claim
  about why the video got its views.
- **`yt-viral` reads, it does not scrape.** Public listings only. It never logs in as you
  and never touches your credentials. In this adaptation, collection goes through the
  read-only Data API connector instead of `yt-dlp`.
- **Tags barely matter** and this pack says so instead of selling you a tag generator.
- **Nothing invents a number.** If a skill wants a figure it does not have, it asks you
  for it or writes the line without it.

## Credits and licence

Adapted from [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill)
by Jake Schincariol, pinned at commit `a2feb21` (2026-09-16), for use with Muse — the
upstream pack targets Claude Code. The six tools were then hardened (bug fixes, typed
argparse CLIs, tests); `hooks.json`, `templates/voice.md`, and `LICENSE` are byte-identical
to upstream. Full details in `PROVENANCE.md` and `CHANGELOG.md`.

MIT. Use it, change it, ship it.
