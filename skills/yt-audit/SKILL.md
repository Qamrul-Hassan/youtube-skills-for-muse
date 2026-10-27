# yt-audit

An audit that lists twenty problems is a way of avoiding the one that matters. This ends in ONE fix.

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook and run the two tools with plain Python from their own folders:

```bash
python3 ../yt-package/title.py titles.txt
python3 ../yt-script/hookscore.py hooks.txt
```

## Before you write

1. Read the voice profile if one exists: `templates/voice.md` in this package, filled in for the creator. If it does not exist, ask for **three of their own videos**, read or transcribe them, infer the voice, and fill the file in.
2. Never invent a number, a result or a source. If a figure would strengthen a line and you do not have one, ask for it or write the line without it.

## What to look at, in this order

1. **The last ten titles, as a set.** Read them as a list, the way the channel page shows them. Do they promise different things? Run them through `../yt-package/title.py`. A channel where every title is the same shape has a format problem, not a title problem.
2. **The thumbnails, at feed size.** Shrink them. What survives? If three of them are unreadable at that size, that is the fix and nothing else matters yet.
3. **The first fifteen seconds of the three most recent.** Transcribe them and score with `../yt-script/hookscore.py`. This is where most channels lose.
4. **Upload rhythm.** Not frequency — CONSISTENCY. Six videos in one week and then nothing for a month is worse than one a fortnight forever.
5. **The retention shape**, if they can export it. `/yt-retention`.

## What to hand back

- The single biggest fix, named, with what to do this week.
- Three things that are already working, so they do not break them. Be specific; "your energy is good" is not an observation.
- What NOT to do yet, and why.

Never open an audit with praise you do not mean, and never end one with a list of twenty things.

## Honest limits

- `hookscore.py` is a heuristic, NOT a predictor — a high score is not a promise, and it barely separates a creator's own hits from misses.
- Retention comes only from a Studio export the user supplies. The read-only API cannot see retention, impressions, or CTR, and an audit must never present public view counts as if they were those metrics.

## Fit in DIG's workflow

Collect titles and public view counts only through the existing read-only YouTube Data API connector (`~/workspace/custom-connectors/custom.youtube-data-api/`, `bin/list_videos.py`) — never scrape, never log in, never share keys, no OAuth. Keep collections small: quota is shared at 10,000 units/day. Thumbnails and hooks come from files the user sends. DIG audits and verifies; it never publishes, edits, or auto-schedules anything.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
