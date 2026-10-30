# List Row Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the redundant file-list rows (`hour — filename — size`) with day-group headers (`YYYY-MM-DD`) and compact rows (`HH:00 — size MB`).

**Architecture:** Display-only change to `static/index.html`: one `<div class="day">` inserted per distinct date while building the list in `load()`, one `.day` CSS rule appended to the style block. Deep-link/active-highlight logic untouched — row buttons keep `dataset.n=<filename>`; headers carry `data-n="day"` which matches no mode and no filename.

**Tech Stack:** Vanilla JS DOM building, existing single-file app, Python unittest suite for regression.

## Global Constraints

- Only file touched: `static/index.html` (`load()` at lines 76-81 and the `<style>` block at line 6). No server/API/HTML-structure changes.
- Row buttons must keep `dataset.n = f.name` and `b.onclick=()=>playMp4(f.name)` exactly — deep-linking and `mark()` depend on them.
- Header divs must be `className='day'`, `dataset.n='day'`, non-clickable.
- Row text format: `f.hour.slice(11)+':00 — '+(f.size/1048576).toFixed(1)+' MB'` (em-dash separators, matching existing rows).
- Header text: `f.hour.slice(0,10)` (i.e. `YYYY-MM-DD`).
- CSS stays minified one-rule-per-selector; the new `.day` rule goes before the `@media(min-width:768px)` block.
- Test suite command: `.venv/bin/python -m unittest test_web test_app` (from the worktree root).

---

## File Structure

- Modify `static/index.html:76-81` — row-building loop in `load()` gains day-header emission.
- Modify `static/index.html:6` — append one `.day` rule to the style block.

No new files. Server (`web.py`) and tests untouched.

---

### Task 1: Day headers + compact rows

**Files:**
- Modify: `static/index.html:6,76-81`

**Interfaces:**
- Consumes: `/api/files` response shape `{name, hour, size, mtime}` (unchanged), `#list` container, existing `mark()`/`boot()` behavior.
- Produces: nothing consumed elsewhere; `#list` now contains `div.day` elements alongside `button.row` elements.

- [ ] **Step 1: Run test suite for a green baseline**

Run: `.venv/bin/python -m unittest test_web test_app`
Expected: all tests PASS.

- [ ] **Step 2: Rewrite the row loop in `load()`**

In `static/index.html`, change:

```js
    fs.forEach(f=>{
      const b=document.createElement('button');
      b.className='row';b.dataset.n=f.name;
      b.textContent=f.hour+' — '+f.name+' — '+(f.size/1048576).toFixed(1)+' MB';
      b.onclick=()=>playMp4(f.name);list.appendChild(b);
    });
```

to:

```js
    let day='';
    fs.forEach(f=>{
      const dd=f.hour.slice(0,10);
      if(dd!==day){day=dd;const h=document.createElement('div');h.className='day';h.dataset.n='day';h.textContent=dd;list.appendChild(h);}
      const b=document.createElement('button');
      b.className='row';b.dataset.n=f.name;
      b.textContent=f.hour.slice(11)+':00 — '+(f.size/1048576).toFixed(1)+' MB';
      b.onclick=()=>playMp4(f.name);list.appendChild(b);
    });
```

Everything else in `load()` (LIVE row, 401 handling, `mark()` call) stays exactly as is.

- [ ] **Step 3: Add the `.day` CSS rule**

In the `<style>` block (line 6), change:

```html
#bar{display:flex;gap:8px;margin:12px 0}@media(min-width:768px){
```

to:

```html
#bar{display:flex;gap:8px;margin:12px 0}.day{color:#999;font-size:12px;padding:4px 2px;margin-top:8px}@media(min-width:768px){
```

- [ ] **Step 4: Re-run test suite**

Run: `.venv/bin/python -m unittest test_web test_app`
Expected: all tests PASS.

- [ ] **Step 5: Smoke check against the running preview server**

The preview server (PID from the controller, port 8081, serving this worktree) reads `index.html` per request, so no restart is needed:

Run: `curl -s http://127.0.0.1:8081/ | grep -c "className='day'"` → expect `1`; `curl -s http://127.0.0.1:8081/ | grep -c '.day{color:#999'` → expect `1`.
If the server is not running, start it as in the spec's preview instructions and re-check.

Manual (human, after review): refresh the preview — day headers `2026-10-29` / `2026-10-28` between groups; rows show `HH:00 — 0.0 MB`; active highlight still tracks selection; `?file=archive_2026-10-29-14.mp4` deep-link still restores and highlights; LIVE click returns to live; date filter shows one header.

- [ ] **Step 6: Commit**

```bash
git add static/index.html
git commit -m "feat(web): group file list under day headers, compact rows to hour + size"
```
