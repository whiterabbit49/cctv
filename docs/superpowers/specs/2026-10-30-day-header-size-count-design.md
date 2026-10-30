# Day Header Size + Count — 2026-10-30

## Goal
Show each day group's total archive size and file count on the day header:
`2026-10-29 — 1.2 GB · 24 files`.

## Context (existing)
- `static/index.html` `load()` (lines 76-84) groups rows: a `div.day` header per
  distinct `f.hour.slice(0,10)`, rows show `HH:00 — X.X MB`.
- Headers are emitted before a day's rows are walked, so a same-pass sum is
  impossible — the totals must be computed before rendering.
- Row size display is `(f.size/1048576).toFixed(1)+' MB'` (single hours are
  always MB-scale).

## Decisions (from brainstorming)
- Pre-pass: one loop over `fs` building `sum[dd]` (bytes) and `cnt[dd]` before
  the render loop.
- Adaptive unit on headers only: `X.X GB` at >= 1 GiB, else `X.X MB`; row text
  unchanged.
- Pluralization: `1 file` vs `N files`.
- The current day's group sums only consolidated hours (the live hour is HLS
  until ffmpeg finishes it) — partial-day totals are expected behavior.

## Design
In `load()`, before the render loop:

```js
const sum={},cnt={};
fs.forEach(f=>{const dd=f.hour.slice(0,10);sum[dd]=(sum[dd]||0)+f.size;cnt[dd]=(cnt[dd]||0)+1;});
const fmt=b=>b>=1073741824?(b/1073741824).toFixed(1)+' GB':(b/1048576).toFixed(1)+' MB';
```

Header emission becomes:
`h.textContent=dd+' — '+fmt(sum[dd])+' · '+cnt[dd]+' file'+(cnt[dd]>1?'s':'');`

Everything else (rows, LIVE row, `mark()`, `boot()`, CSS) unchanged.

## Error handling
None new. Empty/401 list renders as today (LIVE row only, no headers).

## Testing
- `python -m unittest test_web test_app` stays green (frontend-only).
- Manual, in preview: headers show `YYYY-MM-DD — X.X GB|MB · N files`; totals
  match the sum of that day's row sizes; single-file day shows `1 file`; deep-link,
  LIVE, date filter, active highlight all unchanged.

## Out of scope
Per-hour deltas, sparklines, average sizes, local timezone.

## Files to change
- `static/index.html` — `load()` only.
