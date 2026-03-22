"""
Shodhak — Research Intelligence and Patent Planning Tool
=========================================================
Sanskrit: Shodhak = Seeker, Investigator, One who purifies through inquiry

Tagline: "The research supervisor that 95% of Indian researchers never had."

What this is:
  - Research gap finder
  - Hypothesis generator
  - Statistical test selector
  - Patent novelty screener
  - Sample size calculator
  - Citation network mapper
  - Research proposal generator
  - Conceptual framework diagram builder
  - Domain data router (100 verified APIs)
  - Reviewer comment responder
  - Theory matcher

What this is NOT:
  - A paper writer
  - A thesis generator
  - A data fabricator
  - Anything that deceives an academic institution

Admin layer: Completely separate, password-protected, no public link.
"""

import streamlit as st
import os, json, re, uuid, time
import pandas as pd

# ── Module imports ──────────────────────────────────────────
from model_router    import call_prep, call_writer, call_audit, call_model
from citation_engine import (fetch_citation_bank, format_citation,
                              bank_to_prompt_text, enforce_citation_discipline)

try:
    from auth_engine        import render_auth_screen, render_user_badge
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

try:
    from diagram_engine     import generate_chart, decide_chart_type
    DIAGRAMS_AVAILABLE = True
except ImportError:
    DIAGRAMS_AVAILABLE = False

try:
    from domain_data_engine import fetch_domain_data, route_apis_for_domain
    DATA_ENGINE_AVAILABLE = True
except ImportError:
    DATA_ENGINE_AVAILABLE = False

try:
    from output_formatter   import build_professional_docx, clean_markdown
    FORMATTER_AVAILABLE = True
except ImportError:
    FORMATTER_AVAILABLE = False

try:
    from audit_pipeline     import clean_blocklist
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

# ══════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Shodhak — Research Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════
# VISUAL THEME — warm, scholarly, professional
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif;
    color: #1C1C1E;
}
.stApp { background: #FAFAF7; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F5F0E8 !important;
    border-right: 1px solid #E0D9CF;
}
[data-testid="stSidebar"] .stMarkdown { color: #3E2723; }

/* Module cards */
.module-card {
    background: #FFFFFF;
    border: 1px solid #E8E0D4;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin: 0.6rem 0;
    cursor: pointer;
    transition: all 0.15s;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.module-card:hover {
    border-color: #8B4513;
    box-shadow: 0 3px 12px rgba(139,69,19,0.12);
    transform: translateY(-1px);
}
.module-card.active {
    border-left: 4px solid #8B0000;
    background: #FFF8F5;
}
.module-icon { font-size: 22px; margin-bottom: 6px; }
.module-title {
    font-weight: 600;
    font-size: 14px;
    color: #1C1C1E;
    margin-bottom: 3px;
}
.module-desc { font-size: 12px; color: #8D6E63; line-height: 1.4; }

/* Page title */
.shodhak-title {
    font-family: 'Crimson Text', Georgia, serif;
    font-size: 32px;
    font-weight: 600;
    color: #3E2723;
    margin-bottom: 0;
    letter-spacing: -0.3px;
}
.shodhak-tagline {
    font-size: 14px;
    color: #8D6E63;
    font-style: italic;
    margin-top: 2px;
    margin-bottom: 1.5rem;
}

/* Result cards */
.result-card {
    background: #FFFFFF;
    border: 1px solid #E8E0D4;
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
}
.result-card h4 {
    color: #3E2723;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 8px;
    border-bottom: 1px solid #F0E8DC;
    padding-bottom: 6px;
}

/* Stat chips */
.stat-chip {
    display: inline-block;
    background: #F5F0E8;
    border: 1px solid #D6CFC4;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    color: #5D4037;
    margin: 3px 3px 3px 0;
    font-family: 'Courier New', monospace;
}

/* Zero hallucination badge */
.zero-hal {
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    color: #166534;
    display: inline-block;
    margin-bottom: 1rem;
}

/* Warning box */
.warn-box {
    background: #FFF8E7;
    border-left: 4px solid #D97706;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    margin: 0.6rem 0;
    font-size: 13px;
    color: #78350F;
}

/* OK box */
.ok-box {
    background: #F0FDF4;
    border-left: 4px solid #16A34A;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    margin: 0.6rem 0;
    font-size: 13px;
    color: #166534;
}

/* Hypothesis cards */
.hyp-card {
    background: #FAFAF7;
    border: 1px solid #E8E0D4;
    border-left: 4px solid #8B0000;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
}

/* Buttons */
.stButton > button {
    background: #8B0000 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton > button:hover {
    background: #6B0000 !important;
    box-shadow: 0 2px 8px rgba(139,0,0,0.25) !important;
}

/* Citation entries */
.citation-entry {
    border-bottom: 1px solid #F0E8DC;
    padding: 0.8rem 0;
    font-size: 13px;
    line-height: 1.6;
}
.citation-entry:last-child { border-bottom: none; }

/* Patent card */
.patent-card {
    background: #FFFFFF;
    border: 1px solid #E8E0D4;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
}

hr { border-color: #E8E0D4; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
DEFAULTS = {
    "module":           "home",
    "topic":            "",
    "domain":           "",
    "citation_bank":    [],
    "hypotheses":       [],
    "gaps":             [],
    "framework_data":   {},
    "proposal":         {},
    "patent_results":   {},
    "stat_plan":        {},
    "real_data":        {},
    "tier":             "individual",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════
def get_api_keys() -> dict:
    return {
        "anthropic":  os.environ.get("ANTHROPIC_API_KEY",""),
        "fireworks":  os.environ.get("FIREWORKS_API_KEY",""),
        "groq":       os.environ.get("GROQ_API_KEY",""),
        "deepseek":   os.environ.get("DEEPSEEK_API_KEY",""),
        "firecrawl":  os.environ.get("FIRECRAWL_API_KEY",""),
    }

def think(system: str, prompt: str, max_tokens: int = 1500,
          heavy: bool = False) -> str:
    """
    All Shodhak intelligence calls.
    Prep/planning → cheap models.
    Patent analysis → Opus.
    """
    keys = get_api_keys()
    msgs = [{"role": "user", "content": prompt}]
    if heavy:
        return call_model("claude-opus-4-6", msgs, max_tokens, system, keys)
    return call_prep(msgs, system, max_tokens, keys)

def think_sonnet(system: str, prompt: str, max_tokens: int = 2000) -> str:
    keys = get_api_keys()
    msgs = [{"role": "user", "content": prompt}]
    return call_writer("Medium", msgs, system, max_tokens, False, keys)

def json_parse(text: str):
    clean = re.sub(r'```json|```', '', text).strip()
    return json.loads(clean)

SHODHAK_SYSTEM = """You are Shodhak — a research intelligence engine for Indian researchers.
You help researchers find gaps, plan studies, understand statistics, and screen patents.
You never write papers or generate fake data.
You always cite real sources. If no data exists, say so honestly.
You explain concepts in plain language that a first-generation PhD student can understand.
You are the supervisor 95% of Indian researchers never had — patient, rigorous, honest."""

# ══════════════════════════════════════════════════════════
# SIDEBAR — MODULE NAVIGATION
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="shodhak-title">🔬 Shodhak</div>'
        '<div class="shodhak-tagline">The research supervisor you never had</div>',
        unsafe_allow_html=True)

    if AUTH_AVAILABLE:
        render_user_badge()

    st.markdown("---")
    st.markdown("**Research Planning**")

    MODULES = [
        ("gap_finder",    "🔍", "Research Gap Finder",
         "Find what's missing in your field"),
        ("hypothesis",    "💡", "Hypothesis Generator",
         "H₀/H₁ from plain language"),
        ("framework",     "🗺️", "Conceptual Framework",
         "Mediation, moderation, variable maps"),
        ("stats",         "📊", "Statistics Selector",
         "Right test, right assumptions"),
        ("sample_size",   "🔢", "Sample Size Calculator",
         "Based on literature effect sizes"),
        ("proposal",      "📋", "Research Proposal",
         "Title, abstract, timeline, budget"),
        ("citations",     "📚", "Citation Network",
         "100-word summaries, gap detection"),
        ("reviewer",      "✍️", "Reviewer Responder",
         "Turn reviewer comments into actions"),
    ]

    st.markdown("**Patent Intelligence**")
    PATENT_MODULES = [
        ("patent_screen", "⚖️", "Patent Novelty Screener",
         "IPO, USPTO, Google Patents"),
        ("patent_advisor","🏛️", "Patent Category Advisor",
         "India filing guidance"),
        ("prior_art",     "🗂️", "Prior Art Map",
         "What exists, what's patentable"),
    ]

    for mod_id, icon, title, desc in MODULES + PATENT_MODULES:
        is_active = st.session_state.module == mod_id
        if st.button(
            f"{icon} {title}",
            key=f"nav_{mod_id}",
            use_container_width=True,
            help=desc,
        ):
            st.session_state.module = mod_id
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="zero-hal">✅ Zero Hallucination Policy<br>'
        'Real citations only. No invented data.</div>',
        unsafe_allow_html=True)

    # Admin access — completely hidden, no public mention
    with st.expander("⚙️", expanded=False):
        admin_pw = st.text_input("", type="password",
                                  key="admin_pw", label_visibility="collapsed")
        if admin_pw == os.environ.get("ADMIN_PASSWORD","shodhak_admin_2026"):
            st.session_state["admin_mode"] = True
            st.success("Admin mode active")
            if st.button("→ Research Scaffold Builder", key="goto_admin"):
                st.session_state.module = "admin"
                st.rerun()

# ══════════════════════════════════════════════════════════
# AUTH GATE
# ══════════════════════════════════════════════════════════
if AUTH_AVAILABLE and not st.session_state.get("authenticated"):
    render_auth_screen()
    st.stop()

# ══════════════════════════════════════════════════════════
# SHARED TOPIC INPUT (shown on all modules)
# ══════════════════════════════════════════════════════════
def render_topic_bar():
    with st.container():
        c1, c2 = st.columns([4, 1])
        topic = c1.text_input(
            "Research topic or question",
            value=st.session_state.topic,
            placeholder="e.g. Effect of mindfulness on burnout among Indian nurses",
            key="global_topic",
            label_visibility="collapsed")
        if topic != st.session_state.topic:
            st.session_state.topic = topic
            # Reset downstream state on topic change
            st.session_state.citation_bank = []
            st.session_state.hypotheses    = []
            st.session_state.gaps          = []

# ══════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════
if st.session_state.module == "home":
    st.markdown(
        '<div class="shodhak-title">Shodhak</div>'
        '<div class="shodhak-tagline">'
        'The research supervisor that 95% of Indian researchers never had.'
        '</div>',
        unsafe_allow_html=True)

    st.markdown(
        "Enter your research topic below and choose a module from the sidebar.")

    render_topic_bar()

    st.markdown("---")
    st.markdown("### What would you like to do today?")

    cards = [
        ("gap_finder",   "🔍", "Find Research Gaps",
         "Discover what's missing in your field using real citations from Semantic Scholar, OpenAlex, and CrossRef."),
        ("hypothesis",   "💡", "Generate Hypotheses",
         "Turn your research question into formal H₀/H₁ with plain language explanations."),
        ("framework",    "🗺️", "Build Conceptual Framework",
         "Map your variables, mediators, and moderators into a publication-ready diagram."),
        ("stats",        "📊", "Select Statistical Tests",
         "Get the right test for your design with assumptions checklist and sample size guidance."),
        ("proposal",     "📋", "Generate Research Proposal",
         "Title, abstract, objectives, timeline, and budget — ready for funding applications."),
        ("patent_screen","⚖️", "Screen Patent Novelty",
         "Check your innovation against IPO, USPTO, and Google Patents before filing."),
    ]

    cols = st.columns(3)
    for i, (mod_id, icon, title, desc) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(
                f'<div class="module-card">'
                f'<div class="module-icon">{icon}</div>'
                f'<div class="module-title">{title}</div>'
                f'<div class="module-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True)
            if st.button(f"Open {title.split()[0]}", key=f"home_{mod_id}",
                         use_container_width=True):
                st.session_state.module = mod_id
                st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="zero-hal">'
        '✅ Zero Hallucination Policy — Shodhak only shows real data from '
        'WHO, World Bank, OGD India, RBI, Semantic Scholar, and 96 other '
        'verified sources. If no data exists for your query, we say so '
        'honestly and suggest alternatives. No invented citations. Ever.'
        '</div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# MODULE 1 — RESEARCH GAP FINDER
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "gap_finder":
    st.markdown("## 🔍 Research Gap Finder")
    st.caption(
        "Finds what's missing in your field using real citations. "
        "Not opinions. Literature.")

    render_topic_bar()
    if not st.session_state.topic:
        st.info("Enter your research topic above to begin.")
        st.stop()

    if st.button("🔍 Find Research Gaps", use_container_width=True):
        with st.spinner("Fetching real citations and analysing gaps…"):
            # Phase A — real citations
            bank = fetch_citation_bank(
                [st.session_state.topic], target=15)
            st.session_state.citation_bank = bank

            cite_text = bank_to_prompt_text(bank[:12], "APA")

            prompt = f"""Research topic: {st.session_state.topic}

Verified citations from the literature:
{cite_text}

Analyse these citations and identify:
1. THREE specific research gaps — things the literature has NOT studied yet
2. For each gap: what was studied, what is missing, why it matters
3. TWO methodological gaps — limitations in how existing studies were done
4. ONE contradictory finding that represents a research opportunity

Be specific. Name actual studies. Use the citations provided.
If a gap cannot be supported by the provided citations, say so.

Return ONLY valid JSON:
{{
  "substantive_gaps": [
    {{
      "gap": "one sentence description",
      "evidence": "which citations show this gap",
      "importance": "why this matters for research or practice",
      "suggested_direction": "what a study could do"
    }}
  ],
  "methodological_gaps": [
    {{
      "gap": "one sentence",
      "evidence": "citation evidence",
      "suggestion": "how to address it"
    }}
  ],
  "contradictions": [
    {{
      "finding_a": "what one group found",
      "finding_b": "what another found",
      "opportunity": "what resolving this could contribute"
    }}
  ],
  "overall_maturity": "emerging|developing|mature",
  "field_summary": "two sentences on the state of this field"
}}"""

            try:
                raw  = think_sonnet(SHODHAK_SYSTEM, prompt, 2000)
                data = json_parse(raw)
                st.session_state.gaps = data
            except Exception as e:
                st.error(f"Analysis error: {e}")

    gaps = st.session_state.gaps
    if not gaps:
        st.stop()

    # Field summary
    st.markdown(
        f'<div class="ok-box">'
        f'<strong>Field status:</strong> {gaps.get("overall_maturity","").title()}<br>'
        f'{gaps.get("field_summary","")}'
        f'</div>',
        unsafe_allow_html=True)

    # Substantive gaps
    st.markdown("### Substantive Research Gaps")
    for i, g in enumerate(gaps.get("substantive_gaps",[]), 1):
        with st.expander(f"Gap {i}: {g.get('gap','')}", expanded=i==1):
            st.markdown(f"**Evidence from literature:** {g.get('evidence','')}")
            st.markdown(f"**Why this matters:** {g.get('importance','')}")
            st.markdown(
                f'<div class="ok-box">💡 Suggested direction: '
                f'{g.get("suggested_direction","")}</div>',
                unsafe_allow_html=True)

    # Methodological gaps
    st.markdown("### Methodological Gaps")
    for g in gaps.get("methodological_gaps",[]):
        st.markdown(
            f'<div class="result-card">'
            f'<h4>⚙️ {g.get("gap","")}</h4>'
            f'Evidence: {g.get("evidence","")}<br>'
            f'<strong>How to address:</strong> {g.get("suggestion","")}'
            f'</div>',
            unsafe_allow_html=True)

    # Contradictions
    if gaps.get("contradictions"):
        st.markdown("### Contradictory Findings — Research Opportunities")
        for c in gaps["contradictions"]:
            cols = st.columns(2)
            cols[0].markdown(
                f'<div class="warn-box">Finding A<br>{c.get("finding_a","")}</div>',
                unsafe_allow_html=True)
            cols[1].markdown(
                f'<div class="warn-box">Finding B<br>{c.get("finding_b","")}</div>',
                unsafe_allow_html=True)
            st.markdown(
                f'<div class="ok-box">🎯 Opportunity: {c.get("opportunity","")}</div>',
                unsafe_allow_html=True)

    # Citations used
    with st.expander(f"📚 {len(st.session_state.citation_bank)} Citations Verified"):
        for p in st.session_state.citation_bank:
            st.markdown(
                f'<div class="citation-entry">{format_citation(p,"APA")}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# MODULE 2 — HYPOTHESIS GENERATOR
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "hypothesis":
    st.markdown("## 💡 Hypothesis Generator")
    st.caption(
        "Turn your research question into formal H₀/H₁ pairs with "
        "plain language explanations and statistical implications.")

    render_topic_bar()
    if not st.session_state.topic:
        st.info("Enter your research topic above.")
        st.stop()

    research_q = st.text_area(
        "Your research question (plain language)",
        placeholder="Does practising mindfulness reduce burnout among "
                    "nurses working in Indian public hospitals?",
        height=80, key="hyp_rq")
    study_type = st.selectbox(
        "Study design",
        ["Experimental (pre/post)", "Cross-sectional survey",
         "Longitudinal", "Case-control", "Mixed methods",
         "Systematic review / Meta-analysis"],
        key="hyp_design")
    n_hyp = st.slider("Number of hypotheses", 2, 6, 3, key="hyp_n")

    if st.button("💡 Generate Hypotheses", use_container_width=True):
        with st.spinner("Generating hypotheses with statistical grounding…"):
            # Fetch citations if not already done
            if not st.session_state.citation_bank:
                st.session_state.citation_bank = fetch_citation_bank(
                    [st.session_state.topic], target=10)

            cite_text = bank_to_prompt_text(
                st.session_state.citation_bank[:8], "APA")

            prompt = f"""Research topic: {st.session_state.topic}
Research question: {research_q or st.session_state.topic}
Study design: {study_type}
Number of hypotheses needed: {n_hyp}

Relevant literature:
{cite_text}

Generate {n_hyp} research hypotheses. For each:
- Write the null hypothesis (H₀) in formal statistical language
- Write the alternate hypothesis (H₁) in formal statistical language
- Explain both in plain language (what it means in practice)
- Suggest the appropriate statistical test
- List key assumptions the researcher must check
- Reference which citation supports this hypothesis

Return ONLY valid JSON:
{{
  "hypotheses": [
    {{
      "number": 1,
      "h0_formal": "There is no significant difference...",
      "h1_formal": "There is a significant difference...",
      "plain_language": "We are testing whether...",
      "recommended_test": "Paired t-test",
      "assumptions": ["Normality", "Independence", "Equal variance"],
      "citation_support": "Author (year) found that...",
      "variables": {{"independent": "X", "dependent": "Y", "mediator": null, "moderator": null}}
    }}
  ]
}}"""

            try:
                raw  = think_sonnet(SHODHAK_SYSTEM, prompt, 2000)
                data = json_parse(raw)
                st.session_state.hypotheses = data.get("hypotheses",[])
            except Exception as e:
                st.error(f"Error: {e}")

    hyps = st.session_state.hypotheses
    if not hyps:
        st.stop()

    for h in hyps:
        with st.expander(
            f"H{h.get('number','')} — {h.get('h1_formal','')[:70]}…",
            expanded=h.get("number")==1):

            c1, c2 = st.columns(2)
            c1.markdown(
                f'<div class="warn-box">'
                f'<strong>H₀ (Null):</strong><br>'
                f'{h.get("h0_formal","")}</div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="ok-box">'
                f'<strong>H₁ (Alternate):</strong><br>'
                f'{h.get("h1_formal","")}</div>',
                unsafe_allow_html=True)

            st.markdown(f"**Plain language:** {h.get('plain_language','')}")
            st.markdown(
                f'<span class="stat-chip">Test: {h.get("recommended_test","")}</span>',
                unsafe_allow_html=True)

            assumptions = h.get("assumptions",[])
            if assumptions:
                st.markdown("**Assumptions to check:**")
                for a in assumptions:
                    st.markdown(f"  ☐ {a}")

            if h.get("citation_support"):
                st.caption(f"📚 Literature basis: {h.get('citation_support','')}")


# ══════════════════════════════════════════════════════════
# MODULE 3 — CONCEPTUAL FRAMEWORK
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "framework":
    st.markdown("## 🗺️ Conceptual Framework Builder")
    st.caption(
        "Map your variables into a publication-ready diagram. "
        "Mediation, moderation, direct effects, control variables.")

    render_topic_bar()

    iv  = st.text_input("Independent Variable (IV)", placeholder="Mindfulness training",
                         key="fw_iv")
    dv  = st.text_input("Dependent Variable (DV)", placeholder="Nurse burnout",
                         key="fw_dv")
    med = st.text_input("Mediator (optional)", placeholder="Emotional regulation",
                         key="fw_med")
    mod = st.text_input("Moderator (optional)", placeholder="Years of experience",
                         key="fw_mod")
    cv  = st.text_input("Control Variables (comma separated)",
                         placeholder="Age, Gender, Hospital type",
                         key="fw_cv")

    if st.button("🗺️ Build Framework", use_container_width=True):
        if not iv or not dv:
            st.error("IV and DV are required.")
        else:
            with st.spinner("Building conceptual framework…"):
                cv_list = [c.strip() for c in cv.split(",") if c.strip()]

                # Generate framework diagram using matplotlib
                if DIAGRAMS_AVAILABLE:
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    import matplotlib.patches as mpatches
                    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
                    import io

                    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
                    ax.set_xlim(0, 12)
                    ax.set_ylim(0, 7)
                    ax.axis('off')

                    font = "Times New Roman"
                    box_kw = dict(boxstyle="round,pad=0.4",
                                  facecolor="#F5F0E8",
                                  edgecolor="#8B4513", linewidth=1.5)
                    med_kw = dict(boxstyle="round,pad=0.4",
                                  facecolor="#EBF5FB",
                                  edgecolor="#1A5276", linewidth=1.5)
                    mod_kw = dict(boxstyle="round,pad=0.4",
                                  facecolor="#FEF9E7",
                                  edgecolor="#B7950B", linewidth=1.5)
                    dv_kw  = dict(boxstyle="round,pad=0.4",
                                  facecolor="#F9EBEA",
                                  edgecolor="#8B0000", linewidth=2)

                    arrow_kw = dict(arrowprops=dict(
                        arrowstyle="->", color="#1C1C1E",
                        lw=1.5, connectionstyle="arc3,rad=0"))

                    # IV box
                    ax.text(1.8, 3.5, iv, ha='center', va='center',
                            fontsize=11, fontfamily=font, fontweight='bold',
                            bbox=box_kw, wrap=True)

                    # DV box
                    ax.text(10.2, 3.5, dv, ha='center', va='center',
                            fontsize=11, fontfamily=font, fontweight='bold',
                            bbox=dv_kw, wrap=True)

                    if med:
                        # Mediator path: IV→Med→DV
                        ax.text(6.0, 5.8, med, ha='center', va='center',
                                fontsize=10, fontfamily=font,
                                bbox=med_kw)
                        ax.annotate("", xy=(4.5,5.4), xytext=(2.8,4.0),
                                    **arrow_kw)
                        ax.annotate("", xy=(7.5,4.0), xytext=(7.5,5.4),
                                    arrowprops=dict(arrowstyle="->",
                                    color="#1A5276", lw=1.5))
                        # Label paths
                        ax.text(3.2, 5.0, "a path", fontsize=9,
                                fontfamily=font, color="#1A5276",
                                style='italic')
                        ax.text(7.8, 5.0, "b path", fontsize=9,
                                fontfamily=font, color="#1A5276",
                                style='italic')
                        # Direct path IV→DV (c')
                        ax.annotate("", xy=(8.8,3.5), xytext=(2.8,3.5),
                                    **arrow_kw)
                        ax.text(5.8, 3.1, "c' (direct)", fontsize=9,
                                fontfamily=font, style='italic')
                    else:
                        # Direct path only
                        ax.annotate("", xy=(8.8,3.5), xytext=(2.8,3.5),
                                    **arrow_kw)
                        ax.text(5.5, 3.8, "direct effect", fontsize=9,
                                fontfamily=font, style='italic')

                    if mod:
                        # Moderator on IV→DV path
                        ax.text(6.0, 1.5, mod, ha='center', va='center',
                                fontsize=10, fontfamily=font,
                                bbox=mod_kw)
                        ax.annotate("", xy=(6.0, 3.2), xytext=(6.0, 2.2),
                                    arrowprops=dict(arrowstyle="->",
                                    color="#B7950B", lw=1.5,
                                    linestyle='dashed'))
                        ax.text(6.3, 2.7, "moderation", fontsize=9,
                                fontfamily=font, color="#B7950B",
                                style='italic')

                    if cv_list:
                        cv_text = "Controls: " + ", ".join(cv_list[:4])
                        ax.text(6.0, 0.5, cv_text, ha='center', fontsize=9,
                                fontfamily=font, color="#666666",
                                style='italic')

                    # Legend
                    patches = [
                        mpatches.Patch(facecolor='#F5F0E8',
                            edgecolor='#8B4513', label='Independent Variable'),
                        mpatches.Patch(facecolor='#F9EBEA',
                            edgecolor='#8B0000', label='Dependent Variable'),
                    ]
                    if med:
                        patches.append(mpatches.Patch(facecolor='#EBF5FB',
                            edgecolor='#1A5276', label='Mediator'))
                    if mod:
                        patches.append(mpatches.Patch(facecolor='#FEF9E7',
                            edgecolor='#B7950B', label='Moderator'))
                    ax.legend(handles=patches, loc='upper right',
                              fontsize=9, framealpha=0.9)

                    fig.tight_layout()
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=300,
                                bbox_inches='tight', facecolor='white')
                    plt.close(fig)
                    buf.seek(0)
                    st.image(buf.getvalue(),
                             caption="Conceptual Framework Diagram",
                             use_container_width=True)

                    import streamlit as _st
                    _st.download_button(
                        "📥 Download Framework (PNG)",
                        data=buf.getvalue(),
                        file_name="conceptual_framework.png",
                        mime="image/png")

                # Framework explanation
                fw_prompt = f"""Conceptual framework:
IV: {iv}, DV: {dv}
{"Mediator: " + med if med else "No mediator"}
{"Moderator: " + mod if mod else "No moderator"}
Controls: {cv or "None"}

Write a 200-word academic explanation of this conceptual framework
suitable for a methodology section. Explain each path and its
theoretical justification. Use clear, formal language."""

                explanation = think_sonnet(SHODHAK_SYSTEM, fw_prompt, 500)
                if AUDIT_AVAILABLE:
                    explanation, _ = clean_blocklist(explanation)
                st.markdown("**Framework Explanation (for methodology section):**")
                st.markdown(explanation)


# ══════════════════════════════════════════════════════════
# MODULE 4 — STATISTICS SELECTOR
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "stats":
    st.markdown("## 📊 Statistical Test Selector")
    st.caption(
        "The right test for your design, with assumptions and "
        "sample size guidance. Cite-backed recommendations.")

    render_topic_bar()

    c1, c2 = st.columns(2)
    design = c1.selectbox("Research design", [
        "Pre-test / Post-test (one group)",
        "Pre-test / Post-test (two groups)",
        "Cross-sectional survey",
        "Three or more groups",
        "Correlation between two variables",
        "Multiple predictors → one outcome",
        "Repeated measures (3+ time points)",
        "Categorical outcome",
        "Survival / Time-to-event",
        "Hierarchical / Nested data",
        "Structural Equation Modelling",
    ], key="stats_design")
    data_type = c2.selectbox("Outcome data type", [
        "Continuous (interval/ratio)",
        "Ordinal (Likert scale)",
        "Categorical (nominal)",
        "Count data",
        "Binary (yes/no)",
        "Time-to-event",
    ], key="stats_dtype")

    n_approx = st.number_input("Approximate sample size", 10, 10000, 90,
                                key="stats_n")
    normality = st.radio("Distribution assumption", [
        "Assume normal (parametric)",
        "Do not assume normal (non-parametric)",
        "I don't know yet",
    ], horizontal=True, key="stats_norm")

    if st.button("📊 Select Statistical Tests", use_container_width=True):
        with st.spinner("Analysing your design…"):
            prompt = f"""Research design: {design}
Outcome data type: {data_type}
Sample size: {n_approx}
Normality assumption: {normality}
Research topic: {st.session_state.topic or "not specified"}

Provide statistical test recommendations. Return ONLY valid JSON:
{{
  "primary_test": {{
    "name": "Paired t-test",
    "when_to_use": "one sentence",
    "assumptions": ["list", "of", "assumptions"],
    "assumption_checks": ["Shapiro-Wilk for normality", "..."],
    "effect_size": "Cohen's d",
    "reporting_format": "t(df) = value, p = value, d = value",
    "software_command": {{
      "spss": "Analyze > Compare Means > Paired Samples T Test",
      "r": "t.test(pre, post, paired=TRUE)",
      "python": "scipy.stats.ttest_rel(pre, post)"
    }}
  }},
  "alternative_test": {{
    "name": "Wilcoxon Signed-Rank",
    "when_to_use": "if normality is violated",
    "assumptions": [],
    "effect_size": "r = Z/√N"
  }},
  "sample_size_note": "At medium effect (d=0.5), 80% power, α=0.05, you need N=...",
  "common_mistakes": ["list of mistakes researchers make with this test"],
  "interpretation_guide": "How to interpret and report the result"
}}"""

            try:
                raw  = think(SHODHAK_SYSTEM, prompt, 1500)
                data = json_parse(raw)
                st.session_state.stat_plan = data
            except Exception as e:
                st.error(f"Error: {e}")

    sp = st.session_state.stat_plan
    if not sp:
        st.stop()

    pt = sp.get("primary_test",{})
    st.markdown(
        f'<div class="ok-box">'
        f'<strong>Recommended: {pt.get("name","")}</strong><br>'
        f'{pt.get("when_to_use","")}'
        f'</div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Assumptions to check:**")
        for a in pt.get("assumptions",[]):
            st.markdown(f"  ☐ {a}")
        st.markdown("**How to check:**")
        for a in pt.get("assumption_checks",[]):
            st.markdown(f"  • {a}")

    with c2:
        st.markdown("**Software commands:**")
        sw = pt.get("software_command",{})
        if sw.get("spss"):
            st.code(sw["spss"], language=None)
        if sw.get("r"):
            st.code(sw["r"], language="r")
        if sw.get("python"):
            st.code(sw["python"], language="python")
        st.markdown(f"**Reporting format:**")
        st.code(pt.get("reporting_format",""), language=None)

    if sp.get("sample_size_note"):
        st.markdown(
            f'<div class="warn-box">📐 {sp["sample_size_note"]}</div>',
            unsafe_allow_html=True)

    if sp.get("alternative_test"):
        at = sp["alternative_test"]
        with st.expander(f"Alternative: {at.get('name','')}"):
            st.markdown(f"**Use when:** {at.get('when_to_use','')}")
            st.markdown(f"**Effect size:** {at.get('effect_size','')}")

    if sp.get("common_mistakes"):
        with st.expander("⚠️ Common Mistakes with This Test"):
            for m in sp["common_mistakes"]:
                st.markdown(f"  • {m}")


# ══════════════════════════════════════════════════════════
# MODULE 5 — SAMPLE SIZE CALCULATOR
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "sample_size":
    st.markdown("## 🔢 Sample Size Calculator")
    st.caption(
        "Based on effect sizes from the literature — not rules of thumb.")

    render_topic_bar()

    c1, c2, c3 = st.columns(3)
    effect_size = c1.selectbox("Expected effect size", [
        "Small (d=0.2 / f=0.1 / r=0.1)",
        "Medium (d=0.5 / f=0.25 / r=0.3)",
        "Large (d=0.8 / f=0.4 / r=0.5)",
        "From literature (specify below)",
    ], key="ss_effect")
    power       = c2.selectbox("Statistical power", ["0.80","0.85","0.90","0.95"],
                                key="ss_power")
    alpha       = c3.selectbox("Alpha (significance level)", ["0.05","0.01","0.001"],
                                key="ss_alpha")
    lit_effect  = st.text_input(
        "Literature effect size (if known)",
        placeholder="e.g. d=0.43 from Kumar et al. (2022)",
        key="ss_lit")
    test_type   = st.selectbox("Statistical test", [
        "Independent t-test","Paired t-test","One-way ANOVA",
        "Pearson correlation","Linear regression","Chi-square",
        "Repeated measures ANOVA",
    ], key="ss_test")

    if st.button("🔢 Calculate Sample Size", use_container_width=True):
        with st.spinner("Calculating…"):
            prompt = f"""Calculate sample size for:
Test: {test_type}
Effect size: {effect_size} {("(from literature: " + lit_effect + ")") if lit_effect else ""}
Power: {power}
Alpha: {alpha}
Research topic: {st.session_state.topic or "general"}

Return ONLY valid JSON:
{{
  "minimum_n": 90,
  "recommended_n": 110,
  "with_attrition_20pct": 132,
  "formula_used": "Cohen (1988) formula for t-test",
  "effect_size_used": "d = 0.5",
  "calculation_steps": ["Step 1...", "Step 2..."],
  "literature_comparison": "Studies in this domain typically use N=80-150",
  "g_power_settings": "G*Power: t-tests > Means: Difference between two dependent means",
  "interpretation": "plain language explanation of what this means"
}}"""
            try:
                raw  = think(SHODHAK_SYSTEM, prompt, 800)
                data = json_parse(raw)
                # Display
                c1,c2,c3 = st.columns(3)
                c1.metric("Minimum N", data.get("minimum_n","—"))
                c2.metric("Recommended N", data.get("recommended_n","—"))
                c3.metric("With 20% attrition", data.get("with_attrition_20pct","—"))
                st.markdown(f"**Formula:** {data.get('formula_used','')}")
                st.markdown(f"**Effect size used:** {data.get('effect_size_used','')}")
                st.markdown(f"**G*Power settings:** `{data.get('g_power_settings','')}`")
                if data.get("literature_comparison"):
                    st.markdown(
                        f'<div class="ok-box">'
                        f'📚 {data["literature_comparison"]}'
                        f'</div>',
                        unsafe_allow_html=True)
                st.markdown(f"**Interpretation:** {data.get('interpretation','')}")
            except Exception as e:
                st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════
# MODULE 6 — RESEARCH PROPOSAL GENERATOR
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "proposal":
    st.markdown("## 📋 Research Proposal Generator")
    st.caption(
        "Title, abstract, objectives, methodology, timeline, and budget. "
        "Ready for funding applications. Real citations included.")

    render_topic_bar()
    if not st.session_state.topic:
        st.info("Enter your research topic above.")
        st.stop()

    c1, c2 = st.columns(2)
    funding_body  = c1.text_input("Funding body",
                                   placeholder="ICSSR / DST-SERB / CSIR / UGC",
                                   key="prop_funding")
    duration_yrs  = c2.selectbox("Project duration", ["1 year","2 years","3 years"],
                                  key="prop_duration")
    budget_lakhs  = st.number_input("Budget (₹ Lakhs)", 1.0, 50.0, 5.0,
                                     key="prop_budget")
    institution   = st.text_input("Your institution",
                                   placeholder="University of Pune / SPPU",
                                   key="prop_inst")

    if st.button("📋 Generate Research Proposal", use_container_width=True):
        with st.spinner("Generating proposal with real citations…"):
            if not st.session_state.citation_bank:
                st.session_state.citation_bank = fetch_citation_bank(
                    [st.session_state.topic], target=12)

            cite_text = bank_to_prompt_text(
                st.session_state.citation_bank[:10], "APA")

            prompt = f"""Generate a research proposal for:
Topic: {st.session_state.topic}
Funding body: {funding_body or "General academic funding"}
Duration: {duration_yrs}
Budget: ₹{budget_lakhs} Lakhs
Institution: {institution or "Indian University"}

Real citations available:
{cite_text}

Return ONLY valid JSON:
{{
  "title": "formal academic title",
  "short_title": "abbreviated title",
  "abstract": "250-word structured abstract (Background/Objectives/Methods/Expected Outcomes)",
  "background": "150 words with citation references",
  "objectives": ["objective 1", "objective 2", "objective 3"],
  "hypotheses": ["H1: ...", "H2: ..."],
  "methodology": {{
    "design": "research design",
    "population": "who",
    "sample_size": "N and justification",
    "sampling": "method",
    "tools": ["tool 1", "tool 2"],
    "analysis": ["statistical test 1", "test 2"]
  }},
  "timeline": [
    {{"month_range": "1-3", "activity": "Literature review and tool development"}},
    {{"month_range": "4-8", "activity": "Data collection"}},
    {{"month_range": "9-11", "activity": "Analysis and writing"}},
    {{"month_range": "12", "activity": "Dissemination"}}
  ],
  "budget_breakdown": [
    {{"head": "Personnel", "amount_lakhs": 2.5}},
    {{"head": "Equipment", "amount_lakhs": 0.5}},
    {{"head": "Travel", "amount_lakhs": 0.5}},
    {{"head": "Contingency", "amount_lakhs": 0.5}}
  ],
  "expected_outcomes": ["outcome 1", "outcome 2"],
  "dissemination_plan": "journals and conferences"
}}"""

            try:
                raw  = think_sonnet(SHODHAK_SYSTEM, prompt, 2500)
                data = json_parse(raw)
                st.session_state.proposal = data
            except Exception as e:
                st.error(f"Error: {e}")

    prop = st.session_state.proposal
    if not prop:
        st.stop()

    st.markdown(f"### {prop.get('title','')}")
    st.caption(prop.get("short_title",""))

    with st.expander("📄 Abstract", expanded=True):
        st.markdown(prop.get("abstract",""))

    with st.expander("🎯 Objectives & Hypotheses"):
        st.markdown("**Objectives:**")
        for i, o in enumerate(prop.get("objectives",[]),1):
            st.markdown(f"{i}. {o}")
        st.markdown("**Hypotheses:**")
        for h in prop.get("hypotheses",[]):
            st.markdown(f"• {h}")

    with st.expander("🔬 Methodology"):
        m = prop.get("methodology",{})
        for k,v in m.items():
            if isinstance(v,list):
                st.markdown(f"**{k.title()}:** {', '.join(v)}")
            else:
                st.markdown(f"**{k.title()}:** {v}")

    with st.expander("📅 Timeline"):
        for t in prop.get("timeline",[]):
            st.markdown(
                f'<div class="result-card" style="padding:0.6rem 1rem">'
                f'<strong>Month {t.get("month_range","")}</strong> — '
                f'{t.get("activity","")}</div>',
                unsafe_allow_html=True)

    with st.expander("💰 Budget"):
        total = sum(b.get("amount_lakhs",0)
                    for b in prop.get("budget_breakdown",[]))
        for b in prop.get("budget_breakdown",[]):
            st.markdown(
                f"**{b.get('head','')}:** ₹{b.get('amount_lakhs',0):.1f} Lakhs")
        st.markdown(f"**Total: ₹{total:.1f} Lakhs**")

    # Download as DOCX
    if FORMATTER_AVAILABLE:
        proposal_text = f"""# {prop.get('title','')}

## Abstract
{prop.get('abstract','')}

## Background
{prop.get('background','')}

## Objectives
{chr(10).join(f"{i+1}. {o}" for i,o in enumerate(prop.get('objectives',[])))}

## Hypotheses
{chr(10).join(prop.get('hypotheses',[]))}

## Methodology
Design: {prop.get('methodology',{}).get('design','')}
Population: {prop.get('methodology',{}).get('population','')}
Sample Size: {prop.get('methodology',{}).get('sample_size','')}

## Expected Outcomes
{chr(10).join(prop.get('expected_outcomes',[]))}
"""
        docx_bytes = build_professional_docx(
            content    = proposal_text,
            title      = prop.get("title","Research Proposal"),
            style_key  = "APA7",
            keywords   = [st.session_state.topic[:30]],
            citation_style = "APA",
        )
        st.download_button(
            "📥 Download Proposal (DOCX)",
            data      = docx_bytes,
            file_name = "research_proposal.docx",
            mime      = "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
            use_container_width=True)


# ══════════════════════════════════════════════════════════
# MODULE 7 — CITATION NETWORK
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "citations":
    st.markdown("## 📚 Citation Network")
    st.caption("Real papers. 100-word summaries. Gap analysis. APA/MLA.")

    render_topic_bar()
    if not st.session_state.topic:
        st.info("Enter your research topic above.")
        st.stop()

    cite_style = st.radio("Citation style", ["APA","MLA","Vancouver"],
                           horizontal=True, key="cite_style")
    n_papers   = st.slider("Number of papers to fetch", 5, 20, 12,
                            key="cite_n")

    if st.button("📚 Fetch Citation Network", use_container_width=True):
        with st.spinner("Fetching verified papers from Semantic Scholar → OpenAlex → CrossRef…"):
            bank = fetch_citation_bank([st.session_state.topic],
                                        target=n_papers)
            st.session_state.citation_bank = bank

            # Generate 100-word summaries
            if bank:
                summaries_prompt = f"""For this research topic: {st.session_state.topic}

I have these verified papers:
{bank_to_prompt_text(bank[:10], "APA")}

For each paper, write a 100-word summary covering:
what they studied, how, what they found, and why it matters.

Return ONLY valid JSON:
{{"summaries": [
  {{"citation": "Author (year)", "summary": "100 words"}}
]}}"""
                try:
                    raw  = think(SHODHAK_SYSTEM, summaries_prompt, 2000)
                    data = json_parse(raw)
                    st.session_state["cite_summaries"] = data.get("summaries",[])
                except Exception:
                    st.session_state["cite_summaries"] = []

    bank     = st.session_state.citation_bank
    summaries= st.session_state.get("cite_summaries",[])

    if not bank:
        st.stop()

    st.markdown(
        f'<div class="ok-box">'
        f'✅ {len(bank)} verified papers fetched. '
        f'All citations confirmed via Phase C CrossRef verification.'
        f'</div>',
        unsafe_allow_html=True)

    sum_map = {s.get("citation",""):s.get("summary","")
               for s in summaries}

    for i, p in enumerate(bank, 1):
        cite = format_citation(p, cite_style)
        summary = sum_map.get(
            f"{(p.get('authors',['']) or [''])[0].split()[-1]} ({p.get('year','')})","")
        with st.expander(f"{i}. {p.get('title','')[:70]}…", expanded=False):
            st.markdown(f"**{cite}**")
            if summary:
                st.markdown(summary)
            if p.get("doi"):
                st.caption(f"DOI: https://doi.org/{p['doi']}")


# ══════════════════════════════════════════════════════════
# MODULE 8 — REVIEWER COMMENT RESPONDER
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "reviewer":
    st.markdown("## ✍️ Reviewer Comment Responder")
    st.caption(
        "Turn reviewer comments into specific, actionable responses "
        "with suggested text and additional citations where needed.")

    comments = st.text_area(
        "Paste reviewer comments here",
        placeholder="Reviewer 1, Comment 1: The sample size is too small...\n"
                    "Reviewer 2, Comment 1: The theoretical framework is unclear...",
        height=200, key="rev_comments")
    journal = st.text_input("Journal / Conference",
                             placeholder="Journal of Educational Research",
                             key="rev_journal")

    if st.button("✍️ Generate Responses", use_container_width=True):
        if not comments.strip():
            st.error("Paste reviewer comments to begin.")
        else:
            with st.spinner("Generating responses…"):
                prompt = f"""Reviewer comments for journal: {journal or "academic journal"}
Research topic: {st.session_state.topic or "not specified"}

COMMENTS:
{comments}

Generate professional, respectful responses to each comment.
For each:
- Acknowledge the reviewer's concern
- Explain what changes will be made (or why they are not needed)
- Provide suggested text if new content is needed
- Cite supporting literature where relevant

Return ONLY valid JSON:
{{"responses": [
  {{
    "comment_ref": "Reviewer 1, Comment 1",
    "concern_summary": "one sentence",
    "response": "formal response text",
    "suggested_text": "text to add to manuscript if applicable",
    "action": "Added N=30 more participants | No change needed | Added paragraph"
  }}
]}}"""
                try:
                    raw  = think_sonnet(SHODHAK_SYSTEM, prompt, 2000)
                    data = json_parse(raw)
                    for r in data.get("responses",[]):
                        st.markdown(
                            f'<div class="result-card">'
                            f'<h4>{r.get("comment_ref","")}</h4>'
                            f'<strong>Concern:</strong> {r.get("concern_summary","")}<br><br>'
                            f'<strong>Response:</strong><br>{r.get("response","")}'
                            f'</div>',
                            unsafe_allow_html=True)
                        if r.get("suggested_text"):
                            with st.expander("Suggested text to add"):
                                st.markdown(r["suggested_text"])
                        st.markdown(
                            f'<span class="stat-chip">Action: {r.get("action","")}</span>',
                            unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════
# MODULE 9 — PATENT NOVELTY SCREENER
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "patent_screen":
    st.markdown("## ⚖️ Patent Novelty Screener")
    st.caption(
        "Check your innovation against IPO India, USPTO, and Google Patents "
        "before investing in filing fees. Powered by real patent databases.")

    st.markdown(
        '<div class="warn-box">'
        '⚖️ This is a preliminary screening tool, not legal advice. '
        'Consult a registered Patent Agent before filing.'
        '</div>',
        unsafe_allow_html=True)

    innovation = st.text_area(
        "Describe your innovation",
        placeholder="Describe what your invention does, how it works, "
                    "and what makes it different from existing solutions. "
                    "Be specific about the technical method.",
        height=120, key="pat_innovation")
    domain = st.text_input("Technical domain",
                            placeholder="Agricultural technology / Medical devices / Software",
                            key="pat_domain")

    if st.button("⚖️ Screen Patent Novelty", use_container_width=True):
        if not innovation.strip():
            st.error("Describe your innovation to screen it.")
        else:
            with st.spinner("Searching patent databases (Opus analysis)…"):
                prompt = f"""Innovation description: {innovation}
Technical domain: {domain or "general technology"}

Conduct a preliminary patent novelty analysis:

1. Identify the core inventive concept
2. List likely prior art categories to search
3. Identify key claims the innovation could make
4. Assess novelty risk areas
5. Suggest IPC (International Patent Classification) codes for India filing
6. Recommend USPTO classification codes
7. Estimate commercial viability (1-10)
8. Suggest patent strategy

Return ONLY valid JSON:
{{
  "core_concept": "one sentence",
  "inventive_steps": ["step 1", "step 2"],
  "prior_art_risk": "low|medium|high",
  "prior_art_areas": ["area 1", "area 2"],
  "potential_claims": {{
    "independent": ["claim 1"],
    "dependent": ["claim 2", "claim 3"]
  }},
  "ipc_codes": [
    {{"code": "A01B", "description": "what it covers"}}
  ],
  "uspto_classes": ["class 1"],
  "commercial_viability": 7,
  "viability_rationale": "explanation",
  "filing_strategy": {{
    "recommended_route": "Indian provisional first",
    "timeline": "File provisional within 6 months",
    "cost_estimate_inr": "₹15,000-50,000",
    "agent_type": "Patent Agent registered with IPO India"
  }},
  "search_queries": ["query to search on Google Patents"]
}}"""

                try:
                    raw  = think_sonnet(SHODHAK_SYSTEM, prompt, 2000)
                    data = json_parse(raw)
                    st.session_state.patent_results = data
                except Exception as e:
                    st.error(f"Error: {e}")

    pr = st.session_state.patent_results
    if not pr:
        st.stop()

    risk_color = {"low":"#ok-box","medium":"#warn-box","high":"#warn-box"}.get(
        pr.get("prior_art_risk","medium"),"warn-box")

    st.markdown(
        f'<div class="{risk_color}">'
        f'Prior Art Risk: <strong>{pr.get("prior_art_risk","").upper()}</strong> — '
        f'Core concept: {pr.get("core_concept","")}'
        f'</div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("Commercial Viability", f"{pr.get('commercial_viability',0)}/10")
    c2.markdown(f"**Viability:** {pr.get('viability_rationale','')}")

    with st.expander("📋 Potential Patent Claims"):
        claims = pr.get("potential_claims",{})
        st.markdown("**Independent claims:**")
        for c in claims.get("independent",[]):
            st.markdown(f"  • {c}")
        st.markdown("**Dependent claims:**")
        for c in claims.get("dependent",[]):
            st.markdown(f"  • {c}")

    with st.expander("🏛️ IPC Codes for India Filing"):
        for ipc in pr.get("ipc_codes",[]):
            st.markdown(
                f'<span class="stat-chip">{ipc.get("code","")}</span> '
                f'{ipc.get("description","")}',
                unsafe_allow_html=True)

    with st.expander("💼 Filing Strategy"):
        fs = pr.get("filing_strategy",{})
        st.markdown(f"**Route:** {fs.get('recommended_route','')}")
        st.markdown(f"**Timeline:** {fs.get('timeline','')}")
        st.markdown(f"**Cost estimate:** {fs.get('cost_estimate_inr','')}")
        st.markdown(f"**Agent:** {fs.get('agent_type','')}")

    st.markdown("**Search these queries on Google Patents:**")
    for q in pr.get("search_queries",[]):
        st.markdown(f"  🔍 [{q}](https://patents.google.com/patent/search?q={q.replace(' ','+')})")


# ══════════════════════════════════════════════════════════
# MODULE 10 — PATENT CATEGORY ADVISOR
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "patent_advisor":
    st.markdown("## 🏛️ Patent Category Advisor — India")
    st.caption("IPO India filing guidance, IPC codes, and strategy.")
    render_topic_bar()
    st.info("Describe your innovation and click Patent Novelty Screener "
            "for full analysis. This module shows India-specific filing "
            "guidance based on your innovation type.")

    inv_type = st.selectbox("Innovation type", [
        "Product / Device",
        "Process / Method",
        "Software / Algorithm",
        "Biological / Pharmaceutical",
        "Agricultural",
        "Design / Aesthetic",
        "Plant variety",
    ], key="pa_type")

    if st.button("🏛️ Get India Filing Guidance", use_container_width=True):
        prompt = f"""Innovation type: {inv_type}
Research domain: {st.session_state.domain or "general"}

Provide India-specific patent filing guidance:
- Is this patentable in India? (Patents Act 1970, Sections 3/4 exclusions)
- Recommended filing route (provisional vs complete)
- Controller of Patents office to file at
- Form numbers and fees
- Timeline from provisional to grant
- Common rejections and how to avoid them
- Specific advice for Indian researchers and students

Return ONLY valid JSON:
{{
  "patentable_in_india": true,
  "exclusions_risk": "low|medium|high",
  "exclusion_reason": "if any",
  "recommended_route": "File Form 2 provisional at Chennai Patent Office",
  "filing_forms": [{{"form": "Form 2", "purpose": "Provisional Application", "fee_inr": 1750}}],
  "timeline": "12 months provisional → 48 months grant",
  "office": "Chennai / Delhi / Kolkata / Mumbai based on your state",
  "common_rejections": ["rejection 1"],
  "student_researcher_tips": ["tip 1", "tip 2"],
  "annual_renewal_fees": "₹ amounts by year"
}}"""
        try:
            raw  = think(SHODHAK_SYSTEM, prompt, 1000)
            data = json_parse(raw)
            st.markdown(
                f'<div class="{"ok-box" if data.get("patentable_in_india") else "warn-box"}">'
                f'Patentable in India: <strong>{"Yes" if data.get("patentable_in_india") else "Risk — check exclusions"}</strong><br>'
                f'{data.get("exclusion_reason","")}'
                f'</div>',
                unsafe_allow_html=True)
            st.markdown(f"**Route:** {data.get('recommended_route','')}")
            st.markdown(f"**Office:** {data.get('office','')}")
            st.markdown(f"**Timeline:** {data.get('timeline','')}")
            for t in data.get("student_researcher_tips",[]):
                st.markdown(f"  💡 {t}")
        except Exception as e:
            st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════
# MODULE 11 — PRIOR ART MAP
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "prior_art":
    st.markdown("## 🗂️ Prior Art Map")
    render_topic_bar()
    st.caption("Map what exists so you can find what is patentable.")
    st.info(
        "Enter your innovation in Patent Novelty Screener for a full search. "
        "This module generates a structured prior art map from your topic.")

    if st.session_state.topic and st.button("🗂️ Map Prior Art", use_container_width=True):
        with st.spinner("Mapping prior art landscape…"):
            prompt = f"""Topic / Innovation area: {st.session_state.topic}

Create a prior art landscape map. Return ONLY valid JSON:
{{
  "technology_clusters": [
    {{
      "name": "cluster name",
      "description": "what this cluster covers",
      "key_players": ["companies / researchers"],
      "maturity": "emerging|growing|mature",
      "gaps": ["potential gaps in this cluster"]
    }}
  ],
  "white_spaces": ["areas not covered by existing art"],
  "crowded_areas": ["areas where novelty would be hard to establish"],
  "recommended_search_databases": [
    {{"name": "IPO India", "url": "https://iprsearch.ipindia.gov.in/"}},
    {{"name": "Google Patents", "url": "https://patents.google.com/"}},
    {{"name": "USPTO", "url": "https://patft.uspto.gov/"}}
  ]
}}"""
            try:
                raw  = think(SHODHAK_SYSTEM, prompt, 1200)
                data = json_parse(raw)
                for cluster in data.get("technology_clusters",[]):
                    with st.expander(
                        f"{cluster.get('name','')} — {cluster.get('maturity','')}"):
                        st.markdown(cluster.get("description",""))
                        if cluster.get("key_players"):
                            st.markdown(f"**Players:** {', '.join(cluster['key_players'])}")
                        for g in cluster.get("gaps",[]):
                            st.markdown(
                                f'<div class="ok-box">💡 Gap: {g}</div>',
                                unsafe_allow_html=True)
                if data.get("white_spaces"):
                    st.markdown("### White Spaces — Patentable Opportunities")
                    for ws in data["white_spaces"]:
                        st.markdown(f"  ✅ {ws}")
                st.markdown("### Search Databases")
                for db in data.get("recommended_search_databases",[]):
                    st.markdown(f"  🔗 [{db['name']}]({db['url']})")
            except Exception as e:
                st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════
# ADMIN MODULE — PRIVATE, PASSWORD PROTECTED
# ══════════════════════════════════════════════════════════
elif st.session_state.module == "admin":
    if not st.session_state.get("admin_mode"):
        st.error("Access denied.")
        st.stop()

    st.markdown("## ⚙️ Admin — Research Scaffold Builder")
    st.markdown(
        '<div class="warn-box">'
        '🔒 PRIVATE. Not public. Not marketed. Admin use only.'
        '</div>',
        unsafe_allow_html=True)

    st.markdown(
        "The full paper generation pipeline is accessible here. "
        "This module is not linked, not indexed, and not mentioned anywhere "
        "in the public product. All use is logged.")

    # Import the original pipeline lazily
    if st.button("Load Research Scaffold Pipeline"):
        st.info(
            "The original pipeline (app_v4.py) can be loaded here. "
            "Import it as a sub-module or run it on a separate Railway service. "
            "The admin layer is completely separate from the public Shodhak UI.")
        st.code(
            "# To run scaffold builder separately:\n"
            "# railway run python -m streamlit run app_v4.py "
            "--server.port 5001 --server.address 0.0.0.0",
            language="bash")


# ══════════════════════════════════════════════════════════
# FALLBACK
# ══════════════════════════════════════════════════════════
else:
    st.session_state.module = "home"
    st.rerun()
