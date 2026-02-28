# Moreau Arena — Web UI

A simple FastAPI web interface for the Moreau Arena creature combat simulator.

## Setup

Install dependencies (from repo root):

```bash
pip install fastapi uvicorn
```

## Run

From the repo root:

```bash
uvicorn web.app:app --reload --port 8000
```

Or from the `web/` directory:

```bash
cd web
uvicorn app:app --reload --port 8000
```

## Endpoints

| Method | Path           | Description                              |
|--------|----------------|------------------------------------------|
| GET    | `/`            | HTML page with fight simulator form      |
| POST   | `/fight`       | Run N games between two builds           |
| GET    | `/leaderboard` | Aggregated agent win/loss from results/  |

### POST /fight

Request body:
```json
{
  "build1": "bear 8 10 1 1",
  "build2": "buffalo 8 6 4 2",
  "games": 100
}
```

Response:
```json
{
  "build1_wins": 72,
  "build2_wins": 28,
  "draws": 0,
  "avg_ticks": 18.5
}
```

Build format: `animal hp atk spd wil` where stats sum to 20 and each >= 1.

Valid animals: bear, buffalo, boar, tiger, wolf, monkey, crocodile, eagle, snake, raven, shark, owl, fox, scorpion.

### GET /leaderboard

Returns JSON array of agents sorted by win rate, aggregated from `results/*.jsonl` files.
