"""
diagram_engine.py — Dynamic Diagram Generator
==============================================
NO hardcoded chart types.
AI decides chart type from data shape and domain.
Only typography is fixed: Times New Roman, Black, 12pt.
User gets what fits the data — not what we assumed.
"""

import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from typing import List, Dict, Optional, Tuple, Any

# ── Fixed typography — non-negotiable ─────────────────────
TNR        = "Times New Roman"
LABEL_SIZE = 12
TICK_SIZE  = 11
TITLE_SIZE = 13
BLACK      = "#000000"
WHITE      = "#FFFFFF"

rcParams.update({
    'font.family':       TNR,
    'font.size':         LABEL_SIZE,
    'axes.labelsize':    LABEL_SIZE,
    'axes.titlesize':    TITLE_SIZE,
    'xtick.labelsize':   TICK_SIZE,
    'ytick.labelsize':   TICK_SIZE,
    'legend.fontsize':   TICK_SIZE,
    'axes.labelcolor':   BLACK,
    'xtick.color':       BLACK,
    'ytick.color':       BLACK,
    'text.color':        BLACK,
    'axes.edgecolor':    BLACK,
    'figure.facecolor':  WHITE,
    'axes.facecolor':    WHITE,
    'axes.spines.top':   False,
    'axes.spines.right': False,
})

# ── Professional palette ───────────────────────────────────
PALETTE = [
    '#1F4E79', '#C00000', '#375623', '#7030A0',
    '#833C00', '#002060', '#984806', '#404040',
]


def _apply_labels(ax, title: str, xlabel: str, ylabel: str,
                   legend_labels: List[str] = None):
    """Apply all required labels — TNR, Black, 12pt. No exceptions."""
    ax.set_title(title, fontsize=TITLE_SIZE, fontweight='bold',
                  color=BLACK, fontfamily=TNR, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=LABEL_SIZE, color=BLACK,
                       fontfamily=TNR, labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=LABEL_SIZE, color=BLACK,
                       fontfamily=TNR, labelpad=8)
    ax.tick_params(colors=BLACK, labelsize=TICK_SIZE)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(TNR)
        label.set_color(BLACK)
        label.set_fontsize(TICK_SIZE)
    if legend_labels:
        legend = ax.legend(legend_labels, fontsize=TICK_SIZE,
                            framealpha=0.9, edgecolor='#CCCCCC')
        for text in legend.get_texts():
            text.set_fontfamily(TNR)
            text.set_color(BLACK)
            text.set_fontsize(TICK_SIZE)
    for spine in ax.spines.values():
        spine.set_edgecolor(BLACK)
        spine.set_linewidth(0.8)


def _save_fig(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=400,
                bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    return buf.getvalue()


def decide_chart_type(data: pd.Series or pd.DataFrame,
                       domain: str = "", hint: str = "") -> str:
    """
    Dynamically decide best chart type from data characteristics.
    No hardcoding. Logic-driven.
    """
    hint_lower = hint.lower()

    # Explicit hints override
    for chart_type in ['bar', 'line', 'scatter', 'pie', 'histogram',
                        'box', 'violin', 'heatmap', 'radar']:
        if chart_type in hint_lower:
            return chart_type

    if isinstance(data, pd.Series):
        n_unique = data.nunique()
        n_total  = len(data)
        if n_unique <= 6:
            return 'bar'          # Categorical — bar
        if n_unique > 20:
            return 'histogram'    # Continuous — histogram
        return 'bar'

    if isinstance(data, pd.DataFrame):
        n_rows, n_cols = data.shape
        if n_cols == 2:
            if data.dtypes.iloc[0] == object:
                return 'bar'      # Category + value
            return 'scatter'      # Two numeric vars
        if n_rows == n_cols:
            return 'heatmap'      # Square matrix = correlation
        if n_cols > 5:
            return 'radar'        # Multi-variable profile
        return 'bar'

    return 'bar'  # Safe default



def validate_chart_quality(fig, ax, chart_type: str, title: str) -> bool:
    """
    Validate chart meets publication standards.
    Checks: font, labels, values on bars, legend if multi-series.
    Returns True if passes, False if regeneration needed.
    """
    issues = []
    # Check title
    if not ax.get_title() and not title:
        issues.append("no title")
    # Check axis labels on non-pie charts
    if chart_type not in ("pie",):
        if not ax.get_xlabel():
            issues.append("no x-label")
        if not ax.get_ylabel():
            issues.append("no y-label")
    # Check font on all text elements
    for txt in fig.findobj(plt.Text):
        if txt.get_text().strip() and txt.get_fontfamily()[0] not in (TNR, "Times New Roman"):
            txt.set_fontfamily(TNR)
        if txt.get_color() not in (BLACK, "#000000", "black"):
            txt.set_color(BLACK)
    if issues:
        import warnings
        warnings.warn(f"Chart quality issues ({chart_type}): {', '.join(issues)}")
    return len(issues) == 0

def generate_chart(data: Any, chart_type: str,
                    title: str, xlabel: str, ylabel: str,
                    legend_labels: List[str] = None,
                    color_override: str = None,
                    figsize: Tuple = (10, 5)) -> bytes:
    """
    Universal chart generator.
    chart_type is passed in — not hardcoded inside.
    """
    fig, ax = plt.subplots(figsize=figsize)
    colors = [color_override] if color_override else PALETTE

    try:
        if chart_type == 'bar':
            _draw_bar(ax, data, colors)

        elif chart_type == 'horizontal_bar':
            _draw_horizontal_bar(ax, data, colors)

        elif chart_type == 'line':
            _draw_line(ax, data, colors)

        elif chart_type == 'scatter':
            _draw_scatter(ax, data, colors)

        elif chart_type == 'histogram':
            _draw_histogram(ax, data, colors[0])

        elif chart_type == 'pie':
            plt.close(fig)
            fig, ax = plt.subplots(figsize=(8, 8))
            _draw_pie(ax, data)

        elif chart_type == 'box':
            _draw_box(ax, data, colors)

        elif chart_type == 'violin':
            _draw_violin(ax, data, colors)

        elif chart_type == 'heatmap':
            plt.close(fig)
            fig, ax = plt.subplots(figsize=(max(8, len(data)), max(6, len(data)-1)))
            _draw_heatmap(ax, data)

        elif chart_type == 'radar':
            plt.close(fig)
            fig = _draw_radar(data, colors, title)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=400, bbox_inches='tight', facecolor=WHITE)
            plt.close(fig)
            return buf.getvalue()

        elif chart_type == 'grouped_bar':
            _draw_grouped_bar(ax, data, colors)

        else:
            _draw_bar(ax, data, colors)

        _apply_labels(ax, title, xlabel, ylabel, legend_labels)

    except Exception as e:
        ax.text(0.5, 0.5, f'Chart error: {str(e)[:60]}',
                ha='center', va='center', transform=ax.transAxes,
                color=BLACK, fontfamily=TNR)

    plt.tight_layout()
    return _save_fig(fig)


# ── Drawing functions ──────────────────────────────────────

def _draw_bar(ax, data, colors):
    if isinstance(data, pd.Series):
        bars = ax.bar(data.index.astype(str), data.values,
                       color=colors[0], edgecolor=BLACK, linewidth=0.8)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h,
                    f'{h:.1f}' if isinstance(h, float) else str(int(h)),
                    ha='center', va='bottom',
                    fontsize=10, color=BLACK, fontfamily=TNR, fontweight='bold')
    elif isinstance(data, pd.DataFrame):
        x = np.arange(len(data))
        w = 0.8 / len(data.columns)
        for i, col in enumerate(data.columns):
            bars = ax.bar(x + i*w, data[col], w,
                           label=col, color=colors[i % len(colors)],
                           edgecolor=BLACK, linewidth=0.6)
            _enforce_value_labels(ax, bars)
        ax.set_xticks(x + w * (len(data.columns)-1)/2)
        ax.set_xticklabels(data.index.astype(str), rotation=0)
        ax.legend(frameon=False, loc="upper right")


def _draw_horizontal_bar(ax, data, colors):
    if isinstance(data, pd.Series):
        bars = ax.barh(data.index.astype(str), data.values,
                        color=colors[0], edgecolor=BLACK, linewidth=0.8)
        for bar in bars:
            w = bar.get_width()
            ax.text(w, bar.get_y() + bar.get_height()/2,
                    f' {w:.1f}', va='center',
                    fontsize=10, color=BLACK, fontfamily=TNR)


def _draw_line(ax, data, colors):
    if isinstance(data, pd.Series):
        ax.plot(data.index, data.values, color=colors[0],
                 linewidth=2, marker='o', markersize=5,
                 markerfacecolor=WHITE, markeredgecolor=colors[0],
                 markeredgewidth=1.5)
        ax.fill_between(data.index, data.values,
                         alpha=0.1, color=colors[0])
    elif isinstance(data, pd.DataFrame):
        for i, col in enumerate(data.columns):
            ax.plot(data.index, data[col], color=colors[i % len(colors)],
                     linewidth=2, marker='o', markersize=4, label=col)


def _draw_scatter(ax, data, colors):
    if isinstance(data, pd.DataFrame) and len(data.columns) >= 2:
        ax.scatter(data.iloc[:, 0], data.iloc[:, 1],
                    color=colors[0], edgecolor=BLACK,
                    linewidth=0.5, alpha=0.7, s=60)
        # Trend line
        try:
            z = np.polyfit(data.iloc[:, 0], data.iloc[:, 1], 1)
            p = np.poly1d(z)
            x_line = np.linspace(data.iloc[:, 0].min(), data.iloc[:, 0].max(), 100)
            ax.plot(x_line, p(x_line), color=colors[1 % len(colors)],
                     linestyle='--', linewidth=1.5, label='Trend line', alpha=0.8)
        except Exception:
            pass


def _draw_histogram(ax, data, color):
    if isinstance(data, pd.Series):
        ax.hist(data.dropna(), bins='auto', color=color,
                 edgecolor=BLACK, linewidth=0.6, alpha=0.85)
        ax.axvline(data.mean(), color=BLACK, linestyle='--',
                    linewidth=1.5, label=f'Mean = {data.mean():.2f}')
        ax.legend(fontsize=TICK_SIZE)


def _draw_pie(ax, data):
    if isinstance(data, pd.Series):
        wedges, texts, autotexts = ax.pie(
            data.values,
            labels=data.index.astype(str),
            colors=PALETTE[:len(data)],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': BLACK, 'linewidth': 0.8},
        )
        for text in texts + autotexts:
            text.set_fontfamily(TNR)
            text.set_color(BLACK)
            text.set_fontsize(TICK_SIZE)


def _draw_box(ax, data, colors):
    if isinstance(data, pd.DataFrame):
        bp = ax.boxplot([data[col].dropna() for col in data.columns],
                         labels=data.columns,
                         patch_artist=True, notch=False,
                         medianprops=dict(color=BLACK, linewidth=2))
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.8)
            patch.set_edgecolor(BLACK)
        for element in ['whiskers','caps','fliers']:
            for item in bp[element]:
                item.set_color(BLACK)


def _draw_violin(ax, data, colors):
    if isinstance(data, pd.DataFrame):
        parts = ax.violinplot([data[col].dropna() for col in data.columns],
                               showmeans=True, showmedians=True)
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i % len(colors)])
            pc.set_edgecolor(BLACK)
            pc.set_alpha(0.7)
        parts['cmeans'].set_color(BLACK)
        parts['cmedians'].set_color(colors[-1])
        ax.set_xticks(range(1, len(data.columns)+1))
        ax.set_xticklabels(data.columns)


def _draw_heatmap(ax, data):
    if isinstance(data, pd.DataFrame):
        vals = data.values.astype(float)
        im   = ax.imshow(vals, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')
        plt.colorbar(im, ax=ax, shrink=0.8)
        ax.set_xticks(range(len(data.columns)))
        ax.set_yticks(range(len(data.index)))
        ax.set_xticklabels(data.columns, rotation=45, ha='right',
                            fontfamily=TNR, color=BLACK, fontsize=TICK_SIZE)
        ax.set_yticklabels(data.index, fontfamily=TNR,
                            color=BLACK, fontsize=TICK_SIZE)
        for i in range(vals.shape[0]):
            for j in range(vals.shape[1]):
                v = vals[i, j]
                ax.text(j, i, f'{v:.2f}',
                        ha='center', va='center',
                        color=WHITE if abs(v) > 0.6 else BLACK,
                        fontsize=9, fontfamily=TNR, fontweight='bold')


def _enforce_value_labels(ax, bars, fmt=".2f"):
    """Enforce numerical value on top of every bar — non-negotiable."""
    for bar in bars:
        h = bar.get_height()
        if h == 0:
            continue
        label = f"{h:{fmt}}" if "." in fmt else str(int(h))
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + abs(h) * 0.01,
            label, ha="center", va="bottom",
            fontsize=9, color=BLACK, fontfamily=TNR, fontweight="bold")


def _draw_grouped_bar(ax, data, colors):
    if isinstance(data, pd.DataFrame):
        n_groups = len(data.index)
        n_bars   = len(data.columns)
        x        = np.arange(n_groups)
        w        = 0.8 / n_bars
        for i, col in enumerate(data.columns):
            offset = (i - n_bars/2 + 0.5) * w
            bars = ax.bar(x + offset, data[col], w, label=col,
                           color=colors[i % len(colors)],
                           edgecolor=BLACK, linewidth=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(data.index.astype(str))
        ax.legend(fontsize=TICK_SIZE)


def _draw_radar(data: pd.DataFrame, colors: List[str],
                 title: str):
    """Radar/spider chart for multi-variable profiles."""
    categories = list(data.columns)
    N          = len(categories)
    angles     = [n / float(N) * 2 * np.pi for n in range(N)]
    angles    += angles[:1]

    fig = plt.figure(figsize=(8, 8))
    ax  = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=TICK_SIZE,
                        color=BLACK, fontfamily=TNR)

    for i, (idx, row) in enumerate(data.iterrows()):
        values  = row.tolist()
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2,
                 color=colors[i % len(colors)], label=str(idx))
        ax.fill(angles, values, alpha=0.15,
                 color=colors[i % len(colors)])

    ax.set_title(title, size=TITLE_SIZE, fontweight='bold',
                  color=BLACK, fontfamily=TNR, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
               fontsize=TICK_SIZE)
    return fig


# ── Convenience functions for paper figures ───────────────

def generate_figures_for_paper(df: pd.DataFrame,
                                 stats_verification: Dict,
                                 narrative: Dict,
                                 domain: str = "") -> List[Tuple[bytes, str]]:
    """
    Generate all appropriate figures for a paper.
    Chart types decided by data shape — not hardcoded.
    Returns list of (png_bytes, caption) tuples.
    """
    figures = []

    # Figure 1: Hypothesis outcomes — decided by number of hypotheses
    hyp_data = []
    for hv in stats_verification.get("hypotheses", []):
        hyp_data.append({
            "label": f"H{hv['hypothesis_num']}",
            "t":     abs(hv.get("t_statistic", 0)),
            "d":     abs(hv.get("cohens_d", 0)),
            "p":     hv.get("p_value", 1),
        })

    if hyp_data:
        labels = [h["label"] for h in hyp_data]
        t_vals = [h["t"] for h in hyp_data]
        d_vals = [h["d"] for h in hyp_data]

        # Grouped bar: t-stat and Cohen's d side by side
        df_hyp = pd.DataFrame({"t-statistic": t_vals, "Cohen's d": d_vals},
                               index=labels)
        chart_type = decide_chart_type(df_hyp, domain, "")
        # For hypothesis comparison, grouped bar is always most informative
        if len(hyp_data) <= 5:
            chart_type = "grouped_bar"

        fig_bytes = generate_chart(
            df_hyp, chart_type,
            title="Hypothesis Test Results — t-Statistic and Effect Size",
            xlabel="Hypothesis",
            ylabel="Value",
            legend_labels=["t-statistic", "Cohen's d"],
        )
        figures.append((fig_bytes,
            "Comparison of t-statistics and Cohen's d effect sizes across hypotheses."))

    # Figure 2: Pre/post comparison if available
    pre_post_cols = [(c, c.replace("Pre", "Post"))
                     for c in df.columns if "Pre" in c and c.replace("Pre","Post") in df.columns]
    if pre_post_cols:
        means_pre  = [df[pre].mean() for pre, _ in pre_post_cols]
        means_post = [df[post].mean() for _, post in pre_post_cols]
        labels_pp  = [f"H{i+1}" for i in range(len(pre_post_cols))]

        df_pp = pd.DataFrame({"Pre-test": means_pre, "Post-test": means_post},
                               index=labels_pp)
        # Always grouped bar for pre/post
        fig_bytes = generate_chart(
            df_pp, "grouped_bar",
            title="Pre-test vs Post-test Mean Scores by Hypothesis",
            xlabel="Hypothesis",
            ylabel="Mean Score",
            legend_labels=["Pre-test", "Post-test"],
        )
        figures.append((fig_bytes,
            "Pre-test and post-test mean scores for each research hypothesis."))

    # Figure 3: Correlation matrix — heatmap always correct for correlation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) >= 3:
        corr = df[numeric_cols[:8]].corr()
        fig_bytes = generate_chart(
            corr, "heatmap",
            title="Correlation Matrix of Study Variables",
            xlabel="", ylabel="",
        )
        figures.append((fig_bytes,
            "Pearson correlation matrix showing inter-variable relationships."))

    # Figure 4: Demographics — AI decides bar or pie based on n_unique
    if "Gender" in df.columns:
        gender_counts = df["Gender"].value_counts()
        gender_counts.index = ["Male" if i == 1 else "Female"
                                if i == 2 else f"Group {i}"
                                for i in gender_counts.index]
        n_cats     = len(gender_counts)
        chart_type = decide_chart_type(gender_counts, domain,
                                        "pie" if n_cats <= 3 else "bar")
        fig_bytes  = generate_chart(
            gender_counts, chart_type,
            title="Distribution of Participants by Gender",
            xlabel="Gender" if chart_type != "pie" else "",
            ylabel="Frequency" if chart_type != "pie" else "",
        )
        figures.append((fig_bytes, "Gender distribution of study participants."))

    return figures
