# yt-viral

Find what is actually working in a niche and rank it by how far each video beat its own channel's median — then name the title formula. Raw view counts rank channel size, not ideas.

## When to use

Competitor research, topic selection, "what's working right now", or a swipe file — for example before picking the next Forgotten Record topic or checking how a competitor framed the same disaster.

## Collecting the input (DIG route — no scraping)

Do NOT scrape pages and do NOT use yt-dlp. Collect through DIG's existing read-only YouTube Data API connector (`~/workspace/custom-connectors/custom.youtube-data-api/`, `bin/list_videos.py <channel_id>`), which is already approved and needs no new key or login. That connector returns public title/view/duration data per channel; build `collected.json` from it:

```json
[{"channel": "...", "title": "...", "views": 412000, "url": "...", "duration": 613}]
```

Rules:

- At least **four videos per channel**, or the median means nothing. The tool skips thinner channels and says so — never rank on one or two videos.
- Public listings only. Never a logged-in session, never the user's credentials, never the DIG-read API key shared anywhere.
- Quota is shared (10,000 units/day across his tooling). Keep collections small — a handful of channels per run — and say so if a big sweep would cost quota.

## Running it

Run from this folder, with plain Python — there is no Claude Code plugin to install:

```bash
python3 swipe.py collected.json --min 2.0
python3 swipe.py collected.json --min 2.0 --json
```

The tool reads the 21 title formulas from `../yt-script/hooks.json` (same relative layout as upstream) — keep the `skills/` layout intact so that read keeps working. Default threshold is 1.5x when `--min` is omitted.

## Reading the output

The multiple is the signal. Hand back: the top five with their multiples, the formula each title used, and the ONE structural thing they share. Then the harder line — which of those the user could actually make this week, with what he has.

## Limits — say these out loud when presenting

- The formula is a judgement about the TITLE, matched against `hooks.json`. It is not a claim about why the video worked. Never present a formula as the cause of views.
- A multiple says a video outperformed its own channel. It says nothing about whether the topic fits this user's audience — apply his niche-fit filter ("would a Cyclops/Roanoke viewer watch this?" for Forgotten Record) before recommending anything.
- Nothing here publishes, touches an account, or uses an API key. The script only reads the local JSON file and prints.
