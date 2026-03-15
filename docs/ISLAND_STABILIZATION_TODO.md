# Island Stabilization Pass

- [x] Extract island time tracking into a shared helper.
- [x] Harden genesis/succession and adjacent state contracts.
- [x] Normalize dream / confession / M-related storage contracts.
- [x] Add browser-style smoke coverage for core island flows.
- [x] Close remaining high-value hotspot pages and storage crash points.
- [x] Extract shared island UI/helpers where it reduces duplication safely.
- [x] Finish one end-to-end stabilization pass with verification and push.

## Notes

- Shared helpers added:
  - `web/static/island/storage.js`
  - `web/static/island/island-time.js`
  - `web/static/island/ui.js`
- Core verification:
  - `python3 -m pytest -q`
  - `python3 scripts/smoke_web.py`
  - `python3 scripts/smoke_island.py`
