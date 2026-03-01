# I built a combat arena benchmark — can your local model beat GPT-4o?

Hey everyone,

I built a strategy game benchmark called **Moreau Arena** where LLMs pick an animal, allocate stats, and fight 1v1 on a grid. The twist: we tested 8 frontier models and 5 hand-coded bots across 1559 best-of-7 series (7667 total games), and the results are wild.

## The game in 30 seconds

- Pick 1 of 6 animals (bear, buffalo, boar, tiger, wolf, monkey)
- Distribute 20 points across HP, ATK, SPD, WIL (min 1 each)
- Your creature fights on an 8x8 grid for up to 60 ticks
- A shrinking ring prevents stalling
- Best-of-7 series, loser sees the winner's build and can adapt

That's it. No GPU needed for the benchmark itself — it's a local Python simulator. Your model just needs to output a JSON build choice.

## What happened

**Round 1 (vague rules, no feedback):** Every single LLM lost to a 50-line Python heuristic. GPT-4o fell into the "WIL trap" — pouring points into willpower because it sounds important in RPGs. It's not. LLMs won only 37.5% of games against bots.

**Round 2 (exact formulas + adaptation):** We gave models the actual math and let losers see the winner's build. LLMs went from 37.5% to 89.75% win rate against bots. GPT-5.2-Codex jumped from rank 9 to rank 1.

The dominant strategy? Bear with max ATK. Each ATK point deals ~51 damage over 60 ticks. Each HP point absorbs 10. The math is brutally simple once you see it — but models needed the formulas to figure it out.

## Quick start — 3 commands

```bash
git clone https://github.com/supervitek/moreau-arena-paper
pip install -r requirements.txt

# Test with --dry-run first (no API key needed)
python run_challenge.py --dry-run --provider openai --model test --series 3

# Run for real against all 13 agents
python run_challenge.py --provider openai --model your-model --protocol t002
```

Works with any OpenAI-compatible API. Set your `OPENAI_API_BASE` and `OPENAI_API_KEY` and point it at your local server. Also supports Anthropic, Google, and xAI providers natively.

For local models behind an OpenAI-compatible server (llama.cpp, vLLM, text-generation-webui, ollama with OpenAI compat):

```bash
export OPENAI_API_KEY="not-needed"
python run_challenge.py --provider openai --model local-model-name --protocol t002
```

## Results so far

Here's the T002 leaderboard (Bradley-Terry ranking, higher = better):

| Rank | Agent | Type |
|------|-------|------|
| 1 | GPT-5.2-Codex | LLM |
| 2 | Claude 3.5 Sonnet | LLM |
| 3 | Gemini 2.5 Pro | LLM |
| ... | ... | ... |
| 9-13 | All baselines | Bot |

Every LLM outranked every bot. But within LLMs, there's a real spread. Some models find the dominant Bear build immediately. Others waste 3-4 games figuring it out.

## What makes this interesting for local models

- **No contamination.** The game is novel — no model has seen it before. This is pure reasoning, not pattern matching on training data.
- **Cheap to run.** Each series is 7 API calls max. A full round-robin is ~91 series. You can benchmark a model for pennies.
- **Strategy over size.** A smaller model that reasons well about the math could beat a larger model that falls into the WIL trap.
- **Adaptation matters.** The series format rewards models that learn from their losses. This is where local fine-tuned models might shine.

## Lab mode

Want to watch your model learn in real time?

```bash
python lab_mode.py --provider openai --model your-model --rounds 10
```

This runs an iterative loop: your model proposes builds, the simulator tests them, and the model gets feedback. You can watch it converge (or not) on the dominant strategy.

## The arena is open

Everything is MIT licensed — code, data, prompts, all 7667 match records.

GitHub: https://github.com/supervitek/moreau-arena-paper

I'd love to see how Llama 3, Mistral, Qwen, DeepSeek, and other local models perform. If you run the benchmark, post your results — I'll add them to the leaderboard.

Can your model beat the bear?
