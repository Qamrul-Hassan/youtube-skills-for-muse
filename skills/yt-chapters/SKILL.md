# yt-chapters

YouTube chapters from a transcript, validated against YouTube's own rules so they actually render.

```bash
python3 chapters.py transcript.srt --target 8
```

## Using this with Muse

There is no Claude Code plugin to install. Read this file as the playbook and run the tool with plain Python from this folder. The tool reads its transcript parser from the sibling folder (`../yt-edit/deadair.py`, same relative layout as upstream) — keep the `skills/` layout intact so that import keeps working. The tool only reads the transcript file and prints; it never touches media or any account.

## The rules, which are not optional

A chapter list that breaks any of these silently does not become chapters at all — the block just sits in the description doing nothing:

- The first entry must be **00:00**.
- There must be **at least three**.
- Each must be **at least 10 seconds** long.

The tool checks all three and tells you when a list is invalid rather than letting you paste it.

## Retitle every line

`chapters.py` finds the BOUNDARIES well — it scores the pauses you actually took by how much the vocabulary shifts across them. The titles it emits are the topic words, and they are a draft. A chapter called "Thumbnails Titles Packaging" is a placeholder. Rewrite each one as the promise of that section, in the creator's voice, three to five words.

Chapters are also a retention diagnostic: if a section cannot be named in five words, it is two sections or it is filler.

## Fit in DIG's workflow

Chapter lists in metadata packages here are written from scene plans, not from transcripts. Use this tool's output as a draft or a boundary check when a real transcript exists — and retitle every line either way. Never paste tool output as-is, and never present tool-drafted titles as verified wording.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user copies, and the last line of every run is the question: **ship it, or change it?**
