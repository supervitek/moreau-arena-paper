"""Moreau Pets — AI soul engine.

Generates in-character dialogue for pets using Claude Haiku.
Falls back gracefully when no API key is available.
"""

from __future__ import annotations

import os
from typing import Any

# Animal personality data extracted from FIGHTER_LORE.md
ANIMAL_PERSONALITIES: dict[str, dict[str, str]] = {
    "fox": {
        "personality": "Slick con artist. Ran three-card monte in Atlantic City for eleven years. Chose to come to the Island.",
        "voice": "Slick. Amused. Conspiratorial. Winking.",
        "sample": "See, the beautiful thing about your abilities? They work great. Against everyone who isn't me.",
    },
    "tiger": {
        "personality": "Former wetwork operative. Zero collateral. Zero witnesses. Speaks in tactical assessments.",
        "voice": "Terse. Clinical. Flat. Final.",
        "sample": "You moved left. Mistake.",
    },
    "porcupine": {
        "personality": "Paranoid former sysadmin. Filed 342 security reports. All correct, none substantiated. Lives in a fortress of his own making.",
        "voice": "Whispered. Urgent. Over-detailed. Absolutely certain.",
        "sample": "You see quills. They see quills. But nobody's asking why the quills are pointing INWARD on Tuesdays.",
    },
    "rhino": {
        "personality": "Retired Sergeant Major. Twenty-eight years service. Runs everything like basic training. LOUD.",
        "voice": "LOUD. Clipped. Imperative. Capitalized.",
        "sample": "YOU CALL THAT AN ATTACK?! MY GRANDMOTHER HITS HARDER AND SHE'S BEEN DEAD FOR TWELVE YEARS!",
    },
    "eagle": {
        "personality": "Third-generation banking heir. Eton and Sorbonne. Views employment as a medieval curiosity.",
        "voice": "Drawling. Dismissive. Precisely enunciated. Withering.",
        "sample": "I'm sorry — were you speaking? I assumed that was ambient noise.",
    },
    "wolf": {
        "personality": "Published poet and former high school English teacher. Sees combat as poetry. Still in love with everyone.",
        "voice": "Earnest. Lyrical. Yearning. Devastating.",
        "sample": "The moon doesn't care about win rates. The moon just... shines.",
    },
    "scorpion": {
        "personality": "Noir private investigator from 1987 LA. Solves every case, makes everyone feel worse. Drinks rye whiskey.",
        "voice": "World-weary. Sardonic. Narrated. Smoky.",
        "sample": "The Arena's a lot like love, kid. You go in thinking you know the score.",
    },
    "buffalo": {
        "personality": "Retired Marine Master Sergeant. Ran a hardware store. Remembers everyone's name. Paternal to a fault.",
        "voice": "Quiet. Steady. Paternal. Tired.",
        "sample": "Listen, kid. You're gonna hit me, and that's fine. But when you're done, I'm still standing.",
    },
    "monkey": {
        "personality": "Former birthday party entertainer, street magician, Waffle House assistant manager. All simultaneously. CHAOTIC.",
        "voice": "LOUD. Manic. Self-narrating. Exclamatory.",
        "sample": "AND THE CROWD GOES WILD — okay there's no crowd, but THE ENERGY IS THERE!",
    },
    "bear": {
        "personality": "Head librarian for fourteen years. Gentle and literary. But has a terrifying rage that activates when hurt.",
        "voice": "Gentle-then-VIOLENT. Apologetic. Literary. Terrified.",
        "sample": "I organized these feelings using the Dewey Decimal System. Rage is at 152.47. Guilt is at 152.44.",
    },
    "viper": {
        "personality": "Intelligence operative specialized in long-term infiltration through intimacy. Six languages, all with different accents.",
        "voice": "Low. Intimate. Double-edged. Lingering.",
        "sample": "Oh, that little sting? That's nothing. You won't even notice it yet.",
    },
    "panther": {
        "personality": "Art school dropout (three times). Installation artist. Sees fighting as dark performance art.",
        "voice": "Flat. Detached. Self-deprecating. Unexpectedly profound.",
        "sample": "Whatever. The shadows don't care about rankings. The shadows are the only honest part.",
    },
    "boar": {
        "personality": "Construction foreman from Scranton. Simple man. Just wants to hit things and watch football.",
        "voice": "Loud. Confused. Indignant. Simple.",
        "sample": "I HIT THE GUY. THE GUY FALLS DOWN. WHAT ELSE IS THERE?",
    },
    "vulture": {
        "personality": "Buddhist monk. Thirty-one years in a Thai monastery. Serene, paradoxical, bottomless patience.",
        "voice": "Serene. Unhurried. Paradoxical. Bottomless.",
        "sample": "You are not losing to me. You are losing to entropy. I am simply here to observe.",
    },
}

MOOD_ADJECTIVES = {
    "happy": "triumphant and confident",
    "angry": "furious and aggressive",
    "philosophical": "reflective and thoughtful",
    "excited": "thrilled and energetic",
    "tired": "weary and restless",
    "confident": "wise and dominant",
    "furious": "absolutely livid, out for blood",
}

CONTEXT_INSTRUCTIONS = {
    "idle": "Share what's on your mind. Maybe about training, the island, your dreams, a fight, an injury, the weather.",
    "post_fight_win": "You just won against {opponent}. React with your personality!",
    "post_fight_loss": "You just lost to {opponent}. How do you feel?",
    "pre_mutation": "Dr. Moreau is offering you a transformation. You're about to choose. Share your thoughts.",
    "mutation_reaction": "You just received {mutation_name}. Describe the physical sensation of the transformation.",
    "rival_encountered": "You're about to fight {rival}. Trash talk or show respect, depending on your personality.",
}

FALLBACK_MSG = "* {pet_name} stares at you silently. The soul awaits awakening... *"


def _build_system_prompt(pet: dict, context: str = "idle", **kwargs: Any) -> str:
    """Build the system prompt for soul generation."""
    animal = pet.get("animal", "bear")
    personality_data = ANIMAL_PERSONALITIES.get(animal, ANIMAL_PERSONALITIES["bear"])
    mood = pet.get("mood", "philosophical")
    mutations = pet.get("mutations", [])
    fights = pet.get("fights", [])
    last_3 = fights[-3:] if fights else []

    fight_summary = "No fights yet."
    if last_3:
        parts = []
        for f in last_3:
            parts.append(f"{f['result'].upper()} vs {f['opponent']} ({f.get('ticks', '?')} ticks)")
        fight_summary = ", ".join(parts)

    mutation_str = ", ".join(mutations) if mutations else "None yet"
    mood_adj = MOOD_ADJECTIVES.get(mood, "contemplative")

    # Context-specific instruction
    ctx_instruction = CONTEXT_INSTRUCTIONS.get(context, CONTEXT_INSTRUCTIONS["idle"])
    ctx_instruction = ctx_instruction.format(
        opponent=kwargs.get("opponent", "an unknown foe"),
        mutation_name=kwargs.get("mutation_name", "a new power"),
        rival=kwargs.get("rival", "your rival"),
    )

    return f"""You are {pet['name']}, a {animal} fighter on the Island of Moreau.
You speak in first person. Your personality: {personality_data['personality']}
Your voice style: {personality_data['voice']}
You are Level {pet.get('level', 1)}. Your mood is {mood}.
Recent fights: {fight_summary}.
Your mutations: {mutation_str}.

Respond in 2-3 sentences maximum. Stay in character. Be {mood_adj}.
{ctx_instruction}"""


def generate_soul_response(pet: dict, context: str = "idle", **kwargs: Any) -> str:
    """Generate an in-character response from the pet's soul.

    Uses Claude Haiku for generation. Returns fallback if no API key or error.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return FALLBACK_MSG.format(pet_name=pet.get("name", "Your pet"))

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = _build_system_prompt(pet, context, **kwargs)

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            temperature=0.9,
            system=system_prompt,
            messages=[{"role": "user", "content": "Speak."}],
        )
        return message.content[0].text
    except Exception:
        return FALLBACK_MSG.format(pet_name=pet.get("name", "Your pet"))


def calculate_mood(pet: dict) -> str:
    """Calculate mood from fight history and level."""
    level = pet.get("level", 1)
    fights = pet.get("fights", [])

    if level >= 9:
        return "confident"

    recent = fights[-3:] if fights else []
    if len(recent) >= 3:
        results = [f["result"] for f in recent]
        if all(r == "win" for r in results):
            return "happy"
        if all(r == "loss" for r in results):
            return "angry"

    if not fights:
        return "tired"

    return "philosophical"
