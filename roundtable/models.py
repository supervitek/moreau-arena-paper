"""Data models for Round Table council sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Response:
    """A panelist's response to the council question."""
    model: str
    provider: str
    text: str
    elapsed_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None


@dataclass
class Critique:
    """A panelist's critique of all other responses."""
    model: str
    provider: str
    text: str
    elapsed_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None


@dataclass
class SynthesisPoint:
    """A single point in the moderator's synthesis."""
    point: str
    support: str  # which panelists support this
    dissent: str  # who disagrees and why


@dataclass
class Synthesis:
    """The moderator's synthesis of all responses and critiques."""
    model: str
    text: str
    points: list[SynthesisPoint] = field(default_factory=list)
    elapsed_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class Vote:
    """A panelist's vote on each synthesis point."""
    model: str
    provider: str
    votes: list[dict[str, str]] = field(default_factory=list)
    # Each dict: {"point": "...", "vote": "agree|disagree|abstain", "reason": "..."}
    elapsed_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None


@dataclass
class CouncilSession:
    """Complete record of a Round Table council session."""
    question: str
    moderator: str
    panelists: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    responses: list[Response] = field(default_factory=list)
    critiques: list[Critique] = field(default_factory=list)
    synthesis: Synthesis | None = None
    votes: list[Vote] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_elapsed_s: float = 0.0

    def compute_totals(self) -> None:
        self.total_cost_usd = (
            sum(r.cost_usd for r in self.responses)
            + sum(c.cost_usd for c in self.critiques)
            + (self.synthesis.cost_usd if self.synthesis else 0.0)
            + sum(v.cost_usd for v in self.votes)
        )

    def cost_by_model(self) -> dict[str, float]:
        costs: dict[str, float] = {}
        for r in self.responses:
            costs[r.model] = costs.get(r.model, 0.0) + r.cost_usd
        for c in self.critiques:
            costs[c.model] = costs.get(c.model, 0.0) + c.cost_usd
        if self.synthesis:
            costs[self.synthesis.model] = costs.get(self.synthesis.model, 0.0) + self.synthesis.cost_usd
        for v in self.votes:
            costs[v.model] = costs.get(v.model, 0.0) + v.cost_usd
        return costs

    def to_dict(self) -> dict[str, Any]:
        self.compute_totals()
        return {
            "question": self.question,
            "moderator": self.moderator,
            "panelists": self.panelists,
            "timestamp": self.timestamp,
            "responses": [
                {
                    "model": r.model, "provider": r.provider,
                    "text": r.text, "elapsed_s": round(r.elapsed_s, 2),
                    "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
                    "cost_usd": round(r.cost_usd, 4),
                    **({"error": r.error} if r.error else {}),
                }
                for r in self.responses
            ],
            "critiques": [
                {
                    "model": c.model, "provider": c.provider,
                    "text": c.text, "elapsed_s": round(c.elapsed_s, 2),
                    "input_tokens": c.input_tokens, "output_tokens": c.output_tokens,
                    "cost_usd": round(c.cost_usd, 4),
                    **({"error": c.error} if c.error else {}),
                }
                for c in self.critiques
            ],
            "synthesis": {
                "model": self.synthesis.model,
                "text": self.synthesis.text,
                "points": [
                    {"point": p.point, "support": p.support, "dissent": p.dissent}
                    for p in self.synthesis.points
                ],
                "elapsed_s": round(self.synthesis.elapsed_s, 2),
                "input_tokens": self.synthesis.input_tokens,
                "output_tokens": self.synthesis.output_tokens,
                "cost_usd": round(self.synthesis.cost_usd, 4),
            } if self.synthesis else None,
            "votes": [
                {
                    "model": v.model, "provider": v.provider,
                    "votes": v.votes, "elapsed_s": round(v.elapsed_s, 2),
                    "input_tokens": v.input_tokens, "output_tokens": v.output_tokens,
                    "cost_usd": round(v.cost_usd, 4),
                    **({"error": v.error} if v.error else {}),
                }
                for v in self.votes
            ],
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cost_by_model": {k: round(v, 4) for k, v in self.cost_by_model().items()},
        }
