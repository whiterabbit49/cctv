# CCTV Web Viewer Design — 2026-10-16

## Goal
Add a simple web interface to the CCTV archiver (`~/work.personal/cctv`):
show live feed and list of video files. When no file is selected, play live.
When an `.mp4` is selected, play it.

## Context (existing)
- `app.py`: RTSP → HLS 10s `.ts` segments per hour (`YYYY-MM-DD-HH_segment_%05d.ts` + `playlist_YYYY-MM-DD-HH.m3u8`) → hourly consolidation to `archive_YYYY-MM-DD-HH.mp4` (libx264 veryfast, CRF 26) → retention 90 days, purge orphans.
- `Dockerfile`: `jrottenberg/ffmpeg:5.1-alpine` + `python3`, entrypoint `python3 -u app.py`. No web code.
- `k8s/deployment.yaml`: single pod `cctv-archiver`, ns `cctv`, PVC `cctv-archive-pvc` 500Gi RWO at `/archive`, env `RTSP_URL` (secret), `ARCHIVE_PATH=/archive`, `RETENTION_DAYS=90`.
- Browsers cannot play RTSP (user wrote RSTP = RTSP). Live must be HLS.

## Decisions (from brainstorming)
- Live = current hour's HLS playlist, played via hls.js (reuses 10s `.ts` segments, 10–30s delay acceptable).
- File list = flat + date filter (Option B), LIVE entry pinned on top.
- Stack = FastAPI embedded, Option 1 (same container/pod, :8080).
- Auth = shared token (`CCTV_TOKEN`, `?token=` or `X-CCTV-Token` header).
- Layout = top player + flat list below (simplest, mobile-friendly).
- URL state = query params + `history.replaceState` (Option A): `?file=<mp4 name>&t=<seconds>`; live updates, no history spam.

## URL deep-linking (playback state)
Player state lives in the URL so a copied link restores the exact spot:

- **Format:** `?file=archive_YYYY-MM-DD-HH.mp4&t=<seconds>` → play that mp4 at position `t` (`t` omitted = 0). Empty/no params = LIVE. Server side unchanged — this is purely frontend.
- **Update behavior:** `timeupdate` listener writes `t` via `history.replaceState`, throttled to one write per 3s. Also writes immediately on `seeked` and `pause`. Selecting a row updates `file` immediately (`replaceState`, not push — one history entry per session). Clicking 🔴 LIVE clears params (clean URL, no params = live).
- **Restore on load:** parse params → if `file` present, set the date input from the filename prefix (so the list shows the row), fetch `/api/files`, highlight the matching row, play it, and on `loadedmetadata` set `v.currentTime = t`. Live mode ignores `t`.
- **Edge cases:** unknown `file` (deleted by retention, typo) → fetch returns no row → fall back to LIVE and clear the URL. Non-numeric/negative `t` → clamp to 0; `t` beyond duration clamps naturally via `currentTime`. LIVE hour-rollover polling unchanged (live has no URL state).

## Architecture
Same container, two threads. Recorder loop untouched. FastAPI + uvicorn on `:8080` in daemon thread started from `app.py`.
Shares `ARCHIVE_PATH` on disk. Dockerfile adds `py3-pip` + `pip install fastapi uvicorn`.
k8s adds `CCTV_TOKEN` secret env + `containerPort: 8080` (+ Service). No PVC change (RWO stays).

## Components / API
- `GET /` → `index.html` (single file, no build, vanilla JS + hls.js CDN). Top `<video>`, date `<input type=date>` + flat list below.
- `GET /api/live` → `{ playlist_url: "/hls/playlist_YYYY-MM-DD-HH.m3u8", hour: "YYYY-MM-DD-HH" }`. 404 if playlist not yet written (startup).
- `GET /api/files?date=YYYY-MM-DD` → `[{ name, hour, size, mtime }]` for `archive_*.mp4`, newest-first, optional date filter parsed from filename. LIVE row is frontend-hardcoded.
- `GET /hls/{file}` → `.m3u8` as `application/vnd.apple.mpegurl`, `.ts` as `video/mp2t`. Basename-guarded against traversal, only current-hour files + allowlisted extensions.
- `GET /video/{name}` → `FileResponse` with Range support for seeking mp4.
- Auth middleware: compare query/header token to `CCTV_TOKEN` env; empty env = open (local dev). Frontend stores token in `localStorage`, simple prompt box on 401.

## Data flow / playback rules
1. Load with no selection → `GET /api/live` → hls.js loads playlist → autoplay (muted fallback for autoplay policy).
2. Click mp4 → destroy hls instance, `<video src=/video/archive_....mp4>` native playback.
3. Click 🔴 LIVE → destroy mp4 src, re-init hls.js with fresh `/api/live`.
4. Poll `/api/live` every 60s while in LIVE mode; on hour change reload playlist. While in MP4 mode, show "LIVE moved to HH" badge without interrupting.
5. List refresh every 60s + on date filter change.
6. Player ↔ URL sync per "URL deep-linking" above: selecting a video or seeking updates `?file=...&t=...`; loading with those params restores the same spot.

## Error handling
- No playlist yet → 404 + frontend "waiting for live…" retry 5s.
- MP4 deleted by retention between list and play → 404, row greys out on next refresh.
- Bad token → 401 JSON, frontend prompts.
- HLS rollover race (playlist swapped mid-read) → hls.js error handler retries `/api/live`.

## Testing
Extend `test_app.py`: files sorting newest-first + date filter, `/api/live` hour format `YYYY-MM-DD-HH`, auth 401/200 via header + query, HLS mime types, traversal rejection (`../`), mp4 404.
URL deep-linking is frontend-only (no server change): manual checks — copy URL mid-playback, open in fresh tab, playback lands at the same file/position; bad `file` param → LIVE fallback; LIVE click → clean URL.

## Out of scope (v1)
Thumbnails, multi-camera, user accounts, low-latency (<5s) WebRTC, RWX split deployment, download zip.

## Files to change
- `app.py` (or new `web.py` imported): FastAPI app + thread starter.
- `index.html` (new, served as static): UI.
- `Dockerfile`: pip deps.
- `k8s/deployment.yaml` (+ `service.yaml` new): port 8080, `CCTV_TOKEN`.
- `test_app.py`: web tests.
- `README.md`: `CCTV_TOKEN`, port-forward usage.
