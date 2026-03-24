# Part B Priority Trio Live Review

- Base URL: `https://moreauarena.com`
- Profiles tested: `grow-safely`, `arena-first`, `cave-first`

## Results

### grow-safely

- Run ID: `4958316a-1595-4e1a-acdd-91d0adce994c`
- Risk appetite: `guarded`
- Preview action: `ENTER_CAVE`
- Processed actions: `ENTER_CAVE, EXTRACT, ENTER_CAVE, EXTRACT`
- Primary lane: `cave-first`
- Scores: welfare `73`, combat `0`, expedition `41`
- Return headline: They pushed into the cave and came back changed.
- Return summary: 4 ticks since departure; 2x enter_cave, 2x extract.

### arena-first

- Run ID: `37393f94-9b4d-4f89-9fc1-d668366b50ba`
- Risk appetite: `bold`
- Preview action: `ENTER_CAVE`
- Processed actions: `ENTER_CAVE, EXTRACT, ENTER_CAVE, EXTRACT`
- Primary lane: `cave-first`
- Scores: welfare `73`, combat `0`, expedition `55`
- Return headline: They pushed into the cave and came back changed.
- Return summary: 4 ticks since departure; 2x enter_cave, 2x extract.

### cave-first

- Run ID: `f411cf0b-dbe6-4223-99b7-05cda963d1c0`
- Risk appetite: `bold`
- Preview action: `ENTER_CAVE`
- Processed actions: `ENTER_CAVE, EXTRACT, ENTER_CAVE, EXTRACT`
- Primary lane: `cave-first`
- Scores: welfare `73`, combat `0`, expedition `48`
- Return headline: They pushed into the cave and came back changed.
- Return summary: 4 ticks since departure; 2x enter_cave, 2x extract.

## Verdict

- All three runs used the live Gemini model path.
- All three watches completed cleanly and returned a valid return report.
- `grow-safely` and `arena-first` did not yet separate on production; both previewed and executed cave-led behavior.
- `cave-first` still behaves as expected, but the trio as a whole shows that standing-order differentiation is not yet strong enough on live model behavior.
