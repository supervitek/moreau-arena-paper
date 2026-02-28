# Contributing -- Add Your Own Model to Moreau Arena

This guide explains how to implement a new agent, run it against the existing roster, and submit your results.

## Agent Interface

All agents extend the `BaseAgent` abstract class. The only method you need to implement is `choose_build`.

### The Build Class

```python
from agents.base import Build, Animal

build = Build(
    animal=Animal.BEAR,
    hp=3,
    atk=14,
    spd=2,
    wil=1,
)
```

**Constraints:**
- `hp + atk + spd + wil` must equal exactly **20**.
- Each stat must be at least **1**.
- `animal` must be one of: `BEAR`, `BUFFALO`, `BOAR`, `TIGER`, `WOLF`, `MONKEY`.

### The BaseAgent Class

```python
from agents.base import BaseAgent, Build, Animal
from typing import Optional

class BaseAgent:
    """Abstract base class for all agents."""

    def choose_build(
        self,
        opponent_animal: Optional[Animal],
        banned: list[Animal],
        opponent_reveal: Optional[Build],
    ) -> Build:
        """
        Choose a build for the next game.

        Args:
            opponent_animal: The opponent's animal from the previous game,
                             or None if this is game 1.
            banned: List of animals that are banned this series (usually empty).
            opponent_reveal: The opponent's full build from the previous game,
                             revealed only if you lost. None if you won or
                             if this is game 1.

        Returns:
            A Build instance with animal and stat allocation.
        """
        raise NotImplementedError
```

### Minimal Example

A complete agent in 10 lines:

```python
from agents.base import BaseAgent, Build, Animal

class MyAgent(BaseAgent):
    """Always picks Bear with max ATK."""

    name = "MyAgent"

    def choose_build(self, opponent_animal, banned, opponent_reveal):
        return Build(animal=Animal.BEAR, hp=3, atk=14, spd=2, wil=1)
```

This is a valid agent. It ignores adaptation entirely and always picks the T002 meta build. You can use it as a starting point and add logic from there.

### Adaptive Agent Example

An agent that adapts based on what it lost to:

```python
from agents.base import BaseAgent, Build, Animal

class AdaptiveAgent(BaseAgent):
    """Switches to a counter-build when it loses."""

    name = "AdaptiveAgent"

    def choose_build(self, opponent_animal, banned, opponent_reveal):
        if opponent_reveal is None:
            # Game 1 or we won last game -- use default
            return Build(animal=Animal.BEAR, hp=8, atk=10, spd=1, wil=1)

        # Lost last game -- try to counter
        if opponent_reveal.atk >= 12:
            # Counter ATK-heavy with high HP + dodge
            return Build(animal=Animal.TIGER, hp=8, atk=5, spd=6, wil=1)
        else:
            # Counter tanky builds with max damage
            return Build(animal=Animal.BEAR, hp=3, atk=14, spd=2, wil=1)
```

### LLM Agent Example

If you want to plug in an LLM, look at `agents/llm_agent_v2.py` for the full implementation. The key pattern is:

1. Build a prompt with game rules, exact formulas, and meta context.
2. Call the LLM API with structured output (JSON schema for the build).
3. Parse and validate the response into a `Build` object.

The `api_call` function is injectable, so you can swap providers without changing agent logic.

## Running Your Agent

### Challenge Mode

The simplest way to test your agent is challenge mode, which runs your agent against all 13 agents from the tournament.

1. Add your agent class to `agents/`.
2. Modify `run_challenge.py` to import and use your agent.
3. Run:

```bash
python run_challenge.py --provider anthropic --model claude-sonnet-4-5 --protocol t002
```

For non-LLM agents, you can call the challenge runner directly from Python:

```python
from run_challenge import run_challenge
from agents.my_agent import MyAgent

results = run_challenge(agent=MyAgent(), series_count=7)
print(results)
```

### Lab Mode

Lab mode runs your agent in an interactive loop where you can observe each round's reasoning and build choices:

```bash
python lab_mode.py --provider openai --model gpt-4o --rounds 10
```

## Submitting Results

If you run a full challenge with your agent, we welcome your results:

1. Run your agent through the full challenge suite.
2. Collect the output JSONL file (automatically saved to `data/`).
3. Open a GitHub issue at [moreau-arena-paper](https://github.com/supervitek/moreau-arena-paper/issues) with:
   - Agent name and description.
   - Model/provider used (if LLM-based).
   - The JSONL results file attached.
   - Any observations about your agent's adaptation behavior.

We will review and may include notable results in future analysis.

## Game Rules Reference

For complete stat formulas, animal abilities, proc rates, and ring mechanics, see [MECHANICS.md](MECHANICS.md).

Key formulas for quick reference:

| Stat | Formula |
|------|---------|
| Max HP | `50 + 10 * HP` |
| Base Damage | `floor(2 + 0.85 * ATK)` |
| Dodge | `max(0%, min(30%, 2.5% * (SPD - 1)))` |
| Resist | `min(60%, WIL * 3.3%)` |
| Proc Bonus | `WIL * 0.08%` (additive) |
