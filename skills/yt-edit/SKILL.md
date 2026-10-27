# yt-edit

An edit decision list from a timestamped transcript. It prints the cuts. You apply them.

```bash
python3 deadair.py transcript.srt              # srt, vtt or whisper json
python3 deadair.py transcript.srt --floor 0.35 --json
```

No transcript yet? Ask for one, or produce one first — `whisper`, `faster-whisper`, or the caption track YouTube generates on an unlisted upload all work. Do not guess at timings.

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook and run the tool with plain Python from this folder. The tool only reads the transcript file and prints; it never touches media.

## What it finds

- **DEAD** — gaps longer than the floor (default 0.45s), trimmed from the MIDDLE so both sides keep a breath. Cutting flush against speech is what makes a tightened take sound gasping.
- **FILLER** — cues that are nothing but "um", "so yeah", "basically".
- **REPEAT** — a sentence restarted. Compared against the last cue that was actually speech, not the literal previous cue, because most retakes have an "um" between the two attempts.

## What it will not do

It does not touch media. It has no opinion about B-roll. A 40% cut on the report is a 40% cut of SPEECH, and if the video has a long silent demo in it that number is wrong — check the report against the footage before you trust the runtime at the bottom.

## Fit in DIG's workflow

Limited fit, stated plainly: this workflow assembles videos from 10-second generated clips plus recorded voiceover, not from raw talking-head takes, so dead-air/filler detection only applies where a real spoken transcript exists (for example, voiceover timings). Do not force it onto clip assemblies with no spoken track.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
