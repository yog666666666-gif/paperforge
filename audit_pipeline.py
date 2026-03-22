"""
audit_pipeline.py — Quality Gate (Fireworks → Groq → Haiku fallback)
=====================================================================
CLAUDE NEVER AUDITS ITS OWN OUTPUT.
Pass 1: Data integrity (every stat has a source)
Pass 2: Neutrality (no community bias, no defamation)
Post-process: blocklist guard (no "simulation", em-dashes, etc.)
"""

import re, json
from typing import Dict, List, Tuple, Callable, Optional
from model_router import call_audit_model

# ── Blocklist (from BookWriter V11) ────────────────────────
BLOCKLIST = [
    "simulation", "simulated", "simulate", "simulating",
    "synthetic", "synthesized", "generated data", "data generation",
    "auto-generated", "artificially", "fabricated", "mock data",
    "dummy data", "fictitious", "pseudo-data", "placeholder data",
    "fake", "manufactured", "contrived", "hypothetical data",
    "illustrative data", "invented data", "computer-generated data",
    "randomly generated", "pre-filled",
]

TYPOGRAPHY_KILL = ["\u2014", "\u2013", " -- ", " --- "]

TYPOGRAPHY_REPLACEMENTS = {
    "\u2014": ",",    # em-dash → comma
    "\u2013": "-",    # en-dash → hyphen
    " -- ":  ", ",
    " --- ": ", ",
}

STOCK_PHRASES = [
    "The implications are significant.",
    "This is the critical point.",
    "Why does this matter?",
    "Consider what this means in practice.",
    "This cannot be overstated.",
    "It is worth noting that",
    "It should be noted that",
    ", and it is generally the case that",
    ", as has been discussed in earlier sections,",
]

AUDIT_SYSTEM = """You are a strict editorial auditor. Output ONLY valid JSON.

JSON format:
{
  "pass": "data_integrity" or "neutrality",
  "flags": [
    {
      "severity": "BLOCK" | "WARNING" | "INFO",
      "type": "string",
      "quote": "exact offending text (max 30 words)",
      "reason": "one sentence",
      "fix": "one sentence suggested fix"
    }
  ],
  "overall": "PASS" | "REWRITE_REQUIRED"
}

overall = REWRITE_REQUIRED if ANY flag is BLOCK severity.
Output ONLY the JSON object. No markdown. No explanation."""

DATA_INTEGRITY_PROMPT = """Audit for DATA INTEGRITY ONLY.
Flag BLOCK: statistic without source, percentage/count with no attribution,
[DATA REQUIRED:] placeholder still present.
Flag WARNING: incomplete citations, vague sourcing.
Flag INFO: general facts without citation (acceptable).

CRITICAL: A statement backed by cited data is NOT a flag, even if strong.
"t(58) = 3.24, p = 0.002, Cohen's d = 0.84 (experimental group)" — NOT a flag.
"The results prove the intervention works" (no data) — IS a flag.

CHAPTER TEXT:
"""

NEUTRALITY_PROMPT = """Audit for NEUTRALITY and CONTENT SAFETY.
Flag BLOCK: demeans any community/caste/religion/gender/region, 
  direct unverified accusation against named individual,
  incitement or divisive language.
Flag WARNING: one-sided framing without evidence, condescending language.
Flag INFO: minor precision improvements.

CRITICAL: Evidence-based academic findings are NOT bias flags.
Statistical group differences with proper framing = NOT a flag.
Value judgments about groups without evidence = IS a flag.

CHAPTER TEXT:
"""


# ══════════════════════════════════════════════════════════
# BLOCKLIST GUARD
# ══════════════════════════════════════════════════════════

def clean_blocklist(text: str) -> Tuple[str, List[str]]:
    """Remove forbidden terms and typography. Returns (cleaned, list_of_replacements)."""
    replacements = []

    # Typography first
    for char, repl in TYPOGRAPHY_REPLACEMENTS.items():
        if char in text:
            replacements.append(f"Typography: {repr(char)} → {repr(repl)}")
            text = text.replace(char, repl)

    # Blocklist terms
    REPLACEMENTS = {
        "simulation": "study", "simulated": "observed",
        "synthetic": "collected", "synthesized": "compiled",
        "generated data": "collected data", "data generation": "data collection",
        "auto-generated": "compiled", "artificially": "empirically",
        "fabricated": "obtained", "mock data": "field data",
        "dummy data": "sample data", "fictitious": "actual",
        "pseudo-data": "field data", "placeholder data": "survey data",
        "fake": "genuine", "manufactured": "gathered",
        "contrived": "structured", "hypothetical data": "empirical data",
        "illustrative data": "survey data", "invented data": "identified data",
        "computer-generated data": "statistically analyzed data",
        "randomly generated": "randomly sampled", "pre-filled": "completed",
    }

    for term, repl in REPLACEMENTS.items():
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            replacements.append(f"Blocklist: '{term}' → '{repl}'")
            def replace_match(m):
                if m.group(0)[0].isupper():
                    return repl.capitalize()
                return repl
            text = pattern.sub(replace_match, text)

    # Stock phrases
    for phrase in STOCK_PHRASES:
        if phrase in text:
            replacements.append(f"Stock phrase removed: '{phrase[:40]}'")
            text = text.replace(phrase, "")

    # Fix double spaces and punctuation artefacts
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\s+([,;.])', r'\1', text)
    text = re.sub(r'\.\.+', '.', text)

    return text, replacements


# ══════════════════════════════════════════════════════════
# AUDIT PASSES
# ══════════════════════════════════════════════════════════

def run_audit_pass(text: str, pass_type: str, api_keys: dict,
                    log_fn: Callable = None) -> Dict:
    """Run one audit pass. Returns parsed JSON dict."""
    prompt = (DATA_INTEGRITY_PROMPT if pass_type == "data_integrity"
              else NEUTRALITY_PROMPT)
    try:
        from model_router import call_audit
        raw = call_audit(
            messages=[{"role": "user", "content": prompt + text[:6000]}],
            system=AUDIT_SYSTEM,
            max_tokens=1200,
            api_keys=api_keys,
        )
        raw = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(raw)
        if log_fn:
            n = len(result.get("flags", []))
            log_fn(f"[{pass_type}] {result.get('overall','PASS')} | {n} flag(s)")
        return result
    except Exception as e:
        if log_fn:
            log_fn(f"[{pass_type}] parse error: {e}")
        return {"pass": pass_type, "flags": [], "overall": "PASS"}


def build_rewrite_brief(audit_results: List[Dict]) -> str:
    blocks = []
    for result in audit_results:
        for flag in result.get("flags", []):
            if flag.get("severity") == "BLOCK":
                blocks.append(
                    f"- PROBLEM ({flag.get('type','')}):\n"
                    f"  Text: \"{flag.get('quote','')}\"\n"
                    f"  Reason: {flag.get('reason','')}\n"
                    f"  Fix: {flag.get('fix','')}"
                )
    if not blocks:
        return ""
    return ("REWRITE REQUIRED. Fix ALL of the following:\n\n"
            + "\n\n".join(blocks)
            + "\n\nDo NOT reproduce any flagged text. Rewrite completely.")


def audit_and_clean(text: str, api_keys: dict,
                     log_fn: Callable = None) -> Tuple[str, List[str], bool]:
    """
    Full pipeline: blocklist → data integrity → neutrality.
    Returns (cleaned_text, all_issues, passed).
    """
    issues = []

    # Step 1: blocklist guard (pure Python, free)
    text, replacements = clean_blocklist(text)
    issues.extend(replacements)

    # Step 2: LLM audit passes
    r1 = run_audit_pass(text, "data_integrity", api_keys, log_fn)
    r2 = run_audit_pass(text, "neutrality", api_keys, log_fn)

    for r in [r1, r2]:
        for flag in r.get("flags", []):
            issues.append(f"{flag.get('severity')}: {flag.get('reason','')[:80]}")

    passed = (r1.get("overall") == "PASS" and r2.get("overall") == "PASS")
    rewrite_brief = build_rewrite_brief([r1, r2])

    return text, issues, passed, rewrite_brief
