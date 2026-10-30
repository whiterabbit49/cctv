# CCTV Viewer Responsive File-List Layout — 2026-10-30

## Goal
On desktop (viewport ≥768px), place the video file list in a right sidebar next to
the player. On mobile (<768px), keep the list below the player (current behavior).

## Context (existing)
- `static/index.html` is the entire UI: single-file, no build step, inline `<style>`,
  vanilla JS. Layout is one 960px column: `<h2>` header, `<video>`, controls bar
  (date picker + clear + token), then `#list` (flat file list, flex:1, scrolls).
- `main` is `height:100dvh; display:flex; flex-direction:column` — the app fits the
  viewport; only `#list` scrolls.
- All automated tests (`test_web.py`, `test_app.py`) are server-side; none assert
  CSS/layout.

## Decisions (from brainstorming)
- Desktop layout: controls stay under the video (left column = header, video, bar;
  right column = file list only).
- Desktop container widens from 960px to 1400px so the player gains space; sidebar
  is a fixed 320px column.
- Implementation: CSS Grid `grid-template-areas` on `main`, no HTML restructuring,
  no JS changes (Option A). Wrappers (Option B) and JS `matchMedia` (Option C)
  rejected.
- Breakpoint: 768px.

## Design
Only the `<style>` block in `static/index.html` changes.

**Mobile (<768px, default):** unchanged single column — header, video, bar, list.
`main` keeps `display:flex; flex-direction:column; max-width:960px`.

**Desktop (≥768px, media query):**
```css
main {
  max-width: 1400px;
  display: grid;
  grid-template-columns: 1fr 320px;
  grid-template-areas:
    "head head"
    "video list"
    "bar list";
  grid-template-rows: auto 1fr auto;
  column-gap: 16px;
}
h2 { grid-area: head; }
video { grid-area: video; align-self: start; }
#bar { grid-area: bar; }
#list { grid-area: list; margin-top: 0; }
```
- Grid areas assign existing flat children to columns without touching DOM order.
- `video` keeps `width:100%` (fills the `1fr` column, keeps 16:9 via element ratio);
  `align-self:start` stops it stretching to fill a taller row.
- Scroll behavior preserved: page still fits `100dvh`; `#list` (already
  `overflow-y:auto; min-height:0`) becomes the independently scrolling sidebar.
- `#list` needs `min-height:0` respected in grid context (already present) so the
  `1fr` video row doesn't force overflow.

## Error handling
None — pure presentation. All existing failure paths (401 token, live 404 retry,
retention-deleted rows) render inside `#list` and work identically in either
layout.

## Testing
- Automated: `python -m pytest` / `python -m unittest` suite stays green (no
  server or markup changes).
- Manual, browser devtools responsive mode:
  - ~375px wide: stacked layout identical to today; list scrolls, page doesn't.
  - ~1280px wide: two columns; header spans both; list scrolls independently;
    no double scrollbars; video is noticeably wider than before (1400px cap).
  - Resize across 768px: layout switches cleanly, no clipping.

## Out of scope
List row thumbnails, collapsible sidebar, drag-to-resize, sticky player on
mobile scroll, dark/light themes.

## Files to change
- `static/index.html` — `<style>` block only.
