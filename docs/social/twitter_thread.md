# Twitter/X Thread — Moreau Arena

## Tweet 1 (Hook)

We built a combat arena to benchmark LLM strategic reasoning.

Result: with vague rules, every frontier model lost to a 50-line heuristic bot. With exact formulas + feedback, LLMs crushed them 89.75% of the time.

The benchmark isn't broken — the scaffolding is.

## Tweet 2 (Setup)

How it works:

Pick 1 of 6 animals. Allocate 20 stat points across HP/ATK/SPD/WIL (min 1 each). Fight on an 8x8 grid for up to 60 ticks.

Simple rules, deep strategy. No training data to leak. Pure reasoning under uncertainty.

## Tweet 3 (Key finding)

The dominant build? Bear with 14 ATK. 78% win rate across 887 uses.

Why: each ATK point deals ~51 dmg over 60 ticks. Each HP point absorbs 10. The math is 5:1 in favor of ATK.

Most models figured this out — when given the formulas. Without them, they fell into the "WIL trap."

## Tweet 4 (Challenge)

Can YOUR model beat the arena?

```
pip install -r requirements.txt
python run_challenge.py --provider openai --model your-model --protocol t002
```

One command. Full round-robin against 13 agents. Bradley-Terry ranking included.

## Tweet 5 (Links)

Paper + data + code — everything is open:

GitHub: https://github.com/supervitek/moreau-arena-paper

13 agents. 1559 best-of-7 series. 7667 games. All match records, prompts, and analysis scripts included.

The arena is open.
