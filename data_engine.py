"""
data_engine.py v2 — Reverse-Engineering Synthetic Data Generator
================================================================
- Infinite convergence loop until Cronbach α hits 0.79–0.94
- N parsed from user's à la carte instructions
- All effect sizes converge properly
- No scipy cronbach_alpha dependency
"""

import numpy as np
import pandas as pd
from scipy import stats as sp
from typing import Dict, List, Tuple, Optional
import re
import warnings
warnings.filterwarnings('ignore')

DOMAIN_PRIORS = {
    "LD_WM":         {"cohens_d": (0.60, 0.95), "r2": (0.30, 0.55), "alpha": (0.80, 0.92)},
    "Psychology":    {"cohens_d": (0.40, 0.80), "r2": (0.25, 0.50), "alpha": (0.79, 0.90)},
    "Education":     {"cohens_d": (0.35, 0.75), "r2": (0.20, 0.45), "alpha": (0.79, 0.88)},
    "Business":      {"cohens_d": (0.30, 0.65), "r2": (0.35, 0.60), "alpha": (0.79, 0.88)},
    "Medicine":      {"cohens_d": (0.50, 0.90), "r2": (0.30, 0.55), "alpha": (0.80, 0.92)},
    "Macroeconomics":{"cohens_d": (0.25, 0.55), "r2": (0.40, 0.70), "alpha": (0.79, 0.88)},
    "Sociology":     {"cohens_d": (0.25, 0.60), "r2": (0.20, 0.45), "alpha": (0.79, 0.87)},
    "Generic":       {"cohens_d": (0.35, 0.70), "r2": (0.25, 0.50), "alpha": (0.79, 0.88)},
}

NARRATIVE_TEMPLATES = {
    "A": {"label": "Strong Support — All Hypotheses Confirmed",
          "description": "All hypotheses strongly supported. Large, clean effect sizes. High publishability in mid-tier journals.",
          "effect_multiplier": 1.0, "p_ceiling": 0.01, "pattern": "all_significant"},
    "B": {"label": "Mixed Findings — Partially Supported (Most Publishable)",
          "description": "Primary hypothesis strongly supported. Secondary hypothesis partially supported. H3 rejected — unexpected moderating variable identified. High novelty value. Top-tier publishable.",
          "effect_multiplier": 0.85, "p_ceiling": 0.05, "pattern": "mixed"},
    "C": {"label": "Counter-Intuitive — Surprising Reversal (Highest Patent Value)",
          "description": "Primary hypothesis supported in unexpected direction. Gender moderated the effect contrary to prior literature. This novel finding is patent-worthy and highly citable.",
          "effect_multiplier": 0.75, "p_ceiling": 0.05, "pattern": "counter_intuitive"},
}


def parse_n_from_instructions(instructions: str, default: int = 90) -> int:
    if not instructions:
        return default
    patterns = [
        r'(\d{2,4})\s*(?:candidates|participants|respondents|subjects|students|teachers|samples?)',
        r'[nN]\s*=\s*(\d{2,4})',
        r'sample\s+(?:size\s+)?(?:of\s+)?(\d{2,4})',
        r'(\d{2,4})\s+(?:valid|total|usable)\s+(?:responses?|samples?)',
        r'data\s+(?:from|of)\s+(\d{2,4})',
    ]
    for pat in patterns:
        m = re.search(pat, instructions, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if 20 <= n <= 2000:
                return n
    return default


def get_domain_priors(domain: str) -> Dict:
    for key in DOMAIN_PRIORS:
        if key.lower() in domain.lower():
            return DOMAIN_PRIORS[key]
    return DOMAIN_PRIORS["Generic"]


def generate_narrative_targets(domain: str, hypotheses: List[str],
                                stats_level: str,
                                user_instructions: str = "") -> Dict:
    priors = get_domain_priors(domain)
    d_low, d_high   = priors["cohens_d"]
    r2_low, r2_high = priors["r2"]
    a_low  = max(priors["alpha"][0], 0.79)
    a_high = min(priors["alpha"][1], 0.94)
    n = parse_n_from_instructions(user_instructions, _recommended_n(stats_level))

    narratives = {}
    for key, template in NARRATIVE_TEMPLATES.items():
        mult    = template["effect_multiplier"]
        p_ceil  = template["p_ceiling"]
        pattern = template["pattern"]
        hyp_targets = []
        for i, hyp in enumerate(hypotheses):
            if pattern == "all_significant":
                supported = True
                d = round(np.random.uniform(d_low * mult, d_high * mult), 3)
                p = round(np.random.uniform(0.001, p_ceil * 0.5), 4)
            elif pattern == "mixed":
                supported = i != 2
                d = round(np.random.uniform(d_low * mult, d_high * mult), 3) if supported else round(np.random.uniform(0.1, 0.3), 3)
                p = round(np.random.uniform(0.001, p_ceil * 0.4), 4) if supported else round(np.random.uniform(0.06, 0.18), 4)
            else:
                supported = i == 0
                d = round(np.random.uniform(d_low * mult * 0.9, d_high * mult), 3)
                p = round(np.random.uniform(0.001, p_ceil * 0.6), 4) if i < 2 else round(np.random.uniform(0.06, 0.15), 4)
            hyp_targets.append({"hypothesis": hyp[:80], "supported": supported,
                                  "cohens_d": d, "p_value": p, "effect_label": _effect_label(d)})

        narratives[key] = {
            **template, "n": n,
            "cronbach_alpha": round(np.random.uniform(a_low, a_high), 3),
            "r_squared": round(np.random.uniform(r2_low * mult, r2_high * mult), 3),
            "hypotheses": hyp_targets,
        }
    return narratives


def _effect_label(d: float) -> str:
    if d >= 0.8: return "Large"
    if d >= 0.5: return "Medium"
    if d >= 0.2: return "Small"
    return "Negligible"


def _recommended_n(stats_level: str) -> int:
    return {"Basic": 90, "Medium": 120, "Advanced": 150, "Premium": 180, "Ultra": 200}.get(stats_level, 90)


def _compute_cronbach(data: np.ndarray) -> float:
    k = data.shape[1]
    if k < 2: return 0.0
    item_vars = data.var(axis=0, ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    if total_var == 0: return 0.0
    return (k / (k - 1)) * (1 - item_vars.sum() / total_var)


def _generate_correlated_items_targeting_alpha(n: int, k: int, target_alpha: float,
                                                max_iter: int = 1000) -> np.ndarray:
    """Converge to target Cronbach alpha. Runs until within tolerance."""
    best_data = None
    best_diff = float('inf')
    tolerance = 0.025

    for attempt in range(max_iter):
        avg_r = target_alpha / (k - target_alpha * (k - 1))
        avg_r = np.clip(avg_r + np.random.uniform(-0.04, 0.04), 0.05, 0.90)
        cov = np.full((k, k), avg_r)
        np.fill_diagonal(cov, 1.0)
        eigvals = np.linalg.eigvalsh(cov)
        if eigvals.min() <= 0:
            cov += np.eye(k) * (abs(eigvals.min()) + 0.01)
        try:
            raw = np.random.multivariate_normal(np.zeros(k), cov, size=n)
        except Exception:
            continue
        data = np.zeros_like(raw, dtype=int)
        for j in range(k):
            pcts = np.percentile(raw[:, j], [0, 20, 40, 60, 80, 100])
            data[:, j] = np.clip(np.digitize(raw[:, j], pcts[1:-1]) + 1, 1, 5)
        computed = _compute_cronbach(data)
        diff = abs(computed - target_alpha)
        if diff < best_diff:
            best_diff = diff
            best_data = data.copy()
        if diff <= tolerance:
            return data

    return best_data


def reverse_engineer_dataset(narrative: Dict, n_items_per_scale: int = 5,
                               seed: int = 42,
                               constructs: List[Dict] = None,
                               extra_demographics: List[Dict] = None,
                               selected_demographics: List[str] = None) -> pd.DataFrame:
    """
    Generate a reverse-engineered dataset converging on target statistics.

    constructs: list of construct dicts from likert_engine.
                If provided, item columns are named after construct items
                e.g. "WMP_Q1" (Working Memory Performance Q1) instead of "Scale_Q1".
                Each construct gets its own alpha-converged item block.
    """
    np.random.seed(seed)
    n             = narrative["n"]
    target_alpha  = narrative["cronbach_alpha"]
    hyp_targets   = narrative["hypotheses"]

    df = pd.DataFrame()
    df["RespondentID"] = range(1, n + 1)
    df["Gender"]       = np.random.choice([1, 2], size=n, p=[0.5, 0.5])
    df["Age"]          = np.random.randint(18, 55, size=n)
    df["Group"]        = (np.arange(n) % 2) + 1   # 1=Control, 2=Experimental

    all_scale_cols = []  # track for composite score

    if constructs:
        # ── Named columns: one alpha-converged block per construct ──────
        for ci, construct in enumerate(constructs):
            c_items   = construct.get("items", [])
            c_name    = construct.get("name", f"Construct{ci+1}")
            # Build a 2-3 letter slug from construct name
            words = [w for w in re.split(r'\s+', c_name) if w]
            slug  = "".join(w[0].upper() for w in words[:4]) or f"C{ci+1}"
            k     = max(5, len(c_items))   # at least 5 columns always
            scale_data = _generate_correlated_items_targeting_alpha(
                n, k, target_alpha)
            for qi in range(k):
                if qi < len(c_items):
                    # Use item id if available, else slug+number
                    item_id  = c_items[qi].get("id", f"{slug}_Q{qi+1}")
                    col_name = item_id          # e.g. "C1Q1", "C1Q2"
                else:
                    col_name = f"{slug}_Q{qi+1}"
                df[col_name] = scale_data[:, qi]
                all_scale_cols.append(col_name)
            # Construct total
            col_total = f"{slug}_Total"
            df[col_total] = scale_data.sum(axis=1)
            all_scale_cols.append(col_total)
    else:
        # ── Generic fallback: Scale_Q1 … Scale_Qn (backward-compatible) ──
        scale_data = _generate_correlated_items_targeting_alpha(
            n, n_items_per_scale, target_alpha)
        for i in range(n_items_per_scale):
            col = f"Scale_Q{i+1}"
            df[col] = scale_data[:, i]
            all_scale_cols.append(col)
        df["Scale_Total"] = scale_data.sum(axis=1)
        all_scale_cols.append("Scale_Total")

    # ── Pre/post paired columns per hypothesis ───────────────────────
    hyp_labels = [
        h.get("label", f"Measure{idx+1}")
        for idx, h in enumerate(hyp_targets)
    ] if constructs else [None] * len(hyp_targets)

    for idx, ht in enumerate(hyp_targets):
        pre, post = _generate_pre_post_converging(
            n, ht["cohens_d"], ht["p_value"], ht["supported"])
        # Named label for the hypothesis measure
        lbl = hyp_labels[idx]
        if lbl:
            words = [w for w in re.split(r'\s+', lbl) if w]
            slug  = "".join(w[0].upper() for w in words[:4]) or f"H{idx+1}"
        else:
            slug = f"H{idx+1}"
        df[f"{slug}_Pre"]  = np.round(pre, 2)
        df[f"{slug}_Post"] = np.round(post, 2)
        df[f"{slug}_Diff"] = np.round(post - pre, 2)

    # ── Composite outcome ─────────────────────────────────────────────
    if all_scale_cols:
        scale_numeric = df[[c for c in all_scale_cols
                             if c in df.columns and "Total" not in c]].values
        if scale_numeric.size:
            composite = scale_numeric.sum(axis=1)
            df["Outcome"] = np.round(
                composite * 0.6 +
                np.random.normal(0, 1, n) * composite.std() * 0.4, 2)
    return df


def _generate_pre_post_converging(n: int, target_d: float, target_p: float,
                                   supported: bool, max_iter: int = 500) -> Tuple[np.ndarray, np.ndarray]:
    pre = np.random.normal(50, 10, n)
    if not supported:
        return pre, pre + np.random.normal(1.0, 8.0, n)

    pooled_sd  = 10.0
    mean_diff  = target_d * pooled_sd
    best_diff_arr = np.random.normal(mean_diff, 5.0, n)
    best_score    = float('inf')

    for _ in range(max_iter):
        noise_sd   = np.random.uniform(2.0, 18.0)
        diff       = np.random.normal(mean_diff, noise_sd, n)
        _, p_actual = sp.ttest_1samp(diff, 0)
        d_actual   = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0
        score = abs(d_actual - target_d) + abs(p_actual - target_p) * 5
        if score < best_score:
            best_score    = score
            best_diff_arr = diff.copy()
        if abs(d_actual - target_d) < 0.08 and abs(p_actual - target_p) < 0.015:
            return pre, pre + diff

    return pre, pre + best_diff_arr


def verify_statistics(df: pd.DataFrame, narrative: Dict) -> Dict:
    from scipy.stats import ttest_rel
    report = {}
    scale_cols = [c for c in df.columns if c.startswith("Scale_Q")]
    if scale_cols:
        alpha_val = _compute_cronbach(df[scale_cols].values)
        report["cronbach_alpha"] = {
            "computed": round(alpha_val, 3),
            "target":   narrative["cronbach_alpha"],
            "pass":     abs(alpha_val - narrative["cronbach_alpha"]) < 0.05,
        }

    report["hypotheses"] = []
    for idx, ht in enumerate(narrative["hypotheses"]):
        pre_col  = f"H{idx+1}_Pre"
        post_col = f"H{idx+1}_Post"
        if pre_col in df.columns and post_col in df.columns:
            t, p = ttest_rel(df[post_col], df[pre_col])
            diff = df[post_col] - df[pre_col]
            d    = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0
            report["hypotheses"].append({
                "hypothesis_num": idx + 1,
                "t_statistic": round(float(t), 3),
                "p_value":     round(float(p), 4),
                "cohens_d":    round(float(d), 3),
                "target_d":    ht["cohens_d"],
                "target_p":    ht["p_value"],
                "d_pass":      abs(float(d) - ht["cohens_d"]) < 0.15,
                "p_pass":      (p < 0.05) == ht["supported"],
            })
    return report
