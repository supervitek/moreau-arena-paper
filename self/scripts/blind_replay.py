#!/usr/bin/env python3
"""
Circuit C — Blind Replay Audit

Takes a promoted learning, strips all self-system framing, and sends the raw
claim + evidence to a fresh Claude instance for independent evaluation.

Usage:
    python3 self/scripts/blind_replay.py
"""

import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

# Resolve project root (two levels up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # self/scripts/ -> self/ -> project root

PROVEN_DIR = PROJECT_ROOT / "self" / ".learnings" / "proven"
THINKING_DIR = PROJECT_ROOT / "self" / "thinking"
AUDITS_DIR = PROJECT_ROOT / "self" / "audits"
MARKERS_DIR = PROJECT_ROOT / "self" / "session_markers"

CLAUDE_TIMEOUT = 120  # seconds


def find_claude_binary() -> str:
    """Locate the claude CLI binary."""
    # Try PATH first
    for candidate in ["claude", "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    raise RuntimeError(
        "claude CLI not found. Tried: claude, /opt/homebrew/bin/claude, /usr/local/bin/claude"
    )


def list_proven_learnings() -> list[Path]:
    """Return all .md files in the proven learnings directory."""
    if not PROVEN_DIR.is_dir():
        print(f"ERROR: proven learnings directory not found: {PROVEN_DIR}", file=sys.stderr)
        sys.exit(1)
    files = sorted(PROVEN_DIR.glob("*.md"))
    if not files:
        print("No proven learnings found.", file=sys.stderr)
        sys.exit(1)
    return files


def list_existing_audits() -> dict[str, datetime]:
    """Return a mapping of learning_filename -> audit datetime for existing audits."""
    audits: dict[str, datetime] = {}
    if not AUDITS_DIR.is_dir():
        return audits
    for audit_file in AUDITS_DIR.glob("*.md"):
        name = audit_file.name
        # Format: YYYY-MM-DD_<learning_filename>.md
        # Extract learning filename by stripping the date prefix
        match = re.match(r"\d{4}-\d{2}-\d{2}_(.+)$", name)
        if match:
            learning_name = match.group(1)
            # Parse the date from the filename
            date_str = name[:10]
            try:
                audit_dt = datetime.strptime(date_str, "%Y-%m-%d")
                # Keep the most recent audit per learning
                if learning_name not in audits or audit_dt > audits[learning_name]:
                    audits[learning_name] = audit_dt
            except ValueError:
                continue
    return audits


def pick_learning(learnings: list[Path], audits: dict[str, datetime]) -> Path:
    """
    Pick the least-recently-audited learning.
    Prefer unaudited learnings first, then pick the one with the oldest audit.
    """
    # Find unaudited learnings
    unaudited = [lf for lf in learnings if lf.name not in audits]
    if unaudited:
        # Return the first unaudited one (alphabetically)
        return unaudited[0]

    # All have been audited — pick the one with the oldest audit date
    oldest_learning = min(learnings, key=lambda lf: audits.get(lf.name, datetime.min))
    return oldest_learning


def extract_core_claim(content: str) -> str:
    """
    Extract the core claim from a proven learning file.

    Strategy:
    1. Look for a section header containing 'claim', 'pattern', 'core', or 'finding'
       and take the first paragraph under it.
    2. Failing that, take the first substantive paragraph after all top-level
       headers, frontmatter, metadata, and horizontal rules.
    """
    lines = content.split("\n")

    # --- Strategy 1: Find a claim/pattern/core section ---
    claim_section_re = re.compile(
        r"^#{1,3}\s+.*(claim|pattern|core|finding)", re.IGNORECASE
    )
    for i, line in enumerate(lines):
        if claim_section_re.match(line.strip()):
            # Collect the paragraph immediately following this header
            para = _collect_paragraph(lines, i + 1)
            if para:
                return para

    # --- Strategy 2: First substantive paragraph ---
    in_frontmatter = False
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            start_idx = i + 1
            continue
        if in_frontmatter:
            start_idx = i + 1
            continue
        if stripped.startswith("#"):
            start_idx = i + 1
            continue
        if re.match(r"^\*\*[^*]+\*\*", stripped):
            start_idx = i + 1
            continue
        if not stripped:
            start_idx = i + 1
            continue
        # Found the first substantive line
        break

    para = _collect_paragraph(lines, start_idx)
    return para if para else content[:500]


def _collect_paragraph(lines: list[str], start: int) -> str:
    """Collect the first non-empty paragraph starting at line index `start`."""
    result: list[str] = []
    started = False
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#") or stripped == "---":
            if started:
                break
            continue
        # Skip bold metadata lines at the top of the paragraph
        if not started and re.match(r"^\*\*[^*]+\*\*", stripped):
            continue
        started = True
        result.append(stripped)
    return " ".join(result)


def find_thinking_references(content: str) -> list[str]:
    """
    Scan the learning body for references to thinking files.
    Matches patterns like: thinking/063, thinking/097, thinking/098
    """
    # Match thinking/NNN patterns
    matches = re.findall(r"thinking/(\d{3})", content)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def read_thinking_file(number: str) -> tuple[str, str]:
    """
    Read a thinking file by number. Returns (filename, content).
    Thinking files are named like: NNN_description.md
    """
    pattern = f"{number}_*.md"
    matches = list(THINKING_DIR.glob(pattern))
    if not matches:
        return f"thinking/{number}", f"[File not found: thinking/{number}_*.md]"
    filepath = matches[0]
    try:
        content = filepath.read_text(encoding="utf-8")
        return filepath.name, content
    except Exception as e:
        return filepath.name, f"[Error reading {filepath.name}: {e}]"


def build_audit_prompt(claim: str, evidence_files: list[tuple[str, str]]) -> str:
    """
    Build the minimal audit prompt — no preamble.md, no mirror.md, no hypothesis IDs.
    """
    prompt_parts = [
        "You are an independent reviewer. A claim was made by an AI self-reflection system.",
        "Your job is to evaluate whether the cited evidence supports the claim.",
        "",
        "## Claim",
        claim,
        "",
        "## Evidence Files",
    ]

    for filename, content in evidence_files:
        prompt_parts.append(f"### {filename}")
        prompt_parts.append(content)
        prompt_parts.append("")

    prompt_parts.extend([
        "## Questions",
        "1. Does the evidence logically support the claim? Why or why not?",
        "2. What alternative explanations could account for the same evidence?",
        "3. Are there any circular reasoning patterns (claim assumes its own conclusion)?",
        "4. Confidence assessment: HIGH / MEDIUM / LOW / UNSUPPORTED",
        "",
        "Be rigorous. The claim may be wrong.",
    ])

    return "\n".join(prompt_parts)


def run_claude_audit(prompt: str, claude_bin: str) -> tuple[str, bool]:
    """
    Run the audit prompt through claude -p with read-only tools.
    Returns (response_text, success).
    """
    # Build environment: force Max subscription by clearing API key
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = ""

    try:
        result = subprocess.run(
            [claude_bin, "-p", prompt, "--allowedTools", "Read"],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env=env,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return result.stdout.strip(), True
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return f"[Claude exited with code {result.returncode}]\n{error_msg}", False
    except subprocess.TimeoutExpired:
        return f"[Claude timed out after {CLAUDE_TIMEOUT}s]", False
    except Exception as e:
        return f"[Error running claude: {e}]", False


def extract_verdict(response: str) -> str:
    """Extract the confidence assessment from the auditor's response."""
    # Look for explicit confidence keywords
    response_upper = response.upper()
    for level in ["UNSUPPORTED", "LOW", "MEDIUM", "HIGH"]:
        # Check for the word near "confidence" or as a standalone verdict
        if re.search(
            rf"(?:CONFIDENCE|VERDICT|ASSESSMENT)[:\s]*{level}", response_upper
        ):
            return level

    # Fallback: look for standalone mentions in the last portion of the response
    last_portion = response_upper[-500:]
    for level in ["UNSUPPORTED", "LOW", "MEDIUM", "HIGH"]:
        if level in last_portion:
            return level

    return "UNKNOWN"


def write_audit_file(
    learning_path: Path,
    claim: str,
    evidence_names: list[str],
    response: str,
    verdict: str,
) -> Path:
    """Write the audit result to self/audits/."""
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    output_name = f"{today}_{learning_path.name}"
    output_path = AUDITS_DIR / output_name

    evidence_list = "\n".join(f"- {name}" for name in evidence_names)

    content = f"""# Blind Replay Audit: {learning_path.stem}
**Date:** {today}
**Learning file:** self/.learnings/proven/{learning_path.name}
**Evidence files:**
{evidence_list}

## Claim
{claim}

## Auditor Response
{response}

## Verdict
{verdict}
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def write_audit_flag(verdict: str, learning_path: Path) -> Path | None:
    """If verdict is LOW or UNSUPPORTED, create a flag marker."""
    if verdict not in ("LOW", "UNSUPPORTED"):
        return None

    MARKERS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    flag_path = MARKERS_DIR / f"AUDIT_FLAG_{today}.md"
    flag_content = f"""# Audit Flag
**Date:** {today}
**Learning:** {learning_path.name}
**Verdict:** {verdict}

Circuit C blind replay returned {verdict} confidence for this learning.
Manual review recommended.
"""
    flag_path.write_text(flag_content, encoding="utf-8")
    return flag_path


def main() -> None:
    print("=== Circuit C: Blind Replay Audit ===\n")

    # Step 1: Find learnings
    learnings = list_proven_learnings()
    print(f"Found {len(learnings)} proven learnings.")

    # Step 2: Pick target
    audits = list_existing_audits()
    target = pick_learning(learnings, audits)
    print(f"Selected: {target.name}")
    if target.name in audits:
        print(f"  (Last audited: {audits[target.name].date()})")
    else:
        print("  (Never audited)")

    # Step 3: Read and extract claim
    content = target.read_text(encoding="utf-8")
    claim = extract_core_claim(content)
    print(f"\nClaim extracted ({len(claim)} chars).")

    # Step 4: Find thinking references
    thinking_refs = find_thinking_references(content)
    print(f"Thinking references found: {thinking_refs if thinking_refs else '(none)'}")

    # Step 5: Read evidence files
    evidence_files: list[tuple[str, str]] = []
    for ref_num in thinking_refs:
        filename, file_content = read_thinking_file(ref_num)
        evidence_files.append((filename, file_content))
        print(f"  Read: {filename} ({len(file_content)} chars)")

    if not evidence_files:
        print("  No thinking file references found — using learning body as evidence.")
        evidence_files.append((target.name, content))

    # Step 6: Build prompt
    prompt = build_audit_prompt(claim, evidence_files)
    print(f"\nAudit prompt built ({len(prompt)} chars).")

    # Step 7: Find claude
    print("Locating claude CLI...")
    claude_bin = find_claude_binary()
    print(f"  Using: {claude_bin}")

    # Step 8: Run audit
    print("\nRunning blind audit (timeout: {}s)...".format(CLAUDE_TIMEOUT))
    response, success = run_claude_audit(prompt, claude_bin)
    if success:
        print(f"Audit complete ({len(response)} chars).")
    else:
        print(f"Audit failed: {response[:200]}")

    # Step 9: Extract verdict
    verdict = extract_verdict(response)
    print(f"Verdict: {verdict}")

    # Step 10: Write output
    evidence_names = [name for name, _ in evidence_files]
    audit_path = write_audit_file(target, claim, evidence_names, response, verdict)
    print(f"\nAudit written: {audit_path.relative_to(PROJECT_ROOT)}")

    # Step 11: Flag if needed
    flag_path = write_audit_flag(verdict, target)
    if flag_path:
        print(f"FLAG created: {flag_path.relative_to(PROJECT_ROOT)}")
        print("  -> LOW/UNSUPPORTED verdict. Manual review recommended.")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
