"""
prompt_bank.py — Self-Evolving Prompt Bank
==========================================
15-20 paper type templates. Matched by AI. User overrides anything.
Evolves: positive feedback → template gets higher weight.
"""

import json, os, re
from typing import Dict, List, Optional, Tuple

BANK_FILE = "prompt_bank_state.json"

# ── Core templates ─────────────────────────────────────────
BASE_TEMPLATES = {
    "RCT_HealthScience": {
        "match_keywords": ["rct", "randomized", "clinical trial", "intervention", "health", "medicine", "treatment"],
        "mandatory_sections": ["Abstract", "Introduction", "Literature Review", "Methods", "Results", "Discussion", "Conclusion", "References"],
        "stats_basic":    ["Independent t-test", "Chi-square"],
        "stats_medium":   ["ANOVA", "Mann-Whitney U", "Cronbach's alpha"],
        "stats_advanced": ["Mixed ANOVA", "Effect sizes", "Post-hoc Bonferroni", "Power analysis"],
        "citation_density": 25,
        "tone": "formal",
        "abstract_structure": "Background/Aim/Methods/Results/Conclusion",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "LongitudinalSurvey_Psychology": {
        "match_keywords": ["longitudinal", "survey", "psychology", "behavior", "attitude", "scale", "questionnaire", "LD", "working memory"],
        "mandatory_sections": ["Abstract", "Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Implications", "References"],
        "stats_basic":    ["Paired t-test", "Frequency analysis"],
        "stats_medium":   ["Repeated measures ANOVA", "Spearman correlation", "Cronbach's alpha"],
        "stats_advanced": ["SEM", "CFA", "Mediation analysis", "Bootstrap CI"],
        "citation_density": 30,
        "tone": "formal",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "MetaAnalysis_Education": {
        "match_keywords": ["meta-analysis", "systematic review", "effect size", "education", "learning"],
        "mandatory_sections": ["Abstract", "Introduction", "Search Strategy", "Inclusion Criteria", "Results", "Heterogeneity", "Discussion", "References"],
        "stats_basic":    ["Effect size calculation", "Forest plot description"],
        "stats_medium":   ["Funnel plot", "Heterogeneity (I²)", "Random effects model"],
        "stats_advanced": ["Moderator analysis", "Publication bias (Egger's)", "Trim-and-fill"],
        "citation_density": 40,
        "tone": "technical",
        "abstract_structure": "Background/Objectives/Methods/Results/Conclusions",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "CaseStudy_Business": {
        "match_keywords": ["case study", "business", "management", "organization", "company", "strategy", "MBA"],
        "mandatory_sections": ["Abstract", "Introduction", "Background", "Analysis", "Findings", "Discussion", "Recommendations", "References"],
        "stats_basic":    ["Descriptive statistics", "Frequency analysis"],
        "stats_medium":   ["Correlation", "Regression", "SWOT analysis"],
        "stats_advanced": ["SEM", "Multiple regression", "VIF"],
        "citation_density": 20,
        "tone": "semi-formal",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "ExperimentalDesign_CogSci": {
        "match_keywords": ["experiment", "cognitive", "neuroscience", "brain", "memory", "attention", "perception"],
        "mandatory_sections": ["Abstract", "Introduction", "Hypotheses", "Methods", "Results", "Discussion", "References"],
        "stats_basic":    ["Independent t-test", "Paired t-test"],
        "stats_medium":   ["ANOVA", "Post-hoc", "Effect sizes"],
        "stats_advanced": ["Mixed-effects model", "Bootstrap CI", "Bayesian analysis"],
        "citation_density": 28,
        "tone": "technical",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "PolicyBrief_Economics": {
        "match_keywords": ["policy", "economics", "macro", "GDP", "inflation", "government", "fiscal", "monetary"],
        "mandatory_sections": ["Executive Summary", "Background", "Problem Statement", "Evidence", "Policy Options", "Recommendations", "References"],
        "stats_basic":    ["Descriptive statistics", "Time-series description"],
        "stats_medium":   ["Regression", "Correlation", "Index construction"],
        "stats_advanced": ["VAR model", "Cointegration", "VECM", "Granger causality"],
        "citation_density": 20,
        "tone": "accessible",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "SystematicReview_Medicine": {
        "match_keywords": ["systematic review", "prisma", "cochrane", "clinical", "treatment", "diagnosis", "medical"],
        "mandatory_sections": ["Abstract", "Introduction", "Methods", "Search Strategy", "Results", "Discussion", "Conclusion", "References"],
        "stats_basic":    ["Descriptive statistics", "Risk ratios"],
        "stats_medium":   ["Forest plot", "Odds ratio", "NNT"],
        "stats_advanced": ["Network meta-analysis", "GRADE assessment", "Sensitivity analysis"],
        "citation_density": 45,
        "tone": "technical",
        "abstract_structure": "Background/Methods/Results/Conclusions",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "CorrelationalStudy_Sociology": {
        "match_keywords": ["sociology", "social", "community", "gender", "inequality", "culture", "demographic"],
        "mandatory_sections": ["Abstract", "Introduction", "Theoretical Framework", "Methodology", "Results", "Discussion", "Conclusion", "References"],
        "stats_basic":    ["Frequency analysis", "Chi-square", "Spearman correlation"],
        "stats_medium":   ["Logistic regression", "Kruskal-Wallis", "Effect sizes"],
        "stats_advanced": ["Multilevel modeling", "SEM", "Mediation"],
        "citation_density": 25,
        "tone": "formal",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "GeographySpatialAnalysis": {
        "match_keywords": ["geography", "spatial", "GIS", "mapping", "region", "urban", "rural", "land use"],
        "mandatory_sections": ["Abstract", "Introduction", "Study Area", "Data and Methods", "Results", "Discussion", "Conclusion", "References"],
        "stats_basic":    ["Descriptive statistics", "Frequency analysis"],
        "stats_medium":   ["Spatial correlation", "Regression", "ANOVA"],
        "stats_advanced": ["Spatial autocorrelation (Moran's I)", "GWR", "Kriging"],
        "citation_density": 22,
        "tone": "technical",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "LegalDoctrinalAnalysis": {
        "match_keywords": ["legal", "law", "doctrine", "jurisprudence", "court", "statute", "constitutional"],
        "mandatory_sections": ["Abstract", "Introduction", "Legal Framework", "Analysis", "Case Review", "Discussion", "Conclusion", "References"],
        "stats_basic":    [],
        "stats_medium":   [],
        "stats_advanced": [],
        "citation_density": 30,
        "tone": "formal",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
        "citation_format_override": "legal_bluebook",
    },
    "ComputerScience_Engineering": {
        "match_keywords": ["algorithm", "machine learning", "AI", "deep learning", "neural", "software", "system", "architecture"],
        "mandatory_sections": ["Abstract", "Introduction", "Related Work", "Methodology", "Implementation", "Results", "Conclusion", "References"],
        "stats_basic":    ["Accuracy", "Precision", "Recall"],
        "stats_medium":   ["F1-score", "ROC-AUC", "Confusion matrix"],
        "stats_advanced": ["Statistical significance testing", "Effect sizes", "Ablation study"],
        "citation_density": 25,
        "tone": "technical",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
    "Generic_IMRaD": {
        "match_keywords": [],  # fallback — matches everything
        "mandatory_sections": ["Abstract", "Introduction", "Literature Review", "Methods", "Results", "Discussion", "Conclusion", "References"],
        "stats_basic":    ["Descriptive statistics", "t-test", "Chi-square"],
        "stats_medium":   ["ANOVA", "Correlation", "Regression"],
        "stats_advanced": ["SEM", "CFA", "Bootstrap CI", "Effect sizes"],
        "citation_density": 20,
        "tone": "formal",
        "abstract_structure": "unstructured",
        "forbidden_sections": [],
        "first_person": False,
        "weight": 1.0,
    },
}


class PromptBank:
    def __init__(self):
        self.templates = self._load()

    def _load(self) -> Dict:
        if os.path.exists(BANK_FILE):
            try:
                with open(BANK_FILE) as f:
                    saved = json.load(f)
                # Merge saved weights with base templates
                for key, tmpl in BASE_TEMPLATES.items():
                    if key in saved:
                        tmpl["weight"] = saved[key].get("weight", 1.0)
                return dict(BASE_TEMPLATES)
            except Exception:
                pass
        return dict(BASE_TEMPLATES)

    def _save(self):
        try:
            state = {k: {"weight": v["weight"]} for k, v in self.templates.items()}
            with open(BANK_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def match(self, topic: str, domain: str = "") -> Tuple[str, Dict]:
        """Match topic/domain to best template. Returns (key, template)."""
        combined = f"{topic} {domain}".lower()
        scores = {}
        for key, tmpl in self.templates.items():
            score = tmpl["weight"]
            for kw in tmpl.get("match_keywords", []):
                if kw.lower() in combined:
                    score += 2.0
            scores[key] = score

        best_key = max(scores, key=scores.get)
        # Always fall back to Generic if score is too low
        if scores[best_key] <= 1.0:
            best_key = "Generic_IMRaD"
        return best_key, self.templates[best_key]

    def positive_feedback(self, template_key: str):
        """User happy → increase template weight."""
        if template_key in self.templates:
            self.templates[template_key]["weight"] = min(
                5.0, self.templates[template_key]["weight"] + 0.1)
            self._save()

    def negative_feedback(self, template_key: str):
        """User unhappy → slightly decrease weight."""
        if template_key in self.templates:
            self.templates[template_key]["weight"] = max(
                0.5, self.templates[template_key]["weight"] - 0.05)
            self._save()

    def get_stats_for_level(self, template_key: str, level: str) -> List[str]:
        tmpl = self.templates.get(template_key, self.templates["Generic_IMRaD"])
        return tmpl.get(f"stats_{level.lower()}", tmpl["stats_basic"])

    def get_mandatory_sections(self, template_key: str) -> List[str]:
        return self.templates.get(template_key, self.templates["Generic_IMRaD"])["mandatory_sections"]

    def list_all(self) -> List[Dict]:
        return [{"key": k, "weight": v["weight"],
                 "keywords": v["match_keywords"][:5]}
                for k, v in self.templates.items()]


# ── Singleton ──────────────────────────────────────────────
_bank: Optional[PromptBank] = None

def get_bank() -> PromptBank:
    global _bank
    if _bank is None:
        _bank = PromptBank()
    return _bank
