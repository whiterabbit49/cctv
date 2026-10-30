# CCTV Viewer Responsive File-List Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On desktop (viewport ≥768px), show the file list in a 320px sidebar to the right of the player; on mobile (<768px), keep today's stacked layout (list below the player).

**Architecture:** Pure CSS change — append one `@media(min-width:768px)` rule to the inline `<style>` block of the single-file UI `static/index.html`. The media query switches `main` from the base flex column to a CSS Grid with named areas (`"head head" "video list" "bar list"`). No HTML, no JS, no server changes.

**Tech Stack:** Plain CSS (grid-template-areas), existing vanilla-JS single-page app, Python unittest suite for regression.

## Global Constraints

- Only file touched: `static/index.html`, and only its `<style>` block (line 6). No HTML or JavaScript changes.
- Base (mobile) rules must remain byte-identical — desktop styling lives entirely inside the new media query.
- Breakpoint: `min-width:768px`. Desktop container: `max-width:1400px`. Sidebar column: `320px`. Column gap: `16px`.
- Grid rows: `auto auto 1fr` with `align-self:start` on `video` and `#bar` (controls hug the video, not the viewport bottom).
- CSS stays minified one-rule-per-selector, matching the existing style block's formatting.
- Existing test suite command: `python3 -m unittest test_web test_app` (matches CI in `.github/workflows/ci.yaml`).

---

## File Structure

- Modify `static/index.html:6` — append one `@media` block before `</style>`. Single responsibility of this change: responsive layout.

No new files. `web.py` serves `static/index.html` verbatim (`web.py:62,87-92`), so no server work.

---

### Task 1: Desktop grid sidebar via media query

**Files:**
- Modify: `static/index.html:6` (`<style>` block)

**Interfaces:**
- Consumes: existing DOM ids/classes only — `main`, `h2`, `video`, `#bar`, `#list` (all already present in `static/index.html:8-12`).
- Produces: nothing consumed elsewhere; layout is terminal presentation.

- [ ] **Step 1: Run test suite for a green baseline**

Run: `python3 -m unittest test_web test_app`
Expected: all tests PASS (CSS cannot affect them; this proves the working tree is green before the edit).

- [ ] **Step 2: Append the media query to the `<style>` block**

In `static/index.html` line 6, change the end of the style string from:

```html
#bar{display:flex;gap:8px;margin:12px 0}</style>
```

to:

```html
#bar{display:flex;gap:8px;margin:12px 0}@media(min-width:768px){main{max-width:1400px;display:grid;grid-template-columns:1fr 320px;grid-template-areas:"head head" "video list" "bar list";grid-template-rows:auto auto 1fr;column-gap:16px}h2{grid-area:head}video{grid-area:video;align-self:start}#bar{grid-area:bar;align-self:start}#list{grid-area:list;margin-top:0}}</style>
```

Notes for the implementer:
- Everything before `@media` stays exactly as it is — do not reformat the existing rules.
- `#list` already has `flex:1;overflow-y:auto;min-height:0` (line 6). In the grid context the flex property is ignored and `min-height:0` + `overflow-y:auto` make the sidebar scroll independently — no override needed.

- [ ] **Step 3: Re-run test suite**

Run: `python3 -m unittest test_web test_app`
Expected: all tests PASS.

- [ ] **Step 4: Manual layout verification**

Start a local server with dummy archive files (no token, no RTSP needed; `/api/live` will 404 and the player shows a black box — the layout still renders):

```bash
mkdir -p /tmp/cctv-layout-check
for h in 04 05 06 07 08 09 10 11; do printf 'dummy' > /tmp/cctv-layout-check/archive_2026-10-30-$h.mp4; done
ARCHIVE_PATH=/tmp/cctv-layout-check python3 -m uvicorn web:app --port 8081
```

Open `http://127.0.0.1:8081` in a browser with devtools responsive mode:

- **375×700 (mobile):** single column identical to today — header, video, date/token bar, list below; only the list scrolls, page doesn't.
- **1280×800 (desktop):** two columns — header spans both, video + controls in the left column, file list in a 320px right sidebar with its own scrollbar; the controls bar sits directly under the video (not at the viewport bottom); no page-level scrollbar; video clearly wider than the old 960px cap.
- **Resize across 768px:** layout switches cleanly, no clipping or double scrollbars.

Then stop the server and clean up:

```bash
rm -rf /tmp/cctv-layout-check
```

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat(web): file list as right sidebar on desktop, stacked below player on mobile"
```
