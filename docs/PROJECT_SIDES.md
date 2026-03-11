# Moreau Arena — Two Sides of One Coin

## Side A: "The Benchmark" (Science)
Purpose: LLM evaluation, papers, tournaments, reproducibility
Audience: Researchers, ML community
Files: data/, docs/ (paper-related), prompts/, morpeton/, season1/, run_*.py
Pages: /, /tournaments, /leaderboard, /methodology, /match-log, /compare, /paper, /about, /api-docs
Rule: Changes here must preserve tournament integrity. Never modify frozen data.

## Side B: "The Island" (Game)
Purpose: Virtual pets, mutations, fights, lore, social, engagement
Audience: Gamers, casual players
Files: pets/, season1/FIGHTER_LORE.md, web/static/pets/, web/static/fighters/, web/static/moreddit.html
Pages: /pets/*, /fighters/*, /moreddit, /s1-fighters, /s1-matchups
Rule: Creative freedom. Can break and rebuild. localStorage, no auth yet.

## Shared
- season1/engine_s1.py — combat engine (both sides use it)
- season1/animals_s1.py — animal definitions
- web/app.py — serves both (routes clearly separated)
- Navigation — both sides visible to all users

## Working Rule
- "Есть токены — строим Island. Мало токенов — полируем Benchmark."
- Side A задания: prefix "BENCHMARK:"
- Side B задания: prefix "ISLAND:"
