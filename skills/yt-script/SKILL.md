# yt-script

One idea into a script somebody finishes. Five hooks off 21 formulas, scored, then the spoken script with the retention beats marked.

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook and run the tool with plain Python from this folder:

```bash
python3 hookscore.py hooks.txt              # rank hook options, one per line
python3 hookscore.py --hook "one line"      # score a single hook
```

The 21 formulas live in `hooks.json` in this folder; `hookscore.py` reads them from its own directory.

## Before you write

1. Read the voice profile if one exists: `templates/voice.md` in this package, filled in for the creator. That is how they talk, the words they never use, who they are talking to, what they will not claim. If it does not exist, ask for **three of their own videos**, read or transcribe them, infer the voice, and fill the file in. A script in the wrong voice is worse than no script, because the words have to be read out loud. For a faceless channel, "voice" means the narration style, the VO wording rules, and what the channel will not claim — not an on-camera persona.
2. Never invent a number, a result or a source. If a figure would strengthen a line and you do not have one, ask for it or write the line without it.

## The shape

**The first 15 seconds is the whole job.** It does three things or the video leaks: confirm the click the title promised, open a question the viewer cannot close, and prove the payoff exists.

1. **Hook.** Write FIVE against the 21 formulas in `hooks.json`, run them through `hookscore.py`, keep the top two, and show both with their scores. Never hand over one hook.
2. **The turn** (0:15–0:45). Say what the video is going to do, in one sentence, and start doing it. No channel intro, no "before we get started", no subscribe pitch. Those are the single most common cause of the 0:30 cliff.
3. **The body.** One idea per beat. Mark each beat with what is ON SCREEN, not just what is said — a voiceover with nothing to look at is a podcast.
4. **The payoff.** Deliver the thing the hook promised, explicitly, and say that you are delivering it.
5. **The close.** One ask. Not three.

## What to hand back

- The two best hooks with their scored panels.
- The script, beat by beat, with `[ON SCREEN: ...]` on every beat.
- The runtime estimate at 150 words per minute.
- One line naming which formula the winning hook used and why it fits this idea.

## Honest limits — say these, do not soften them

- `hookscore.py` is a heuristic, NOT a predictor. The author calibrated it against 74 real short-form hooks: it separates deliberately bad hooks from real ones well, and it separates a creator's own hits from their own misses barely at all. A low score is a reason to look again; a high score is not a promise.
- The formula classifier judges the words in the hook, not why a video worked.

## Fit in DIG's workflow

In this setup Gemini drafts scripts and DIG verifies them before anything goes live; DIG never auto-publishes. Use this skill's method to check drafts and to write new hook options — as a check on the draft, not as a replacement for verification of every figure, name, and claim.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
