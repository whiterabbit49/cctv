# Day Header Size + Count Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day-group headers show the day's total size and file count: `YYYY-MM-DD — X.X GB|MB · N files`.

**Architecture:** Pure display change to `static/index.html` `load()`: a pre-pass builds `sum[dd]`/`cnt[dd]` maps plus an adaptive `fmt()` byte formatter; header emission uses them. Rows, LIVE row, deep-linking, highlighting, and CSS are untouched.

**Tech Stack:** Vanilla JS, existing single-file app, Python unittest suite for regression.

## Global Constraints

- Only file touched: `static/index.html`, `load()` only. No CSS/HTML/server changes.
- Row text (`HH:00 — X.X MB`), LIVE row, `mark()`, `boot()` behavior unchanged.
- Header text: `dd+' — '+fmt(sum[dd])+' · '+cnt[dd]+' file'+(cnt[dd]>1?'s':'')` — em-dash before size, middle dot before count.
- `fmt`: `X.X GB` when bytes >= 1073741824, else `X.X MB`.
- Headers remain `div.day` with `data-n="day"`.
- Test suite command: `.venv/bin/python -m unittest test_web test_app` (from the worktree root, once created).

---

## File Structure

- Modify `static/index.html:76-84` — `load()` gains pre-pass + formatter; header emission uses them.

No new files.

---

### Task 1: Day totals on headers

**Files:**
- Modify: `static/index.html:76-84`

**Interfaces:**
- Consumes: `/api/files` shape `{name, hour, size, mtime}` (unchanged), existing grouping loop.
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Run test suite for a green baseline**

Run: `.venv/bin/python -m unittest test_web test_app`
Expected: all tests PASS.

- [ ] **Step 2: Add the pre-pass and formatter**

In `static/index.html` `load()`, change:

```js
    let day='';
    fs.forEach(f=>{
      const dd=f.hour.slice(0,10);
      if(dd!==day){day=dd;const h=document.createElement('div');h.className='day';h.dataset.n='day';h.textContent=dd;list.appendChild(h);}
```

to:

```js
    const sum={},cnt={};
    fs.forEach(f=>{const dd=f.hour.slice(0,10);sum[dd]=(sum[dd]||0)+f.size;cnt[dd]=(cnt[dd]||0)+1;});
    const fmt=b=>b>=1073741824?(b/1073741824).toFixed(1)+' GB':(b/1048576).toFixed(1)+' MB';
    let day='';
    fs.forEach(f=>{
      const dd=f.hour.slice(0,10);
      if(dd!==day){day=dd;const h=document.createElement('div');h.className='day';h.dataset.n='day';h.textContent=dd+' — '+fmt(sum[dd])+' · '+cnt[dd]+' file'+(cnt[dd]>1?'s':'');list.appendChild(h);}
```

The row-emission lines inside the same `forEach` and everything after it stay exactly as they are.

- [ ] **Step 3: Re-run test suite**

Run: `.venv/bin/python -m unittest test_web test_app`
Expected: all tests PASS.

- [ ] **Step 4: Smoke check against a local preview**

Start (or reuse) a preview server serving this worktree with dummy files sized to exercise both units — e.g. per day: one 2 GiB file (2147483648 bytes) plus a few small ones:

```bash
mkdir -p /tmp/cctv-size-check
truncate -s 2147483648 /tmp/cctv-size-check/archive_2026-10-29-14.mp4
truncate -s 52428800 /tmp/cctv-size-check/archive_2026-10-29-15.mp4
truncate -s 52428800 /tmp/cctv-size-check/archive_2026-10-28-03.mp4
ARCHIVE_PATH=/tmp/cctv-size-check .venv/bin/python -m uvicorn web:app --port 8082 &
```

Check: `curl -s http://127.0.0.1:8082/api/files | python3 -m json.tool` returns 3 entries with sizes. Then in a browser (human, after review): headers show `2026-10-29 — 2.0 GB · 2 files` and `2026-10-28 — 50.0 MB · 1 file`; deep-link, LIVE, filter unchanged.

Stop the server and `rm -rf /tmp/cctv-size-check` when done.

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat(web): day headers show total size and file count"
```
