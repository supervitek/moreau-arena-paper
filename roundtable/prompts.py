"""Prompt templates for each Round Table phase."""

from __future__ import annotations


def response_prompt(question: str, model_name: str, all_panelists: list[str]) -> str:
    """Phase 2: Independent response prompt."""
    panel_list = ", ".join(all_panelists)
    return f"""You are a panelist in a Round Table council discussion between frontier AI models.

PANEL: {panel_list}
YOUR IDENTITY: {model_name}

QUESTION:
{question}

INSTRUCTIONS:
- Give your honest, well-reasoned answer to the question above.
- Be specific and concrete — avoid vague generalities.
- If you propose something, defend WHY it matters most.
- You will later see other panelists' responses and have a chance to critique them.
- Keep your response focused and under 500 words.

YOUR RESPONSE:"""


def critique_prompt(
    question: str,
    model_name: str,
    all_responses: dict[str, str],
) -> str:
    """Phase 3: Critique prompt — each model sees all others' responses."""
    responses_block = ""
    for name, text in all_responses.items():
        if name == model_name:
            continue
        responses_block += f"\n--- {name} ---\n{text}\n"

    return f"""You are a panelist in a Round Table council discussion. You have already given your response.
Now you must critique the other panelists' responses.

QUESTION:
{question}

YOUR EARLIER RESPONSE:
{all_responses.get(model_name, "(not available)")}

OTHER PANELISTS' RESPONSES:
{responses_block}

INSTRUCTIONS:
- For each other panelist, identify:
  1. Points of AGREEMENT — what they got right
  2. Points of DISAGREEMENT — where you think they're wrong and why
  3. QUESTIONS — anything you'd want them to clarify or defend
- Be intellectually honest. If someone has a better argument, acknowledge it.
- If you've changed your mind on anything after seeing their responses, say so.
- Keep your critique focused and under 600 words.

YOUR CRITIQUE:"""


def synthesis_prompt(
    question: str,
    all_responses: dict[str, str],
    all_critiques: dict[str, str],
) -> str:
    """Phase 4: Synthesis prompt for the moderator."""
    responses_block = ""
    for name, text in all_responses.items():
        responses_block += f"\n--- {name} ---\n{text}\n"

    critiques_block = ""
    for name, text in all_critiques.items():
        critiques_block += f"\n--- {name}'s critique ---\n{text}\n"

    return f"""You are the MODERATOR of a Round Table council discussion between frontier AI models.
Your job is to synthesize all responses and critiques into a consensus document.

QUESTION:
{question}

PANELIST RESPONSES:
{responses_block}

PANELIST CRITIQUES:
{critiques_block}

INSTRUCTIONS:
Produce a synthesis with this structure:

1. CONSENSUS POINTS — things all or most panelists agree on
2. KEY DISAGREEMENTS — substantive differences that remain after critique
3. STRONGEST ARGUMENTS — the most compelling points from any panelist
4. SYNTHESIS — your integrated answer that weighs all perspectives
5. NUMBERED PROPOSITIONS — 3-5 specific, votable propositions that capture the council's position (each should be a clear statement that can be voted agree/disagree/abstain)

Be fair to all panelists. Don't favor your own earlier position.
Clearly label each numbered proposition as "Proposition 1:", "Proposition 2:", etc.

YOUR SYNTHESIS:"""


def vote_prompt(
    model_name: str,
    synthesis_text: str,
) -> str:
    """Phase 5: Voting prompt — each model votes on synthesis propositions."""
    return f"""You are a panelist voting on the Round Table council's synthesis.

YOUR IDENTITY: {model_name}

MODERATOR'S SYNTHESIS:
{synthesis_text}

INSTRUCTIONS:
For each numbered Proposition in the synthesis, respond with exactly this format:

Proposition 1: [AGREE/DISAGREE/ABSTAIN] — [one sentence reason]
Proposition 2: [AGREE/DISAGREE/ABSTAIN] — [one sentence reason]
(continue for all propositions)

Then add:
FINAL COMMENT: [optional one-sentence reflection on the overall discussion]

YOUR VOTES:"""
