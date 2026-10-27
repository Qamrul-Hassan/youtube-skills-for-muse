# yt-package

The title and the thumbnail are ONE unit. Writing them separately is why most packaging fails: the thumbnail repeats the title, and half the click surface says the same thing twice.

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook and run the tool with plain Python from this folder:

```bash
python3 title.py --title "..." --thumb "AI RAN IT"
python3 title.py titles.txt            # one per line, ranked
```

## Before you write

1. Read the voice profile if one exists: `templates/voice.md` in this package, filled in for the creator. If it does not exist, ask for **three of their own videos**, read or transcribe them, infer the voice, and fill the file in.
2. Never invent a number, a result or a source. If a figure would strengthen a line and you do not have one, ask for it or write the line without it.

## Rules the tool enforces, and why

- **60 characters** is where desktop search truncates, **40** is a mobile home feed. Both are reported because they fail differently: a desktop cut loses the tail, a mobile cut can lose the subject.
- **The thumbnail must not repeat the title.** Different words, same promise.
- **Three words maximum on the thumbnail.** At feed size a fourth word is a grey smear.
- **A number, a name or a date** beats every adjective available to you.
- **Two all-caps words is the ceiling** before a title reads as spam.

## Write ten, keep two

Generate ten titles, run them all through `title.py`, show the top three with their scores and the specific issue on each. For the winner, write the thumbnail brief: the expression, the framing, the three words, and what the background has to do to hold contrast at feed size.

## Fit in DIG's workflow

Title-plus-thumbnail as one unit is already a standing rule here, and the linter is a mechanical second check on candidates — it does not replace judgement about the story or the audience. Scores are the tool's heuristic (14 points per issue, 4 per good mark), not a prediction of CTR. Nothing here reads Studio data: impressions and CTR are Studio-only and cannot be checked through the read-only API.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
