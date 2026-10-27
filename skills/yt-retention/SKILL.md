# yt-retention

Read a YouTube Studio audience-retention export and find where viewers actually leave, then name the single biggest leak and one change for it.

## When to use

The user shares a Studio retention export, or asks why viewers stop watching / how pacing failed on a published video. This is the only retention signal DIG can read: the read-only YouTube Data API cannot see retention (Studio-only data, needs OAuth DIG does not have). The CSV always comes from the user.

## Getting the input

Studio → the video → Analytics → Engagement → audience-retention chart → download icon → "Audience retention". Two columns: position (percent or seconds) and percentage still watching. If the axis is a percentage, pass `--duration <seconds>` so cliff positions resolve to seconds.

## Running it

Run from this folder, with plain Python — there is no Claude Code plugin to install:

```bash
python3 retention.py retention.csv --duration 660
python3 retention.py retention.csv --duration 660 --transcript transcript.srt
python3 retention.py retention.csv --duration 660 --json
```

The `--transcript` mode reads its transcript parser from the sibling folder (`../yt-edit/deadair.py`, same relative layout as upstream) — keep the `skills/` layout intact so that import keeps working. With a transcript, the tool prints what was being said at each cliff — that is the only actionable version of the report.

## Reading the output

Three different problems, three different fixes:

- **HOOK LEAK** — lost in the first 30 seconds. Under 25% is healthy (author's heuristic, not a YouTube rule). A leak here is always the first fifteen seconds of script, never the edit. Fix the first line before anything else.
- **CLIFFS** — single steep drops (over 0.8%). A cliff is a moment: an unsignposted topic change, a long setup. Name the moment and what was said there.
- **SLIDE** — the steady bleed across the middle. A flat slide is pacing: the fix is cutting, not rewriting.

## What to hand back

The single biggest leak and one change for it — not a list of five. Then, only if asked, the rest. If the hook leak is healthy and the slide is flat, say the video is fine and the problem is packaging, and route to the title/thumbnail check.

## Limits

- The tool reads the export exactly as given; garbage export in, garbage verdict out. Check the CSV has at least 8 data points (the tool refuses fewer).
- Thresholds (25% hook leak, 0.8% cliff) are the original author's heuristics. Present them as such, never as YouTube law or a prediction.
- Nothing here publishes, touches an account, or uses an API key. The script only reads local files and prints.
