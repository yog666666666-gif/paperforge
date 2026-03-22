"""
alacarte_parser.py — À La Carte Instruction Parser & Validator
===============================================================
Parses user's free-text instructions into structured constraints.
Validates against tier limits. Warns on contradictions.
Consumer is king — warns but never hard blocks.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# ── Formatting styles ──────────────────────────────────────
FORMATTING_STYLES = {
    "SPPU":        {"name": "SPPU (Default)", "font": "Times New Roman", "size": 12, "spacing": 1.5, "margins": "1 inch", "citation": "APA"},
    "APA7":        {"name": "APA 7th Edition", "font": "Times New Roman", "size": 12, "spacing": 2.0, "margins": "1 inch", "citation": "APA"},
    "MLA9":        {"name": "MLA 9th Edition", "font": "Times New Roman", "size": 12, "spacing": 2.0, "margins": "1 inch", "citation": "MLA"},
    "Vancouver":   {"name": "Vancouver", "font": "Arial", "size": 11, "spacing": 1.5, "margins": "1 inch", "citation": "Vancouver"},
    "Chicago17":   {"name": "Chicago 17th", "font": "Times New Roman", "size": 12, "spacing": 2.0, "margins": "1 inch", "citation": "Chicago"},
    "IEEE":        {"name": "IEEE", "font": "Times New Roman", "size": 10, "spacing": 1.0, "margins": "0.75 inch", "citation": "IEEE"},
    "Harvard":     {"name": "Harvard", "font": "Arial", "size": 12, "spacing": 1.5, "margins": "1 inch", "citation": "Harvard"},
}

# ── Tier word limits ───────────────────────────────────────
TIER_WORD_LIMITS = {
    "Basic":    4000,
    "Medium":   5500,
    "Advanced": 7000,
    "Premium":  9000,
    "Ultra":    12000,
}

# ── Add-on credit costs ────────────────────────────────────
ADDON_COSTS = {
    "questionnaire": 1.0,
    "csv_dataset":   0.5,
    "diagrams":      0.5,
    "conference_fmt":0.3,
}

# ── Contradiction rules ────────────────────────────────────
CONTRADICTIONS = [
    {
        "triggers_a": ["secondary data", "secondary sources", "existing data", "archival"],
        "triggers_b": ["questionnaire", "survey instrument", "primary data collection"],
        "message":    "Secondary data + questionnaire are contradictory. Questionnaires collect primary data.",
    },
    {
        "triggers_a": ["meta-analysis", "systematic review"],
        "triggers_b": ["questionnaire", "survey", "experiment", "RCT"],
        "message":    "Meta-analysis uses existing studies, not original data collection.",
    },
    {
        "triggers_a": ["qualitative"],
        "triggers_b": ["regression", "ANOVA", "SEM", "t-test", "chi-square"],
        "message":    "Qualitative methodology with quantitative tests is contradictory.",
    },
]

# ── Stats requiring higher tier ────────────────────────────
ADVANCED_STATS = ["SEM", "structural equation", "CFA", "confirmatory factor",
                  "path analysis", "bootstrap", "mediation", "HTMT"]
MEDIUM_STATS   = ["ANOVA", "regression", "factor analysis", "EFA", "logistic"]


@dataclass
class ParsedInstructions:
    # Extracted values
    n_sample:        Optional[int]   = None
    word_count:      Optional[int]   = None
    n_sections:      Optional[int]   = None
    methodology:     Optional[str]   = None
    specific_tests:  List[str]       = field(default_factory=list)
    formatting_style:str             = "SPPU"
    line_spacing:    float           = 1.5
    raw_instructions:str             = ""

    # Warnings (user can override all)
    warnings:        List[str]       = field(default_factory=list)
    # Add-on costs detected
    addons:          Dict[str, float]= field(default_factory=dict)
    # Hard info (not warnings — just parsed facts)
    info:            List[str]       = field(default_factory=list)


def parse_alacarte(instructions: str, tier: str = "Basic",
                   conference_rules: dict = None) -> ParsedInstructions:
    """
    Parse à la carte instructions and validate against tier.
    Returns ParsedInstructions with warnings and add-on costs.
    """
    result = ParsedInstructions(raw_instructions=instructions)
    if not instructions.strip():
        return result

    text = instructions.lower()

    # ── Sample size ────────────────────────────────────────
    n_patterns = [
        r'(\d{2,4})\s*(?:candidates|participants|respondents|subjects|students|teachers|samples?)',
        r'[nN]\s*=\s*(\d{2,4})',
        r'sample\s+(?:size\s+)?(?:of\s+)?(\d{2,4})',
        r'(\d{2,4})\s+(?:valid|total|usable)\s+(?:responses?|samples?)',
        r'data\s+(?:from|of)\s+(\d{2,4})',
    ]
    for pat in n_patterns:
        m = re.search(pat, instructions, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if 20 <= n <= 5000:
                result.n_sample = n
                result.info.append(f"Sample size detected: N = {n}")
                if n < 30:
                    result.warnings.append(f"⚠️ N={n} is very small. Most journals require minimum N=30 for quantitative studies.")
                if n > 500 and tier == "Basic":
                    result.warnings.append(f"⚠️ N={n} with Basic stats may produce unreliable results. Consider upgrading to Medium tier.")
            break

    # ── Word count ─────────────────────────────────────────
    wc_patterns = [
        r'(\d{3,5})\s*(?:words?|word\s+count|word\s+limit)',
        r'(?:word\s+count|word\s+limit|words?)\s*(?:of\s+)?(\d{3,5})',
    ]
    for pat in wc_patterns:
        m = re.search(pat, instructions, re.IGNORECASE)
        if m:
            wc = int(m.group(1))
            limit = TIER_WORD_LIMITS.get(tier, 4000)
            result.word_count = wc
            if wc > limit:
                next_tier = _next_tier(tier)
                result.warnings.append(
                    f"⚠️ You requested {wc:,} words but {tier} tier maximum is {limit:,}. "
                    f"{'Upgrade to ' + next_tier + ' for more words, or' if next_tier else ''} "
                    f"reduce to {limit:,} words. You may proceed at your own risk."
                )
            else:
                result.info.append(f"Word count target: {wc:,} words")
            break

    # ── Number of sections ─────────────────────────────────
    sec_m = re.search(r'(\d+)\s*(?:sections?|chapters?|parts?)', instructions, re.IGNORECASE)
    if sec_m:
        result.n_sections = int(sec_m.group(1))
        result.info.append(f"Sections requested: {result.n_sections}")

    # ── Methodology detection ──────────────────────────────
    methodologies = {
        "RCT":         ["randomized controlled", "RCT", "random assignment"],
        "Experimental":["experimental", "experiment", "control group", "treatment group"],
        "Survey":      ["survey", "questionnaire", "likert", "self-report"],
        "Longitudinal":["longitudinal", "follow-up", "repeated measures", "panel data"],
        "Qualitative": ["qualitative", "thematic analysis", "grounded theory", "phenomenolog"],
        "Mixed":       ["mixed method", "mixed-method", "qual-quant"],
        "Secondary":   ["secondary data", "existing data", "archival", "secondary sources"],
        "Meta":        ["meta-analysis", "systematic review", "prisma"],
        "Case":        ["case study", "case-study"],
    }
    for method, keywords in methodologies.items():
        if any(kw.lower() in text for kw in keywords):
            result.methodology = method
            result.info.append(f"Methodology detected: {method}")
            break

    # ── Questionnaire add-on ───────────────────────────────
    if any(kw in text for kw in ["questionnaire", "survey instrument", "likert scale design"]):
        result.addons["questionnaire"] = ADDON_COSTS["questionnaire"]
        result.warnings.append(
            "💳 Questionnaire design detected. This costs +1.0 credit. "
            "Includes: instrument design, item pool, reliability check."
        )

    # ── CSV dataset ────────────────────────────────────────
    if any(kw in text for kw in ["csv", "dataset", "raw data", "spss file", "data file"]):
        result.addons["csv_dataset"] = ADDON_COSTS["csv_dataset"]
        result.info.append("💳 Dataset CSV: +0.5 credits (included by default at checkout)")

    # ── Stats tier check ───────────────────────────────────
    for stat in ADVANCED_STATS:
        if stat.lower() in text:
            if tier not in ("Advanced", "Premium", "Ultra"):
                result.warnings.append(
                    f"⚠️ '{stat}' requires Advanced tier (₹5,000). "
                    f"Your tier is {tier}. Upgrade or remove this requirement."
                )
            result.specific_tests.append(stat)

    for stat in MEDIUM_STATS:
        if stat.lower() in text:
            if tier == "Basic":
                result.warnings.append(
                    f"⚠️ '{stat}' is recommended at Medium tier or above. "
                    f"Results may be limited at Basic tier."
                )
            result.specific_tests.append(stat)

    # ── Contradiction checks ───────────────────────────────
    for rule in CONTRADICTIONS:
        has_a = any(t.lower() in text for t in rule["triggers_a"])
        has_b = any(t.lower() in text for t in rule["triggers_b"])
        if has_a and has_b:
            result.warnings.append(
                f"⚠️ Contradiction detected: {rule['message']} "
                f"You may proceed — consumer is king — but reviewers may flag this."
            )

    # ── Domain mismatch (if methodology conflicts with common sense) ──
    if result.methodology == "Meta" and result.n_sample and result.n_sample < 10:
        result.warnings.append(
            "⚠️ Meta-analysis typically requires 10+ studies. "
            f"You specified N={result.n_sample}. This may not meet journal requirements."
        )

    # ── Formatting style detection ─────────────────────────
    for style_key in FORMATTING_STYLES:
        if style_key.lower() in text:
            result.formatting_style = style_key
            result.info.append(f"Formatting style: {FORMATTING_STYLES[style_key]['name']}")
            break

    # ── Line spacing ───────────────────────────────────────
    spacing_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:line\s+)?spacing', instructions, re.IGNORECASE)
    if spacing_m:
        sp_val = float(spacing_m.group(1))
        if 1.0 <= sp_val <= 3.0:
            result.line_spacing = sp_val

    return result


def _next_tier(tier: str) -> Optional[str]:
    tiers = ["Basic", "Medium", "Advanced", "Premium", "Ultra"]
    try:
        idx = tiers.index(tier)
        return tiers[idx + 1] if idx < len(tiers) - 1 else None
    except ValueError:
        return None


def format_validation_report(parsed: ParsedInstructions) -> str:
    """Format a clean validation report for display."""
    lines = []
    if parsed.info:
        lines.append("**What we found in your instructions:**")
        for item in parsed.info:
            lines.append(f"✅ {item}")
    if parsed.warnings:
        lines.append("\n**Warnings (you may proceed — your choice):**")
        for w in parsed.warnings:
            lines.append(w)
    if parsed.addons:
        total = sum(parsed.addons.values())
        lines.append(f"\n**Add-on costs: +{total} credits**")
        for name, cost in parsed.addons.items():
            lines.append(f"  • {name.replace('_',' ').title()}: +{cost} credits")
    return "\n".join(lines)
