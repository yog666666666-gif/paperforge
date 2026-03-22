"""
citation_engine.py — Phase A / B / C Zero-Hallucination Pipeline
=================================================================
Phase A: Fetch-first from Semantic Scholar → OpenAlex → CrossRef cascade
Phase B: Inject bank into prompts. Claude only cites from bank.
Phase C: CrossRef verify every citation before download.
"""

import json, re, time, difflib, urllib.request, urllib.parse
from typing import List, Dict, Optional, Tuple


# ══════════════════════════════════════════════════════════
# PHASE A — Pre-fetch real papers
# ══════════════════════════════════════════════════════════

def fetch_citation_bank(queries: List[str], target: int = 15,
                         ss_key: str = None) -> List[Dict]:
    """
    Cascade: Semantic Scholar → OpenAlex → CrossRef.
    Returns deduplicated list of real papers with DOIs.
    """
    bank = []
    seen_titles = set()

    for query in queries[:4]:
        papers = _semantic_scholar(query, limit=8, api_key=ss_key)
        if len(papers) < 3:
            papers += _open_alex(query, limit=8)
        if len(papers) < 3:
            papers += _crossref_search(query, limit=5)

        for p in papers:
            title_key = p.get("title", "")[:60].lower().strip()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                bank.append(p)

        if len(bank) >= target:
            break

    return bank[:target]


def _semantic_scholar(query: str, limit: int = 8,
                       api_key: str = None) -> List[Dict]:
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query, "limit": limit,
            "fields": "title,authors,year,externalIds,venue,abstract,citationCount"
        }
        full_url = url + "?" + urllib.parse.urlencode(params)
        headers = {"User-Agent": "PaperForge/1.0"}
        if api_key:
            headers["x-api-key"] = api_key
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        papers = []
        for item in data.get("data", []):
            doi = (item.get("externalIds") or {}).get("DOI", "")
            papers.append({
                "title":   item.get("title", ""),
                "authors": [a.get("name","") for a in (item.get("authors") or [])[:4]],
                "year":    item.get("year") or 0,
                "doi":     doi,
                "venue":   item.get("venue", ""),
                "abstract": (item.get("abstract") or "")[:300],
                "source":  "semantic_scholar",
                "verified": False,
            })
        return papers
    except Exception as e:
        print(f"[SemanticScholar] {e}")
        return []


def _open_alex(query: str, limit: int = 8) -> List[Dict]:
    try:
        params = {"search": query, "per-page": limit,
                  "select": "title,authorships,publication_year,doi,host_venue,abstract_inverted_index"}
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "PaperForge/1.0",
                                                    "mailto": "paperforge@example.com"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        papers = []
        for item in data.get("results", []):
            doi = (item.get("doi") or "").replace("https://doi.org/", "")
            authors = []
            for a in (item.get("authorships") or [])[:4]:
                name = (a.get("author") or {}).get("display_name", "")
                if name:
                    authors.append(name)
            papers.append({
                "title":   item.get("title", ""),
                "authors": authors,
                "year":    item.get("publication_year") or 0,
                "doi":     doi,
                "venue":   (item.get("host_venue") or {}).get("display_name", ""),
                "abstract": "",
                "source":  "openalex",
                "verified": False,
            })
        return papers
    except Exception as e:
        print(f"[OpenAlex] {e}")
        return []


def _crossref_search(query: str, limit: int = 5) -> List[Dict]:
    try:
        params = {"query": query[:120], "rows": limit,
                  "mailto": "paperforge@example.com"}
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "PaperForge/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        papers = []
        for item in (data.get("message") or {}).get("items", []):
            title_list = item.get("title") or [""]
            title = title_list[0] if title_list else ""
            authors_raw = item.get("author") or []
            authors = []
            for a in authors_raw[:4]:
                name = f"{a.get('given','')} {a.get('family','')}".strip()
                if name:
                    authors.append(name)
            year_parts = (item.get("published-print") or item.get("published-online") or {})
            year = 0
            dp = year_parts.get("date-parts", [[]])
            if dp and dp[0]:
                year = dp[0][0]
            doi = item.get("DOI", "")
            venue = (item.get("container-title") or [""])[0]
            papers.append({
                "title":   title,
                "authors": authors,
                "year":    year,
                "doi":     doi,
                "venue":   venue,
                "abstract": "",
                "source":  "crossref",
                "verified": False,
            })
        return papers
    except Exception as e:
        print(f"[CrossRef] {e}")
        return []


# ══════════════════════════════════════════════════════════
# PHASE B — Citation discipline enforcement
# ══════════════════════════════════════════════════════════

def enforce_citation_discipline(text: str, bank: List[Dict],
                                  threshold: float = 0.50) -> Tuple[str, int]:
    """
    Scan text for (Author, Year) patterns.
    If not in bank → silently remove the citation.
    Returns (cleaned_text, num_removed).
    """
    pattern = re.compile(r'\(([A-Z][a-zA-Z\-\']+(?:\s+et\s+al\.?)?),?\s+(\d{4}[a-z]?)\)')
    removed = 0

    def check_and_replace(match):
        nonlocal removed
        cited_surname = match.group(1).split()[0].lower()
        cited_year    = int(re.sub(r'[a-z]', '', match.group(2)))
        for paper in bank:
            if not paper.get("authors"):
                continue
            first_author = paper["authors"][0].split()[-1].lower()
            year = paper.get("year", 0) or 0
            name_sim = difflib.SequenceMatcher(None, cited_surname, first_author).ratio()
            if name_sim >= threshold and abs(cited_year - year) <= 1:
                return match.group(0)  # keep
        removed += 1
        return ""  # strip ghost citation

    cleaned = pattern.sub(check_and_replace, text)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\s+([,;.])', r'\1', cleaned)
    return cleaned, removed


# ══════════════════════════════════════════════════════════
# PHASE C — CrossRef verification before download
# ══════════════════════════════════════════════════════════

def verify_citation_crossref(paper: Dict) -> bool:
    """
    Verify a paper against CrossRef.
    70% title similarity + year within 3 years → verified.
    """
    title = paper.get("title", "")
    year  = paper.get("year", 0) or 0
    if not title:
        return False
    try:
        time.sleep(0.2)  # CrossRef rate limit
        encoded = urllib.parse.quote(title[:120])
        url = (f"https://api.crossref.org/works?query.title={encoded}"
               f"&rows=3&mailto=paperforge@example.com")
        req = urllib.request.Request(url, headers={"User-Agent": "PaperForge/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        for item in (data.get("message") or {}).get("items", [])[:3]:
            item_title = ((item.get("title") or [""])[0]).lower()
            ratio = difflib.SequenceMatcher(None, title.lower()[:80],
                                             item_title[:80]).ratio()
            item_year = 0
            dp = (item.get("published-print") or item.get("published-online") or {}).get("date-parts", [[]])
            if dp and dp[0]:
                item_year = dp[0][0]
            if ratio >= 0.70 and abs((year or 0) - item_year) <= 3:
                if not paper.get("doi") and item.get("DOI"):
                    paper["doi"] = item["DOI"]
                return True
    except Exception:
        pass
    return False


def verify_bank_phase_c(bank: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Run Phase C on all papers in bank.
    Returns (verified_papers, num_stripped).
    """
    verified, stripped = [], 0
    for paper in bank:
        if paper.get("doi"):
            paper["verified"] = True
            verified.append(paper)
        elif verify_citation_crossref(paper):
            paper["verified"] = True
            verified.append(paper)
        else:
            stripped += 1
    return verified, stripped


# ══════════════════════════════════════════════════════════
# FORMATTING
# ══════════════════════════════════════════════════════════

def format_citation(paper: Dict, style: str = "APA") -> str:
    authors = paper.get("authors", [])
    author_str = ""
    if authors:
        names = authors[:3]
        author_str = ", ".join(names)
        if len(authors) > 3:
            author_str += ", et al."
    year  = paper.get("year", "n.d.")
    title = paper.get("title", "Unknown title")
    venue = paper.get("venue", "")
    doi   = paper.get("doi", "")
    doi_str = f" https://doi.org/{doi}" if doi else ""

    if style == "APA":
        return f"{author_str} ({year}). {title}. *{venue}*.{doi_str}"
    if style == "Vancouver":
        return f"{author_str}. {title}. {venue}. {year}.{doi_str}"
    if style == "MLA":
        return f'{author_str}. "{title}." {venue}, {year}.{doi_str}'
    return f"{author_str} ({year}). {title}. {venue}.{doi_str}"


def bank_to_prompt_text(bank: List[Dict], style: str = "APA") -> str:
    """Format bank as numbered list for injection into prompts."""
    lines = []
    for i, p in enumerate(bank, 1):
        lines.append(f"[{i}] {format_citation(p, style)}")
    return "\n".join(lines)
