"""
likert_engine.py — Likert Construct Editor & Table Generator
=============================================================
- AI generates constructs with minimum 5 items each (8 for Indian studies)
- User edits every item
- SPSS-style tables with row/column totals
- Crosstabulation with AI suggestions
- Combined or separate tables
- Black labels, Times New Roman, vibrant fills
"""

import streamlit as st
import json
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
import io
from typing import List, Dict, Optional, Tuple

# ── Typography ─────────────────────────────────────────────
rcParams['font.family']      = 'Times New Roman'
rcParams['font.size']        = 11
rcParams['axes.labelcolor']  = 'black'
rcParams['xtick.color']      = 'black'
rcParams['ytick.color']      = 'black'
rcParams['text.color']       = 'black'
rcParams['axes.edgecolor']   = 'black'
rcParams['figure.facecolor'] = 'white'
rcParams['axes.facecolor']   = 'white'

# ── Vibrant but professional color palette (black labels) ──
CHART_COLORS = [
    '#1F4E79',  # Deep navy
    '#C00000',  # Deep red
    '#375623',  # Dark green
    '#7030A0',  # Purple
    '#833C00',  # Brown
    '#002060',  # Dark blue
    '#984806',  # Dark orange
    '#4F4F4F',  # Dark grey
]

LIKERT_LABELS = {
    5: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    4: ["Strongly Disagree", "Disagree", "Agree", "Strongly Agree"],
    3: ["Disagree", "Neutral", "Agree"],
}

MIN_ITEMS_INDIA = 8   # Indian studies standard
MIN_ITEMS_BASIC = 5   # Absolute minimum


def generate_constructs_prompt(domain: str, hypotheses: List[str],
                                n_constructs: int = 3,
                                items_per_construct: int = 8) -> str:
    return f"""Generate a Likert questionnaire for this research:
Domain: {domain}
Hypotheses: {'; '.join(hypotheses[:3])}

Requirements:
- {n_constructs} constructs (one per hypothesis)
- EXACTLY {items_per_construct} items per construct (Indian studies standard)
- Likert scale: 1=Strongly Disagree to 5=Strongly Agree
- Items must be positively worded (no negations)
- Academic language, measurable, not ambiguous

Return ONLY valid JSON:
{{
  "constructs": [
    {{
      "id": "C1",
      "name": "Construct Name (e.g. Working Memory Performance)",
      "hypothesis": "H1",
      "items": [
        {{"id": "C1Q1", "text": "Full item text here as it would appear in questionnaire."}},
        {{"id": "C1Q2", "text": "..."}},
        ... exactly {items_per_construct} items
      ]
    }},
    ...
  ],
  "demographic_items": [
    {{"id": "D1", "text": "Age", "type": "range", "options": ["18-25", "26-35", "36-45", "46+"]}},
    {{"id": "D2", "text": "Gender", "type": "categorical", "options": ["Male", "Female", "Other"]}},
    {{"id": "D3", "text": "Educational Qualification", "type": "categorical", "options": ["Graduate", "Post-Graduate", "PhD", "Other"]}},
    {{"id": "D4", "text": "Years of Experience", "type": "range", "options": ["0-5", "6-10", "11-20", "20+"]}}
  ]
}}
Return ONLY valid JSON. No markdown."""


def render_construct_editor(constructs: List[Dict],
                             claude_call_fn=None,
                             domain: str = "",
                             hypotheses: List[str] = None) -> List[Dict]:
    """
    Render editable Likert construct items. Returns updated constructs.

    Tabs per construct:
      Basic  — rename construct, edit / delete / add items
      Advanced — bulk regenerate all items via AI (requires claude_call_fn)

    claude_call_fn: optional callable(system, prompt, max_tokens) → str
                    If None, Advanced tab shows a disabled state.
    """
    if not constructs:
        return constructs

    updated = []
    for ci, construct in enumerate(constructs):
        c_name  = construct.get("name", f"Construct {ci+1}")
        c_hyp   = construct.get("hypothesis", "")
        items   = construct.get("items", [])
        n_items = len(items)

        # ── Minimum-count badge ───────────────────────────────────────
        if n_items < MIN_ITEMS_BASIC:
            badge = f'⛔ {n_items} items — BELOW MINIMUM ({MIN_ITEMS_BASIC})'
        elif n_items < MIN_ITEMS_INDIA:
            badge = f'⚠️ {n_items} items — below Indian standard ({MIN_ITEMS_INDIA})'
        else:
            badge = f'✅ {n_items} items'

        with st.expander(
            f"📋 {c_name} ({c_hyp}) — {badge}", expanded=False
        ):
            # Count-validation alert inside expander
            if n_items < MIN_ITEMS_BASIC:
                st.markdown(
                    f'<div class="warn-box">⛔ CRITICAL: {n_items} items. Minimum is {MIN_ITEMS_BASIC}. Cronbach alpha will be unreliable. Indian studies require {MIN_ITEMS_INDIA}.</div>',
                    unsafe_allow_html=True)
            elif n_items < MIN_ITEMS_INDIA:
                st.markdown(
                    f'<div class="warn-box">⚠️ {n_items} items. Indian reviewers expect {MIN_ITEMS_INDIA}+ per construct.</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="ok-box">✅ {n_items} items — Indian studies standard met.</div>',
                    unsafe_allow_html=True)

            # ── Tabs: Basic / Advanced ────────────────────────────────
            tab_basic, tab_advanced = st.tabs(["✏️ Basic Edit", "⚙️ Advanced"])

            # ── BASIC TAB ─────────────────────────────────────────────
            with tab_basic:
                construct_name = st.text_input(
                    "Construct Name", value=c_name,
                    key=f"cn_{ci}",
                    help="Name used as CSV column prefix and in paper.")

                st.caption(f"Minimum 5 items required. Indian studies standard: 8+.")
                updated_items = []
                for ii, item in enumerate(items):
                    col1, col2 = st.columns([5, 1])
                    new_text = col1.text_input(
                        f"Item {ii+1}",
                        value=item.get("text", ""),
                        key=f"item_{ci}_{ii}",
                        label_visibility="collapsed")
                    if col2.button("✕", key=f"del_item_{ci}_{ii}",
                                   help="Delete this item"):
                        if len(updated_items) + (n_items - ii - 1) >= MIN_ITEMS_BASIC:
                            continue   # delete only if min still met
                        else:
                            st.warning(f"Cannot delete — must keep at least {MIN_ITEMS_BASIC} items.")
                    updated_items.append({**item, "text": new_text})

                # Add item button
                if st.button(f"＋ Add Item", key=f"add_item_{ci}"):
                    updated_items.append({
                        "id": f"C{ci+1}Q{len(updated_items)+1}",
                        "text": "New questionnaire item — click to edit."
                    })

                # Ensure minimum 5 items always
                while len(updated_items) < MIN_ITEMS_BASIC:
                    n_now = len(updated_items)
                    updated_items.append({
                        "id": f"C{ci+1}Q{n_now+1}",
                        "text": f"Item {n_now+1} — please edit this placeholder."
                    })

            # ── ADVANCED TAB ──────────────────────────────────────────
            with tab_advanced:
                st.markdown("**Regenerate all items for this construct using AI.**")
                st.caption(
                    "Rewrites every item from scratch. Your manual edits "
                    "in Basic tab are overwritten. Use after construct rename.")

                n_regen = st.number_input(
                    "Items to generate", min_value=MIN_ITEMS_BASIC,
                    max_value=20, value=max(MIN_ITEMS_INDIA, n_items),
                    key=f"regen_n_{ci}",
                    help=f"Min {MIN_ITEMS_BASIC}. Indian standard: {MIN_ITEMS_INDIA}.")

                scale_type = st.selectbox(
                    "Scale type",
                    ["1=Strongly Disagree to 5=Strongly Agree (Likert)",
                     "1=Never to 5=Always (Frequency)",
                     "1=Very Poor to 5=Excellent (Quality)",
                     "1=Strongly Oppose to 5=Strongly Support (Attitude)"],
                    key=f"scale_type_{ci}")

                regen_note = st.text_area(
                    "Additional instructions (optional)",
                    placeholder="e.g. Focus on classroom behaviour, avoid negated items",
                    key=f"regen_note_{ci}", height=68)

                if claude_call_fn is None:
                    st.info("AI regeneration unavailable in this context.")
                elif st.button(f"🔄 Regenerate Items for {c_name}",
                               key=f"regen_btn_{ci}",
                               use_container_width=True):
                    with st.spinner(f"Generating {n_regen} items…"):
                        regen_prompt = (
                            f"You are an expert psychometrician.\n"
                            f"Construct: {c_name} (Hypothesis: {c_hyp})\n"
                            f"Domain: {domain or 'Research'}\n"
                            f"Hypotheses context: {(hypotheses or [])[:2]}\n"
                            f"Scale: {scale_type.split('(')[0].strip()}\n"
                            f"Extra instructions: {regen_note or 'None'}\n\n"
                            f"Generate EXACTLY {n_regen} Likert items.\n"
                            f"Rules: positively worded, academic language, "
                            f"no negations, measurable, not ambiguous.\n"
                            f"Each item ≥ 8 words.\n\n"
                            f"Return ONLY valid JSON, no markdown:\n"
                            f"{{\"items\": [\"Item text 1\", \"Item text 2\", ...]}}\n"
                            f"Exactly {n_regen} strings in the array."
                        )
                        try:
                            raw = claude_call_fn(
                                "You are a psychometrics expert. Return only JSON.",
                                regen_prompt, 1200)
                            raw = re.sub(r'```json|```', '', raw).strip()
                            data = json.loads(raw)
                            new_item_texts = data.get("items", [])
                            if len(new_item_texts) >= MIN_ITEMS_BASIC:
                                updated_items = [
                                    {"id": f"C{ci+1}Q{qi+1}", "text": txt}
                                    for qi, txt in enumerate(new_item_texts)
                                ]
                                st.success(
                                    f"✅ {len(updated_items)} items generated. "
                                    f"Switch to Basic tab to review.")
                            else:
                                st.error(
                                    f"AI returned only {len(new_item_texts)} items. "
                                    f"Try again or edit manually.")
                        except Exception as _e:
                            st.error(f"Regeneration failed: {_e}. Try again.")

            # ── Commit this construct ─────────────────────────────────
            updated.append({
                **construct,
                "name":  construct_name if 'construct_name' in dir() else c_name,
                "items": updated_items,
            })

    return updated


def generate_spss_frequency_table(df: pd.DataFrame, column: str,
                                   labels: List[str] = None) -> pd.DataFrame:
    """Generate SPSS-style frequency table with row totals."""
    counts = df[column].value_counts().sort_index()
    total  = len(df)

    rows = []
    cum_pct = 0.0
    for val in sorted(counts.index):
        count  = int(counts[val])
        pct    = round(count / total * 100, 1)
        cum_pct = round(cum_pct + pct, 1)
        label  = labels[int(val)-1] if labels and 0 < int(val) <= len(labels) else str(val)
        rows.append({
            "Value": int(val),
            "Label": label,
            "Frequency": count,
            "Percent (%)": pct,
            "Valid Percent (%)": pct,
            "Cumulative Percent (%)": min(cum_pct, 100.0),
        })

    # Totals row
    rows.append({
        "Value": "Total",
        "Label": "Total",
        "Frequency": total,
        "Percent (%)": 100.0,
        "Valid Percent (%)": 100.0,
        "Cumulative Percent (%)": 100.0,
    })

    return pd.DataFrame(rows)


def generate_crosstab(df: pd.DataFrame, row_var: str, col_var: str,
                       row_labels: List[str] = None,
                       col_labels: List[str] = None) -> pd.DataFrame:
    """Generate SPSS-style crosstabulation with row, column, and grand totals."""
    ct = pd.crosstab(df[row_var], df[col_var], margins=True, margins_name="Total")

    # Rename index/columns if labels provided
    if row_labels:
        ct.index = [row_labels[i-1] if isinstance(i, int) and 0 < i <= len(row_labels) else str(i) for i in ct.index]
    if col_labels:
        ct.columns = [col_labels[i-1] if isinstance(i, int) and 0 < i <= len(col_labels) else str(i) for i in ct.columns]

    return ct


def suggest_crosstabs(constructs: List[Dict], demo_items: List[Dict]) -> List[Dict]:
    """AI-style crosstab suggestions based on constructs and demographics."""
    suggestions = []
    construct_names = [c.get("name","C") for c in constructs]
    demo_names      = [d.get("text","D") for d in demo_items]

    # Standard academic crosstabs
    for demo in demo_names[:4]:
        for construct in construct_names[:2]:
            suggestions.append({
                "row": demo,
                "col": construct,
                "rationale": f"Compare {construct} across {demo} groups — standard demographic analysis"
            })

    # Construct-construct crosstabs
    if len(construct_names) >= 2:
        suggestions.append({
            "row": construct_names[0],
            "col": construct_names[1],
            "rationale": f"Examine relationship between {construct_names[0]} and {construct_names[1]}"
        })

    return suggestions[:6]


def plot_frequency_bar(freq_df: pd.DataFrame, title: str,
                        color_idx: int = 0) -> bytes:
    """SPSS-style bar chart. Black labels, Times New Roman, vibrant fill."""
    data = freq_df[freq_df["Label"] != "Total"].copy()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(data["Label"], data["Frequency"],
                   color=CHART_COLORS[color_idx % len(CHART_COLORS)],
                   edgecolor='black', linewidth=0.8, width=0.6)

    # Value labels on bars — BLACK
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3,
                f'{int(h)}', ha='center', va='bottom',
                fontsize=11, color='black',
                fontfamily='Times New Roman', fontweight='bold')

    ax.set_title(title, fontsize=13, fontweight='bold',
                  color='black', fontfamily='Times New Roman', pad=12)
    ax.set_xlabel("Response Category", fontsize=11, color='black',
                   fontfamily='Times New Roman')
    ax.set_ylabel("Frequency", fontsize=11, color='black',
                   fontfamily='Times New Roman')
    ax.tick_params(colors='black')
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
    plt.xticks(rotation=15, ha='right', fontsize=10, color='black')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()
    return buf.getvalue()


def plot_stacked_bar(df: pd.DataFrame, constructs: List[Dict],
                      title: str = "Construct Response Profile") -> bytes:
    """Stacked bar chart for construct comparison. Black labels."""
    construct_means = {}
    for c in constructs:
        cols = [f"Scale_Q{i+1}" for i in range(len(c.get("items",[])))]
        valid_cols = [col for col in cols if col in df.columns]
        if valid_cols:
            construct_means[c.get("name","C")] = df[valid_cols].mean().mean()

    if not construct_means:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                transform=ax.transAxes, color='black')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        return buf.getvalue()

    fig, ax = plt.subplots(figsize=(10, 5))
    names  = list(construct_means.keys())
    values = list(construct_means.values())
    colors = CHART_COLORS[:len(names)]

    bars = ax.bar(names, values, color=colors, edgecolor='black', linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom',
                fontsize=11, color='black', fontfamily='Times New Roman',
                fontweight='bold')

    ax.axhline(y=3.0, color='black', linestyle='--', linewidth=1, alpha=0.5,
                label='Neutral (3.0)')
    ax.set_ylim(0, 5.5)
    ax.set_title(title, fontsize=13, fontweight='bold',
                  color='black', fontfamily='Times New Roman')
    ax.set_ylabel("Mean Score (1–5 Likert)", fontsize=11, color='black',
                   fontfamily='Times New Roman')
    ax.legend(fontsize=10, framealpha=0.9)
    ax.tick_params(colors='black')
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
    plt.xticks(rotation=10, ha='right', color='black')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return buf.getvalue()


def plot_correlation_heatmap(df: pd.DataFrame,
                              title: str = "Correlation Matrix") -> bytes:
    """Correlation heatmap. Black labels, professional look."""
    scale_cols = [c for c in df.columns if c.startswith("Scale_Q") or c.startswith("H")]
    if len(scale_cols) < 2:
        scale_cols = df.select_dtypes(include=[np.number]).columns[:8].tolist()

    if len(scale_cols) < 2:
        return b""

    corr = df[scale_cols].corr()
    n    = len(scale_cols)

    fig, ax = plt.subplots(figsize=(max(8, n), max(6, n-1)))

    # Manual heatmap with black labels
    im = ax.imshow(corr.values, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(scale_cols, rotation=45, ha='right',
                        fontsize=9, color='black', fontfamily='Times New Roman')
    ax.set_yticklabels(scale_cols, fontsize=9, color='black',
                        fontfamily='Times New Roman')

    # Cell values
    for i in range(n):
        for j in range(n):
            val = corr.values[i, j]
            color = 'white' if abs(val) > 0.6 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    fontsize=8, color=color, fontweight='bold',
                    fontfamily='Times New Roman')

    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title, fontsize=13, fontweight='bold',
                  color='black', fontfamily='Times New Roman', pad=12)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return buf.getvalue()
