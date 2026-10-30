# CCTV Viewer List Row Grouping — 2026-10-30

## Goal
Stop repeating the date/filename on every file-list row. Group rows under
non-clickable day headers; rows show only hour and size.

## Context (existing)
- `static/index.html` `load()` (lines 71-83) renders each file as
  `f.hour + ' — ' + f.name + ' — ' + (f.size/1048576).toFixed(1) + ' MB'` —
  the date appears twice (hour is `YYYY-MM-DD-HH`, filename repeats it).
- `web.py` `/api/files` sorts newest-first by name; `f.hour = name[8:-4]`.
- `mark()` highlights the row whose `dataset.n` matches mode
  (`(b.dataset.n||'live')===mode`); `boot()` deep-link restore matches
  `dataset.n===file` across `#list` children.
- Hours are UTC (parsed from filenames) — unchanged by this feature.

## Decisions (from brainstorming)
- Group by day: header div per distinct date; rows shrink to
  `HH:00 — <size> MB`.
- Headers are non-clickable divs carrying `data-n="day"` so `mark()` can never
  flag them active (`'day'` never equals a mode) and `boot()`'s filename match
  ignores them. Row buttons keep `dataset.n = <filename>` — deep-linking and
  highlighting logic untouched.
- LIVE row stays pinned above all groups.
- Display-only change: one file (`static/index.html`), no server/API changes.

## Design
In `load()`, track the previous row's date; when `f.hour.slice(0,10)` changes,
append `<div class="day" data-n="day">YYYY-MM-DD</div>` before that day's rows.
Row text becomes `f.hour.slice(11) + ':00 — ' + (f.size/1048576).toFixed(1) + ' MB'`.

Style block gains one rule:
`.day{color:#999;font-size:12px;padding:4px 2px;margin-top:8px}`

With a date filter active the list shows a single header + that day's rows.

## Error handling
None new. Existing paths (401, retention-deleted rows, empty day) render as
today — an empty list shows just the LIVE row, same as now.

## Testing
- `python -m unittest test_web test_app` stays green (frontend-only change).
- Manual, in the running preview: day headers appear between groups; rows show
  `HH:00 — size`; active highlight still tracks selection; deep-link
  `?file=archive_....mp4` still restores, plays, and highlights; LIVE click
  returns to live; date filter shows one header.

## Out of scope
Local-timezone conversion, collapsible groups, thumbnails.

## Files to change
- `static/index.html` — `load()` row rendering + one `.day` CSS rule.
