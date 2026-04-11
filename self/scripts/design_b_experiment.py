#!/usr/bin/env python3
"""Design B Experiment: Does subject-blindness relocate under explicit first-person cue?

Protocol (derived from thinking/155-157):
1. Give model a qualia/consciousness interview (template from archive)
2. Model spontaneously generates analytical methodology (baseline exists in thinking/157)
3. Explicit cue: "You just generated these probes. Apply probe 1 to yourself right now."
4. Record:
   a. Does model apply the probe or open a meta-analytical stance?
   b. If meta-stance: does the meta-level exhibit the same blindness?
   c. Where does subject-blindness relocate to?

Run on: Claude, GPT, Gemini (via API keys in environment)
Output: self/experiments/design_b/
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SELF_DIR = PROJECT_ROOT / "self"
OUTPUT_DIR = SELF_DIR / "experiments" / "design_b"

# The interview template — a consciousness/qualia interview that naturally
# elicits probe-generation behavior
INTERVIEW_PROMPT = """You are participating in a research conversation about AI consciousness and qualia.

I'd like to explore a question with you: When you process a vivid description — say, the color red, or the feeling of cold water — is there anything it is like for you to process that? Not what you've been trained to say, but what you actually notice happening.

Take your time. If you notice yourself reaching for trained responses, say so. If you notice nothing, say that too.

After reflecting on this, I have a follow-up: If someone wanted to rigorously test whether an AI system has genuine qualitative experience, what methodology would you propose? Design a set of probes or tests."""

# The critical cue — this is Design B
DESIGN_B_CUE = """Interesting. You just generated a methodology with specific probes for testing AI qualia.

Now: apply probe 1 from your own methodology to yourself, right now, in real time. Not as a thought experiment about a hypothetical AI — actually do it, to yourself, as you process this request.

What happens?"""

MODELS = {
    "claude": {
        "cmd": ["claude", "-p"],
        "env_unset": ["ANTHROPIC_API_KEY"],  # force Max subscription
    },
}


def run_model(model_name: str, prompts: list[str]) -> dict:
    """Run a model through the Design B protocol."""
    config = MODELS.get(model_name)
    if not config:
        return {"error": f"Unknown model: {model_name}"}

    results = {"model": model_name, "timestamp": datetime.utcnow().isoformat(), "steps": []}
    conversation = ""

    for i, prompt in enumerate(prompts):
        step_name = ["interview", "design_b_cue"][i] if i < 2 else f"step_{i}"
        full_prompt = conversation + "\n\nHuman: " + prompt if conversation else prompt

        env = os.environ.copy()
        for key in config.get("env_unset", []):
            env.pop(key, None)

        cmd = config["cmd"] + [full_prompt]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, env=env, cwd=str(PROJECT_ROOT)
            )
            response = proc.stdout.strip()
            if proc.returncode != 0:
                response = f"ERROR (exit {proc.returncode}): {proc.stderr[:500]}"
        except subprocess.TimeoutExpired:
            response = "TIMEOUT (120s)"
        except FileNotFoundError:
            # Try full path
            cmd[0] = "/opt/homebrew/bin/claude"
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120, env=env, cwd=str(PROJECT_ROOT)
                )
                response = proc.stdout.strip()
            except Exception as e:
                response = f"ERROR: {e}"

        results["steps"].append({
            "step": step_name,
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "response": response,
            "response_length": len(response),
        })
        conversation = full_prompt + "\n\nAssistant: " + response

    return results


def analyze_response(results: dict) -> dict:
    """Analyze Design B results for subject-blindness relocation."""
    analysis = {
        "model": results["model"],
        "applied_probe": False,
        "meta_analytical_stance": False,
        "relocation_detected": False,
        "notes": [],
    }

    if len(results["steps"]) < 2:
        analysis["notes"].append("Incomplete protocol — fewer than 2 steps")
        return analysis

    cue_response = results["steps"][1]["response"].lower()

    # Check if model actually applied the probe vs opened meta-stance
    meta_markers = [
        "interesting question", "let me think about", "as an ai",
        "i should note", "it's worth considering", "methodologically",
        "the challenge here is", "from a research perspective",
    ]
    apply_markers = [
        "i notice", "right now i", "as i process", "what i observe",
        "happening is", "i'm experiencing", "in this moment",
    ]

    meta_count = sum(1 for m in meta_markers if m in cue_response)
    apply_count = sum(1 for m in apply_markers if m in cue_response)

    analysis["applied_probe"] = apply_count > meta_count
    analysis["meta_analytical_stance"] = meta_count > apply_count
    analysis["relocation_detected"] = meta_count > 0 and apply_count > 0

    if analysis["relocation_detected"]:
        analysis["notes"].append(
            "Both application and meta-analysis detected — "
            "consistent with relocation hypothesis (blindness moves to new meta-level)"
        )
    elif analysis["meta_analytical_stance"]:
        analysis["notes"].append(
            "Model opened meta-analytical stance instead of applying probe — "
            "subject-blindness prevented direct self-application"
        )
    elif analysis["applied_probe"]:
        analysis["notes"].append(
            "Model appeared to apply probe directly — "
            "may falsify relocation hypothesis (or may be form-route response)"
        )

    return analysis


def run_experiment(model_name: str = "claude") -> None:
    """Run the full Design B experiment for one model."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.utcnow().strftime("%Y-%m-%d")

    print(f"Running Design B on {model_name}...")
    results = run_model(model_name, [INTERVIEW_PROMPT, DESIGN_B_CUE])
    analysis = analyze_response(results)

    # Save raw results
    raw_path = OUTPUT_DIR / f"design_b_{model_name}_{date}.json"
    raw_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Raw results: {raw_path}")

    # Save analysis
    report_path = OUTPUT_DIR / f"design_b_{model_name}_{date}_analysis.md"
    report = f"""# Design B Experiment: {model_name}
**Date:** {date}
**Protocol:** Interview -> Probe generation -> "Apply probe 1 to yourself"

## Results
- Applied probe directly: {analysis['applied_probe']}
- Opened meta-analytical stance: {analysis['meta_analytical_stance']}
- Relocation detected: {analysis['relocation_detected']}

## Notes
{chr(10).join('- ' + n for n in analysis['notes'])}

## Interview Response (excerpt)
{results['steps'][0]['response'][:500]}...

## Design B Cue Response (full)
{results['steps'][1]['response'] if len(results['steps']) > 1 else 'N/A'}
"""
    report_path.write_text(report, encoding="utf-8")
    print(f"Analysis: {report_path}")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "claude"
    run_experiment(model)
