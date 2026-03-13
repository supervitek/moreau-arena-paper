# Codex Audit Report — Side B
**Date:** March 13, 2026
**Files scanned:** 48
**Auditor:** Codex

## Summary
- Critical: 5
- Warning: 12
- Info: 5

## Critical Issues
- `web/static/island/train.html:924`, `web/static/island/pit.html:965`, `web/static/island/rivals.html:1733`, `web/static/island/deep-tide.html:1812`, `web/static/island/prophecy.html:1751`, `web/static/island/oath.html:1450`, `web/static/pets/train.html:602`, `web/static/pets/pvp.html:788`  
  What’s wrong: all of these pages `fetch('/api/v1/fight/s1')`, but `web/app.py:1510` only exposes `POST /fight/s1`. The audited frontend combat flows will 404 instead of running fights.  
  Suggested fix: either add a `/api/v1/fight/s1` alias in `web/app.py` or change every caller to `/fight/s1`.

- `web/static/island/home.html:2117`, `web/static/island/train.html:725`, `web/app.py:1410-1416`  
  What’s wrong: island UI links users to `/island/mutate`, but the island route whitelist has no `mutate` page. This is a hard 404 from the main dashboard and post-fight mutation CTA.  
  Suggested fix: point these links to `/island/lab`, or add a real `/island/mutate` page and whitelist it.

- `web/static/island/kennel.html:634`, `web/static/island/kennel.html:640`, `web/static/island/kennel.html:677`, `web/static/island/kennel.html:684`, `web/static/island/kennel.html:844`  
  What’s wrong: kennel uses `island_active_pet_id`, while the rest of Side B uses `moreau_active_pet`. Selecting a pet in kennel does not update the active pet state used by `home.html`, `train.html`, `pit.html`, `arena.html`, and the pets pages.  
  Suggested fix: standardize on `moreau_active_pet` everywhere, or add an explicit bridge layer that keeps both keys in sync.

- `web/static/pets/forbidden-lab.html:1950`, `web/static/pets/forbidden-lab.html:2501-2514`, `web/static/pets/forbidden-lab.html:2591`  
  What’s wrong: Bible §22/§23 says `instability >= 100 -> deceased = true`. The lab caps instability at 100, then applies a probabilistic death roll; a pet can survive at 100 instability.  
  Suggested fix: short-circuit the roll. If instability reaches 100, mark the pet deceased immediately and persist that state.

- `web/static/island/black-market.html:1439`, `web/static/island/black-market.html:1507`, `web/static/island/black-market.html:1537`, `web/static/island/black-market.html:1558`, `web/static/island/black-market.html:1510`, `web/static/island/black-market.html:1551-1552`  
  What’s wrong: Black Market still writes to legacy `pet.stats` when `base_stats` is absent, and it can increase `instability` / `corruption` without enforcing the canonical threshold effects (`deceased`, `is_tainted`). This can leave the stored pet model internally inconsistent.  
  Suggested fix: write only `pet.base_stats`, migrate any legacy pets once, and apply threshold enforcement after every instability/corruption mutation.

## Warnings
- `web/static/island/onboarding.html:264`, `web/static/island/home.html:1616`  
  What’s wrong: onboarding state is stored under `moreau_onboarding_complete`, but Bible §19 defines `moreau_onboarded`. The code is internally consistent here, but it has drifted from the project’s canonical key list.  
  Suggested fix: rename to `moreau_onboarded` or update the bible and all readers together.

- `web/static/island/black-market.html:1597`, `web/static/island/black-market.html:1627`, `web/static/island/lab.html:706-709`  
  What’s wrong: Black Market posts are stored in `moreau_moreddit`, while the canonical feed key is `moreau_moreddit_feed`. That splits the social feed into two stores.  
  Suggested fix: use one key only, preferably `moreau_moreddit_feed`.

- `web/static/island/shrine.html:1482`, `web/static/island/prophecy.html:2026-2031`, `web/static/island/menagerie.html:1172-1175`, `web/static/island/menagerie.html:1561`, `web/static/island/menagerie.html:1850-1854`, `web/static/island/menagerie.html:2112`, `web/static/island/achievements.html:369-389`  
  What’s wrong: multiple pages unlock achievement IDs that do not exist in the canonical `ACHIEVEMENTS` object: `artifact_hunter`, `oracle_*`, `spirit_walker`, `spirit_keeper`, `immortalizer`, `spirit_bonder`, `full_circle`, `epitaph_writer`. These achievements can be written to storage but will not render in the logbook.  
  Suggested fix: add these IDs to `ACHIEVEMENTS`, or stop writing undocumented IDs.

- `web/static/pets/profile.html:742-812`, `web/static/pets/profile.html:876-883`, `pets/mutation_tree.py:42-193`  
  What’s wrong: the profile dossier ships its own mutation tree with different IDs and different stat deltas than the canonical Python tree. Example: profile uses `bloodrage` / `berserker_mode` and inflated stat changes; canonical data uses `blood_rage` / `berserker`. Dossier math can therefore display incorrect “base vs mutation bonus” numbers.  
  Suggested fix: derive this UI from the canonical mutation definitions instead of maintaining a second hand-written tree.

- `web/static/island/pit.html:773`, `web/static/island/pit.html:1054-1057`, `web/static/island/rivals.html:1877-1885`, `web/static/island/train.html:773`, `web/static/pets/train.html:522`  
  What’s wrong: XP awards are not consistent. Training uses the canonical win=30 / loss=10, but Pit uses winner-only `XP_SPAR = 15`, and Rivals adds an extra `bonusXP = 50` on defeat of a rival.  
  Suggested fix: decide whether Pit and Rivals are intentionally special. If not, normalize them to the mutation tree constants.

- `web/static/island/kennel.html:612`, `web/static/island/kennel.html:705-706`, `pets/mutation_tree.py:26-30`  
  What’s wrong: kennel displays progress using `XP_PER_LEVEL = [0,100,250,500,...]`, while the canonical thresholds are `{2:50,3:100,4:150,5:200,6:300,...}`. The kennel XP bar is therefore out of sync with real leveling.  
  Suggested fix: replace the hard-coded kennel table with the canonical thresholds.

- `web/static/island/home.html:1901`, `web/static/pets/home.html:855`, `web/static/pets/train.html:590`, `web/static/island/pit.html:856`, `web/static/island/train.html:912`, `web/static/island/dreams-engine.js:193`, `web/static/island/m-engine.js:173`  
  What’s wrong: Side B still has widespread `pet.base_stats || pet.stats` fallbacks. Bible §22 explicitly says `pet.base_stats`, never `pet.stats`. These fallbacks can hide data drift and let legacy fields survive indefinitely.  
  Suggested fix: migrate old pets once, then remove every `pet.stats` fallback from island/pets code.

- `web/static/island/crimson.html:870`  
  What’s wrong: Crimson uses `var stats = pet.stats || {};` for amplified display stats. Unlike most other pages, there is no `base_stats` fallback here, so base-stats-only pets show incorrect numbers.  
  Suggested fix: read `pet.base_stats` only.

- `web/static/island/home.html:1617`, `web/static/island/home.html:1683`, `web/static/island/home.html:1934`, `web/static/pets/index.html:456`, `web/static/pets/index.html:629`, `web/static/pets/forbidden-lab.html:1913`, `web/static/pets/forbidden-lab.html:1921`  
  What’s wrong: there are many `JSON.parse(localStorage.getItem(...))` calls without `try/catch`. A single malformed localStorage value can take down the whole page during init.  
  Suggested fix: wrap all localStorage parses in `try/catch` and fall back to safe defaults.

- `web/static/pets/hub.html:455`, `web/static/pets/home.html:1000-1007`, `web/static/pets/train.html:767-780`, `web/static/pets/pvp.html:955-965`, `web/static/island/deep-tide.html:1637`  
  What’s wrong: user-controlled pet names are interpolated into `innerHTML` without escaping. A crafted pet name can inject markup into the page.  
  Suggested fix: use `textContent` or escape names before concatenating HTML.

- `web/static/island/menagerie.html:1566`, `web/static/island/menagerie.html:1859`, `web/static/island/shrine.html:1490`, `web/static/island/dreams-engine.js:170-223`  
  What’s wrong: `generateDream()` is called with unsupported dream types (`spirit_immortalized`, `spirit_bonded`, `discovery`). The engine silently returns because those keys are missing from `DREAM_LIBRARY`; `spirit_bonded` also passes a non-pet object shape.  
  Suggested fix: add the missing dream templates and keep the function signature `generateDream(type, pet, extra)`.

- `web/static/island/cosmetics.html:622-623`, `web/static/island/cosmetics.html:629`, `web/static/island/synergies.html:575-576`, `web/static/island/synergies.html:582`, `web/app.py:1231-1327`  
  What’s wrong: cosmetics/synergies nav still points to nonexistent benchmark routes `/matchups`, `/cycles`, and `/s1`. Those 404 in the current FastAPI route table.  
  Suggested fix: replace them with the existing routes or remove the dead links.

- `web/static/island/home.html:2701-2704`, `web/static/island/train.html:1622-1625`, `web/static/island/pit.html:1696-1699`, `web/static/island/graveyard.html:606-609`  
  What’s wrong: several pages write achievements directly into `moreau_achievements` instead of using the canonical logbook utility. This is why Side B can accumulate undocumented IDs and mixed payload shapes (`date` vs `timestamp`).  
  Suggested fix: centralize achievement writes through one shared helper and enforce one record shape.

## Info / Style
- `web/app.py:1345-1353`  
  Verified clean: `GET /api/v1/island/config` returns `configured: bool(url and key)`, so missing env vars correctly produce `configured: false`.

- `pets/soul.py:151-168`, `web/app.py:1436-1445`  
  Verified clean: `POST /api/v1/pets/soul` handles missing `ANTHROPIC_API_KEY` gracefully by returning the fallback soul text instead of throwing.

- `web/app.py:1397-1402`  
  Verified clean: `POST /api/v1/island/arena-fight` transforms pet data into the required `"animal hp atk spd wil"` string format before calling the S1 engine.

- `web/static/island/home.html:1735-1736`, `web/static/island/home.html:2224`, `web/static/island/home.html:2258-2265`, `web/static/island/home.html:2571-2686`  
  Verified clean: hub integration uses `typeof` guards before touching `TideEngine`, `ConfessionEngine`, and `MEngine`, and `MEngine.process()` is called on home load.

- `web/static/island`, `web/static/pets`, `web/app.py:1339-1445`  
  Side A contamination check: no audited island/pets frontend code writes to `config.json`, `data/tournament_*`, or benchmark artifacts. No Side B route in the audited block mutates frozen tournament data.

## Files Verified Clean
- `pets/mutation_tree.py`
- `pets/soul.py`
- `web/static/island/confessions.html`
- `web/static/island/index.html`
