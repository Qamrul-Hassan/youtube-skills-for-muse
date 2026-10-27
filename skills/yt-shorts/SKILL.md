# yt-shorts

A Short cut out of a long video is not a clip of the best moment. It is a moment that **survives without the video around it**, which is a much smaller set.

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook. The one tool this skill uses is the hook scorer in the sibling folder, run with plain Python:

```bash
python3 ../yt-script/hookscore.py --hook "new first line"
```

## Picking

Read the transcript and find spans of 20–55 seconds where all three are true:

1. It opens on a complete thought. If the first sentence needs the previous minute, it is not a Short.
2. There is a turn in it — a claim, then something that complicates or proves it.
3. It ends on a line, not a trail-off.

Rank the candidates and show the top five with their timecodes and first line, so the user can reject one without reading the whole transcript.

## Writing each one

- **A NEW first line.** The long video's line assumes context this viewer does not have. Write the replacement and run it through `../yt-script/hookscore.py`.
- **On-screen text for the first two seconds**, different words from the spoken line.
- **A loop point**: what the last line sets up so the first line answers it.
- Vertical framing note — what gets cropped out of a 16:9 frame and whether that matters.

## Honest limits

`hookscore.py` is a heuristic, NOT a predictor — it separates deliberately bad hooks from real ones well, and a creator's own hits from misses barely at all. A low score is a reason to look again; a high score is not a promise.

## Fit in DIG's workflow

Stated plainly: this workflow makes standalone 9:16-native trailer Shorts, planned in advance at package time (three per long video, each carrying the long video as its Related Video), not transcript cutdowns of a talking-head video. Use this skill's picking method to find candidate moments, then map each one onto the scene-based clips that actually exist. Never invent a clip, a timecode, or a spoken line that is not in the transcript or the scene plan.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
