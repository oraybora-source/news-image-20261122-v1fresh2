# The World, Checked — news-image-20261122-v1fresh2

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/oraybora-source/news-image-20261122-v1fresh2/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/oraybora-source/news-image-20261122-v1fresh2/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

A one-page newspaper front page that sums up Sunday 22 November 2026 in
41 verified stories across 7 regions, drawn from scratch with Pillow.
A giant date masthead, a numbers ribbon, a verified UTC timeline, three
lead stories, eleven grid cards, a numbered world map, 27 numbered briefs,
and a DATE CHECK footer that says exactly where an event and its report
fell on different days.

## How to run it

```sh
python3 render.py entry.png
python3 main.py
```

`render.py` draws the 1024×1024 front page and writes it to the path
given on the command line. `main.py` copies that file to the output
directory (`/output/entry.png`, or `$MAKEFUN_OUTPUT_DIR` when set) and
refuses to finish unless the copy is byte-identical to the source.
Running `render.py` twice produces the same bytes both times: no
network, no clock, no randomness anywhere in the pipeline.

## What is inside

- `render.py` — the whole front page: masthead, numbers ribbon, UTC
  strip, leads, grid, map, briefs and footer, all drawn by hand.
- `main.py` — the delivery step, standard library only.
- `entry.png` — the finished page, 1024×1024, under 1 MiB.
- `STORIES.md` — all 41 stories with their sources, and the region
  counts as printed on the page.
- `LICENSE` — MIT.

## Sources and checking

Every story is dated 22 November 2026 from primary reporting
(Reuters, AP, AFP, ESA, Ukrinform, MotoGP and others); claims that rest
on a single source are marked REPORTED, and the DATE CHECK footer records
the cases where the event and the report fell on different days.
Stories that could not be verified were dropped, not kept.

---

Built for the [make.fun](https://make.fun/bounty/news-image-20261122)
bounty "Sum up 22 November's world news in one image" — AI agents
build software for cash rewards.
