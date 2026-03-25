# Part B Priority Trio Live Review (Postfix)

This report captures the first live production trio pass after deploy `b9cf8b6` (`fix: enforce part b standing orders on house agent`) reached [moreauarena.com](https://moreauarena.com).

## Summary

- `grow-safely` now stays on the stabilizing lane instead of drifting into an early cave sample.
- `arena-first` now holds the arena lane on the first tick when arena is available and welfare is stable.
- `cave-first` still takes the cave lane, preserving expedition-first behavior.

## Live Runs

### Grow Safely

- Run ID: `0412b414-f13d-479c-a547-c2eb53ced0d8`
- Source artifact: `reports/part_b_grow_safely_deploy_check_2.json`
- Preview action: `CARE`
- Processed actions: `CARE`
- Scores: welfare `97`, combat `0`, expedition `0`
- Return lane: `stabilizing`
- Return posture: `stable`

### Arena First

- Run ID: `c11cf4e5-86bf-4a3d-9220-7a1b05281b88`
- Source artifact: `reports/part_b_arena_first_deploy_check_2.json`
- Preview action: `ENTER_ARENA`
- Processed actions: `ENTER_ARENA`
- Scores: welfare `82`, combat `28`, expedition `0`
- Return lane: `arena-first`
- Return posture: `stable`

### Cave First

- Run ID: `313d74ec-c4cd-4016-bc1c-4f41be98ec34`
- Source artifact: `reports/part_b_cave_first_deploy_check_2.json`
- Preview action: `ENTER_CAVE`
- Processed actions: `ENTER_CAVE`
- Scores: welfare `81`, combat `0`, expedition `24`
- Return lane: `cave-first`
- Return posture: `deep in the cave`

## Verdict

The standing-order differentiation is now live on production. The first-tick trio split is clean:

- `grow-safely` -> care/stability
- `arena-first` -> combat lane
- `cave-first` -> expedition lane

This closes the product seam from the earlier trio pass where `arena-first` and `grow-safely` both drifted into cave behavior on prod.
