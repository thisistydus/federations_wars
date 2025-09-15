# Changelog — Federation Wars

## v0.3.0 — Modularization & Multipage UI
**Date:** 2025-09-14

### ✨ New
- **Repo restructure for scale**
  - Introduced `fw/` Python package for core logic (no Streamlit deps):
    - `fw/db.py` — state, seed data, CRUD, save/load JSON
    - `fw/sim/booking.py` — card builder (intergender/tag/trios rules)
    - `fw/sim/engine.py` — match runner & show flow
    - `fw/models.py` — basic enums/constants
    - `fw/util/ids.py` — id/slug helpers
    - `fw/logic/universe.py` — time skip & weekly scheduling
  - Streamlit **multipage** app under `pages/`:
    - `1_Dashboard.py`, `2_Federations.py`, `3_Workers.py`, `4_Shows.py`, `5_News.py`
  - **`app.py`** is now a lightweight launcher (sidebar, save/load, ticker strip).

- **Save/Load (JSON) preserved** across the new layout:
  - Download current universe as `universe.json`
  - Upload the same file to restore the exact state

### 🔧 Changes
- Moved all non-UI logic out of Streamlit files to enable easier testing & future features (titles, promos, economy, etc.).
- Seeding logic centralized in `fw/db.py::seed_demo()`; easier to expand demo workers/feds.
- Page code slimmed and now calls into `fw` modules (cleaner diffs going forward).

### 🧨 Breaking changes
- **Imports changed**: any custom code referencing functions directly from the old single-file `app.py` must now import from the appropriate `fw.*` module.
- If you had local edits inside the old `app.py`, those need to be re-applied in the new module locations.

### ✅ Migration notes
- Pull the new tree, then run as usual: `streamlit run app.py`.
- Use **Seed Demo Data** to start fresh, or **Load JSON** to continue a previous save.
- To add more demo content, edit `fw/db.py::seed_demo()` (workers, feds, employment, shows).

### 🧪 Smoke test checklist
1. **Seed Demo Data** → app boots with 3 feds, 12 workers, week 1 shows.
2. **Auto-book / Run Card** → cards generate respecting intergender/tag/trios; results appear with recaps.
3. **Run All Cards (This Week)** → completes remaining shows; News shows items.
4. **Save / Load** → download JSON, reload app, upload JSON → state restored.
5. **Skip Time** → week increments; next week’s shows auto-scheduled.

### 📌 Next (road to MVP)
- **Bigger Seed Pack**: 40–60 workers, 6–8 feds (TEW-style content pack).
- **Titles & Lineage**: per-fed belts, champions, title matches in recaps, lineage views.
- **Match Engine v0.1**: finishers, flavor spots, basic injuries/fatigue.
- **Promo Engine (stub)**: persona/gimmick-driven promos to News.
- **Detail Views & Links**: worker/fed/show/title pages with cross-linking.

---

## v0.2.0 — Federation Rules, Gender, and Masks
**Date:** 2025-09-13

### ✨ New
- Worker **gender** (`male|female|nonbinary`).
- Federation rules: `allow_intergender`, `allow_tag` (2v2), `allow_trios` (3v3).
- **Masked** persona per-employment (e.g., masked in Lucha).
- Team-aware **card builder** & **simulator** (MMA singles-only).
- UI updates across Federations/Workers/Shows; mask indicator (🎭).

### 🔧 Changes
- `create_fed(...)`, `create_worker(...)`, and `employ_worker(...)` signatures extended.
- `ensure_card(...)` and `run_match(...)` updated for teams.

### 🧨 Breaking
- Old function call shapes required updates; fixed via UI or by passing new args.

