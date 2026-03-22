"""
conference_matcher.py — Conference Theme Matching Engine
=========================================================
MUSTEST: Must match conference themes to user domain.
AI suggests closest subtheme match.
User can override with custom title.
"""

import re
import json
from typing import Dict, List, Optional, Tuple


def extract_conference_themes(conference_text: str) -> Dict:
    """
    Extract themes, subthemes, word limits, formatting rules
    from conference brochure text.
    """
    result = {
        "conference_name": "",
        "themes":          [],
        "subthemes":       [],
        "word_limit":      None,
        "abstract_limit":  None,
        "font":            None,
        "font_size":       None,
        "spacing":         None,
        "citation_style":  None,
        "submission_email":"",
        "deadline":        "",
        "raw_rules":       [],
    }

    text = conference_text.lower()

    # Conference name
    name_m = re.search(r'(?:national|international|annual)[\w\s]+(?:seminar|conference|symposium|workshop)',
                        conference_text, re.IGNORECASE)
    if name_m:
        result["conference_name"] = name_m.group(0).strip()

    # Word limits
    wl_m = re.search(r'(?:word\s+limit|maximum\s+words?|not\s+exceed)\s*[:\-]?\s*(\d{3,5})',
                      text, re.IGNORECASE)
    if wl_m:
        result["word_limit"] = int(wl_m.group(1))

    # Abstract limit
    abs_m = re.search(r'abstract\s*[:\-]?\s*(\d{2,4})\s*words?', text, re.IGNORECASE)
    if abs_m:
        result["abstract_limit"] = int(abs_m.group(1))

    # Font
    if 'times new roman' in text:
        result["font"] = "Times New Roman"
    elif 'arial' in text:
        result["font"] = "Arial"
    elif 'calibri' in text:
        result["font"] = "Calibri"

    # Font size
    fs_m = re.search(r'font\s+size\s*[:\-]?\s*(\d{1,2})\s*(?:pt|point)?', text, re.IGNORECASE)
    if fs_m:
        result["font_size"] = int(fs_m.group(1))

    # Spacing
    if '1.5' in text and 'spacing' in text:
        result["spacing"] = 1.5
    elif 'double' in text and 'spacing' in text:
        result["spacing"] = 2.0
    elif 'single' in text and 'spacing' in text:
        result["spacing"] = 1.0

    # Citation style
    for style in ['APA', 'MLA', 'Chicago', 'Vancouver', 'IEEE', 'Harvard']:
        if style.lower() in text:
            result["citation_style"] = style
            break

    # Email
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', conference_text)
    if email_m:
        result["submission_email"] = email_m.group(0)

    # Extract themes/subthemes
    theme_patterns = [
        r'(?:theme|track|sub.?theme|topic)\s*\d*\s*[:\-]\s*(.+?)(?:\n|$)',
        r'^\d+\.\s+(.{10,80})$',
    ]
    themes = []
    for pat in theme_patterns:
        matches = re.findall(pat, conference_text, re.MULTILINE | re.IGNORECASE)
        themes.extend([m.strip() for m in matches if len(m.strip()) > 10])

    result["themes"]    = list(set(themes[:15]))
    result["subthemes"] = themes[15:30] if len(themes) > 15 else []

    return result


def match_domain_to_themes(domain: str, topic: str,
                             themes: List[str]) -> List[Dict]:
    """
    Match user's domain and topic to conference themes.
    Returns ranked matches with confidence scores.
    """
    if not themes:
        return []

    domain_lower = domain.lower()
    topic_lower  = topic.lower()

    matches = []
    for theme in themes:
        theme_lower = theme.lower()
        score = 0

        # Word overlap scoring
        domain_words = set(re.findall(r'\w+', domain_lower))
        topic_words  = set(re.findall(r'\w+', topic_lower))
        theme_words  = set(re.findall(r'\w+', theme_lower))

        domain_overlap = len(domain_words & theme_words)
        topic_overlap  = len(topic_words & theme_words)
        score = domain_overlap * 2 + topic_overlap

        # Keyword bonuses
        bonus_pairs = [
            (['education', 'learning', 'teaching'], ['education', 'pedagogy', 'curriculum']),
            (['psychology', 'behavior', 'cognitive'], ['psychology', 'mental', 'cognition']),
            (['technology', 'ai', 'digital'], ['technology', 'innovation', 'digital']),
            (['health', 'medical', 'clinical'], ['health', 'medicine', 'clinical']),
            (['management', 'business', 'economics'], ['management', 'business', 'finance']),
        ]
        for domain_kws, theme_kws in bonus_pairs:
            if (any(kw in domain_lower for kw in domain_kws) and
                    any(kw in theme_lower for kw in theme_kws)):
                score += 3

        matches.append({
            "theme":      theme,
            "score":      score,
            "confidence": min(round(score / max(len(theme_words), 1) * 100, 0), 99),
        })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


def suggest_paper_title(domain: str, topic: str, matched_theme: str,
                         hypotheses: List[str]) -> List[str]:
    """Generate 3 title suggestions aligned with conference theme."""
    base_topic = topic[:60].strip()
    suggestions = [
        f"{base_topic}: A Study in the Context of {matched_theme}",
        f"Exploring {domain} Dimensions of {base_topic}",
        f"{base_topic}: Evidence from {matched_theme} Research",
    ]
    return suggestions
