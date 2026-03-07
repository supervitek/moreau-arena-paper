"""Core Round Table council orchestrator.

Runs 4 phases:
  1. Independent responses (parallel)
  2. Critique round (parallel)
  3. Moderator synthesis
  4. Voting (parallel)
"""

from __future__ import annotations

import random
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import IO

from .models import (
    CouncilSession,
    Critique,
    Response,
    Synthesis,
    Vote,
)
from .prompts import (
    critique_prompt,
    response_prompt,
    synthesis_prompt,
    vote_prompt,
)
from .providers import (
    MODEL_PROVIDERS,
    call_model,
    estimate_cost,
)


def _progress(msg: str, out: IO[str] = sys.stderr) -> None:
    """Print a progress message."""
    out.write(f"\r{msg}")
    out.flush()


def _dry_response(model: str) -> str:
    """Generate a fake response for --dry-run mode."""
    proposals = [
        "non-transitive cycle coverage",
        "win-rate variance under seed permutation",
        "baseline dominance threshold",
        "build diversity index",
    ]
    pick = random.choice(proposals)
    return (
        f"[DRY RUN — {model}]\n\n"
        f"I propose that the most important quality gate for Season 1 is "
        f"**{pick}**. This matters because it ensures the benchmark "
        f"measures genuine strategic reasoning rather than noise. "
        f"Without this gate, we risk publishing results that don't "
        f"replicate under different random seeds or matchup orderings."
    )


def _dry_critique(model: str) -> str:
    return (
        f"[DRY RUN — {model}]\n\n"
        f"I agree with most panelists on the importance of reproducibility. "
        f"However, I think the emphasis should be on build diversity rather "
        f"than seed variance — a benchmark where all agents converge on "
        f"the same build isn't testing strategy at all."
    )


def _dry_synthesis() -> str:
    return (
        "[DRY RUN — SYNTHESIS]\n\n"
        "## Consensus Points\n"
        "All panelists agree that reproducibility is non-negotiable.\n\n"
        "## Key Disagreements\n"
        "The panel is split between seed-variance testing and build-diversity "
        "metrics as the primary gate.\n\n"
        "## Strongest Arguments\n"
        "The argument for build diversity is compelling — a benchmark where "
        "all agents play identically fails to test strategy.\n\n"
        "## Synthesis\n"
        "Season 1 should gate on BOTH seed-variance (< 25% outcome flip) AND "
        "build-diversity (> 3 unique builds per agent). Neither alone suffices.\n\n"
        "## Propositions\n"
        "Proposition 1: Season 1 must verify < 25% win-rate variance across seeds.\n"
        "Proposition 2: Each LLM agent must produce at least 3 distinct builds.\n"
        "Proposition 3: Baseline agents should use the same 6-animal pool as LLMs.\n"
    )


def _dry_vote(model: str) -> str:
    votes = ["AGREE", "DISAGREE", "ABSTAIN"]
    return (
        f"[DRY RUN — {model}]\n\n"
        f"Proposition 1: {random.choice(votes)} — Seed variance is fundamental.\n"
        f"Proposition 2: {random.choice(votes)} — Build diversity matters.\n"
        f"Proposition 3: {random.choice(votes)} — Pool parity is important.\n\n"
        f"FINAL COMMENT: Good discussion overall."
    )


class Council:
    """Orchestrates a multi-model Round Table session."""

    def __init__(
        self,
        question: str,
        panelists: list[str],
        moderator: str,
        dry_run: bool = False,
        skip_critique: bool = False,
        skip_vote: bool = False,
        max_workers: int = 4,
    ):
        self.question = question
        self.panelists = panelists
        self.moderator = moderator
        self.dry_run = dry_run
        self.skip_critique = skip_critique
        self.skip_vote = skip_vote
        self.max_workers = max_workers

        # Validate
        for m in panelists:
            if m not in MODEL_PROVIDERS and not dry_run:
                raise ValueError(f"Unknown model: {m}")
        if moderator not in MODEL_PROVIDERS and not dry_run:
            raise ValueError(f"Unknown moderator model: {moderator}")

        self.session = CouncilSession(
            question=question,
            moderator=moderator,
            panelists=panelists,
        )

    def run(self) -> CouncilSession:
        """Execute all phases and return the completed session."""
        t0 = time.time()

        self._phase_responses()
        if not self.skip_critique:
            self._phase_critiques()
        self._phase_synthesis()
        if not self.skip_vote:
            self._phase_votes()

        self.session.total_elapsed_s = time.time() - t0
        self.session.compute_totals()
        return self.session

    # ------------------------------------------------------------------
    # Phase 2: Independent responses (parallel)
    # ------------------------------------------------------------------

    def _phase_responses(self) -> None:
        n = len(self.panelists)
        _progress(f"Phase 1/4: Collecting responses... 0/{n}")

        def _get_response(model: str) -> Response:
            provider = MODEL_PROVIDERS.get(model, "unknown")
            if self.dry_run:
                time.sleep(random.uniform(0.3, 0.8))
                return Response(
                    model=model, provider=provider,
                    text=_dry_response(model), elapsed_s=0.5,
                )
            prompt = response_prompt(self.question, model, self.panelists)
            t0 = time.time()
            try:
                text, in_tok, out_tok = call_model(model, prompt)
                elapsed = time.time() - t0
                return Response(
                    model=model, provider=provider, text=text,
                    elapsed_s=elapsed, input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=estimate_cost(model, in_tok, out_tok),
                )
            except Exception as e:
                return Response(
                    model=model, provider=provider,
                    text=f"[ERROR: {e}]", elapsed_s=time.time() - t0,
                    error=str(e),
                )

        done = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(_get_response, m): m for m in self.panelists}
            for future in as_completed(futures):
                resp = future.result()
                self.session.responses.append(resp)
                done += 1
                _progress(f"Phase 1/4: Collecting responses... {done}/{n}")

        # Sort by panelist order
        order = {m: i for i, m in enumerate(self.panelists)}
        self.session.responses.sort(key=lambda r: order.get(r.model, 99))
        _progress(f"Phase 1/4: Collecting responses... {n}/{n} done\n")

    # ------------------------------------------------------------------
    # Phase 3: Critique round (parallel)
    # ------------------------------------------------------------------

    def _phase_critiques(self) -> None:
        n = len(self.panelists)
        _progress(f"Phase 2/4: Critique round... 0/{n}")

        all_responses = {r.model: r.text for r in self.session.responses}

        def _get_critique(model: str) -> Critique:
            provider = MODEL_PROVIDERS.get(model, "unknown")
            if self.dry_run:
                time.sleep(random.uniform(0.3, 0.8))
                return Critique(
                    model=model, provider=provider,
                    text=_dry_critique(model), elapsed_s=0.5,
                )
            prompt = critique_prompt(self.question, model, all_responses)
            t0 = time.time()
            try:
                text, in_tok, out_tok = call_model(model, prompt)
                elapsed = time.time() - t0
                return Critique(
                    model=model, provider=provider, text=text,
                    elapsed_s=elapsed, input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=estimate_cost(model, in_tok, out_tok),
                )
            except Exception as e:
                return Critique(
                    model=model, provider=provider,
                    text=f"[ERROR: {e}]", elapsed_s=time.time() - t0,
                    error=str(e),
                )

        done = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(_get_critique, m): m for m in self.panelists}
            for future in as_completed(futures):
                crit = future.result()
                self.session.critiques.append(crit)
                done += 1
                _progress(f"Phase 2/4: Critique round... {done}/{n}")

        order = {m: i for i, m in enumerate(self.panelists)}
        self.session.critiques.sort(key=lambda c: order.get(c.model, 99))
        _progress(f"Phase 2/4: Critique round... {n}/{n} done\n")

    # ------------------------------------------------------------------
    # Phase 4: Synthesis (moderator only — sequential)
    # ------------------------------------------------------------------

    def _phase_synthesis(self) -> None:
        _progress("Phase 3/4: Synthesizing...")

        all_responses = {r.model: r.text for r in self.session.responses}
        all_critiques = {c.model: c.text for c in self.session.critiques}

        if self.dry_run:
            time.sleep(random.uniform(0.5, 1.0))
            self.session.synthesis = Synthesis(
                model=self.moderator,
                text=_dry_synthesis(),
                elapsed_s=0.7,
            )
            _progress("Phase 3/4: Synthesizing... done\n")
            return

        prompt = synthesis_prompt(self.question, all_responses, all_critiques)
        t0 = time.time()
        try:
            text, in_tok, out_tok = call_model(self.moderator, prompt)
            elapsed = time.time() - t0
            self.session.synthesis = Synthesis(
                model=self.moderator, text=text,
                elapsed_s=elapsed, input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=estimate_cost(self.moderator, in_tok, out_tok),
            )
        except Exception as e:
            self.session.synthesis = Synthesis(
                model=self.moderator,
                text=f"[SYNTHESIS ERROR: {e}]",
                elapsed_s=time.time() - t0,
            )

        _progress("Phase 3/4: Synthesizing... done\n")

    # ------------------------------------------------------------------
    # Phase 5: Voting (parallel)
    # ------------------------------------------------------------------

    def _phase_votes(self) -> None:
        if not self.session.synthesis:
            return

        n = len(self.panelists)
        _progress(f"Phase 4/4: Voting... 0/{n}")

        synthesis_text = self.session.synthesis.text

        def _get_vote(model: str) -> Vote:
            provider = MODEL_PROVIDERS.get(model, "unknown")
            if self.dry_run:
                time.sleep(random.uniform(0.2, 0.5))
                return Vote(
                    model=model, provider=provider,
                    votes=[],  # raw text in dry run
                    elapsed_s=0.3,
                )
            prompt = vote_prompt(model, synthesis_text)
            t0 = time.time()
            try:
                text, in_tok, out_tok = call_model(model, prompt)
                elapsed = time.time() - t0
                # Parse votes from text
                parsed_votes = _parse_votes(text)
                return Vote(
                    model=model, provider=provider,
                    votes=parsed_votes,
                    elapsed_s=elapsed, input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=estimate_cost(model, in_tok, out_tok),
                )
            except Exception as e:
                return Vote(
                    model=model, provider=provider, votes=[],
                    elapsed_s=time.time() - t0, error=str(e),
                )

        done = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(_get_vote, m): m for m in self.panelists}
            for future in as_completed(futures):
                vote = future.result()
                self.session.votes.append(vote)
                done += 1
                _progress(f"Phase 4/4: Voting... {done}/{n}")

        order = {m: i for i, m in enumerate(self.panelists)}
        self.session.votes.sort(key=lambda v: order.get(v.model, 99))
        _progress(f"Phase 4/4: Voting... {n}/{n} done\n")


def _parse_votes(text: str) -> list[dict[str, str]]:
    """Parse vote text into structured vote records."""
    import re
    votes: list[dict[str, str]] = []
    pattern = re.compile(
        r"Proposition\s+(\d+)\s*:\s*(AGREE|DISAGREE|ABSTAIN)\s*[—\-–]\s*(.*)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        votes.append({
            "point": f"Proposition {match.group(1)}",
            "vote": match.group(2).upper(),
            "reason": match.group(3).strip(),
        })
    return votes
