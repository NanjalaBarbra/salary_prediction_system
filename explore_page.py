"""
explore_page.py
───────────────
Data exploration page for the Salary Prediction App.

Displays interactive charts derived from the Stack Overflow Developer Survey
so users can understand salary trends before making their own prediction.

Charts are intentionally read-only / non-interactive — they are pre-computed
from the full dataset and cached so the page loads fast on repeat visits.

Sections
────────
1. Helper utilities  — data cleaning, chart styling
2. Data loading      — reads and cleans the CSV once, caches the result
3. show_explore_page — the Streamlit page function called from app.py
   a. Header + KPI row
   b. Row 1  — Country distribution (pie) + Avg salary by country (bar)
   c. Row 2  — Salary vs experience (line) + Salary by education (bar)
   d. Row 3  — Salary by employment type + Salary by undergrad major
   e. Row 4  — Salary by web framework (full width)
   f. Row 5  — Salary by dev type (full width)   ← NEW
   g. Row 6  — Top languages by salary (full width) ← NEW
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ══════════════════════════════════════════════════════════════
# 1. HELPER UTILITIES
# ══════════════════════════════════════════════════════════════

def shorten_categories(categories, cutoff):
    """
    Collapse rare categories into 'other'.

    Any category whose count is below `cutoff` is relabelled 'other'.
    Returns a dict  {original_value: mapped_value}  suitable for .map().
    """
    categorical_map = {}
    for i in range(len(categories)):
        if categories.values[i] >= cutoff:
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            categorical_map[categories.index[i]] = "other"
    return categorical_map


def clean_experience(x):
    """Convert free-text experience strings to a numeric float (years)."""
    if pd.isnull(x):
        return 0.5
    if x == "More than 50 years":
        return 50
    if x == "Less than 1 year":
        return 0.5
    try:
        return float(x)
    except (ValueError, TypeError):
        return 0.5


def clean_education(x):
    """Bucket granular education labels into four broad categories."""
    if pd.isnull(x):
        return "Less than Bachelor's"
    if "Bachelor's degree" in x:
        return "Bachelor's degree"
    if "Master's degree" in x:
        return "Master's degree"
    if "Professional degree" in x or "Other doctoral" in x:
        return "Post grad"
    return "Less than Bachelor's"


def clean_undergrad_major(x):
    """Map raw undergrad major text to a standardised short label."""
    if pd.isnull(x):
        return "Unknown"
    x = x.lower()
    if "computer science" in x or "software engineering" in x or "computer engineering" in x:
        return "CS/Software Eng"
    elif "information systems" in x or "information technology" in x or "system administration" in x:
        return "IT/Systems"
    elif "engineering" in x:
        return "Other Engineering"
    elif "natural science" in x:
        return "Natural Sciences"
    elif "web development" in x or "web design" in x:
        return "Web Dev/Design"
    elif "mathematics" in x or "statistics" in x:
        return "Math/Stats"
    elif "business" in x:
        return "Business"
    elif "humanities" in x:
        return "Humanities"
    elif "social science" in x:
        return "Social Sciences"
    elif "fine arts" in x or "performing arts" in x:
        return "Arts"
    elif "never declared" in x:
        return "Undeclared"
    elif "health science" in x:
        return "Health Sciences"
    else:
        return "Other"


def clean_devtype(x):
    """
    Simplify developer type strings.

    Some respondents list multiple roles separated by ';'.
    We take only the first role to keep the chart readable.
    """
    if pd.isnull(x):
        return "Unknown"
    # Take the first listed role and strip whitespace
    first = x.split(";")[0].strip()
    # Shorten common verbose labels
    replacements = {
        "Developer, full-stack": "Full-stack Dev",
        "Developer, back-end": "Back-end Dev",
        "Developer, front-end": "Front-end Dev",
        "Developer, mobile": "Mobile Dev",
        "Developer, desktop or enterprise applications": "Desktop/Enterprise Dev",
        "Developer, embedded applications or devices": "Embedded Dev",
        "Developer, QA or test": "QA/Test Dev",
        "Developer, game or graphics": "Game/Graphics Dev",
        "Engineer, data": "Data Engineer",
        "Engineer, site reliability": "Site Reliability Eng",
        "Data scientist or machine learning specialist": "Data Scientist / ML",
        "Database administrator": "DBA",
        "DevOps specialist": "DevOps",
        "System administrator": "Sys Admin",
        "Product manager": "Product Manager",
        "Scientist": "Scientist",
        "Designer": "Designer",
        "Educator": "Educator",
        "Senior Executive (C-Suite, VP, etc.)": "C-Suite / VP",
        "Marketing or sales professional": "Marketing / Sales",
    }
    return replacements.get(first, first)


# ══════════════════════════════════════════════════════════════
# 2. DATA LOADING  (cached — runs once per Streamlit session)
# ══════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """
    Read the 2025 survey CSV and return a cleaned DataFrame.

    Columns kept
    ────────────
    Country, EdLevel, Experience, Employment,
    WebframeHaveWorkedWith, DevType,
    LanguageHaveWorkedWith, Salary

    Cleaning steps
    ──────────────
    - Salary: drop nulls, keep $5k–$500k range
    - Experience: already numeric in 2025 survey
    - Employment: map to Full-time / Freelancer / Student / other
    - Country: collapse rare countries to 'other' (< 400 respondents)
    - EdLevel: bucket into four levels
    - DevType: take primary role, shorten label
    - LanguageHaveWorkedWith: semicolon-separated — exploded later per chart
    """
    df = pd.read_csv("data/survey_results_public.csv", low_memory=False)

    # 2025 column names — different from 2020
    wanted = ["Country", "EdLevel", "WorkExp", "Employment",
              "WebframeHaveWorkedWith",
              "DevType", "LanguageHaveWorkedWith", "ConvertedCompYearly"]
    available = [c for c in wanted if c in df.columns]
    df = df[available]

    # Rename for clarity
    rename_map = {"ConvertedCompYearly": "Salary", "WorkExp": "Experience"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop rows missing salary
    df = df[df["Salary"].notnull()]

    # Experience — already numeric in 2025, just clip extremes
    df["Experience"] = pd.to_numeric(df["Experience"], errors="coerce")
    df = df[df["Experience"].notnull()]
    df["Experience"] = df["Experience"].clip(0, 50)

    # Employment
    df["Employment"] = df["Employment"].apply(lambda x:
        "Full-time"            if pd.notna(x) and str(x).startswith("Employed")
        else "Freelancer"      if pd.notna(x) and ("contractor" in str(x).lower() or "freelancer" in str(x).lower())
        else "Student"         if pd.notna(x) and str(x) == "Student"
        else "other"
    )

    country_map = shorten_categories(df["Country"].value_counts(), 400)
    df["Country"] = df["Country"].map(country_map)

    if "WebframeHaveWorkedWith" in df.columns:
        web_map = shorten_categories(df["WebframeHaveWorkedWith"].value_counts(), 400)
        df["WebframeHaveWorkedWith"] = df["WebframeHaveWorkedWith"].map(web_map)

    df["EdLevel"] = df["EdLevel"].apply(clean_education)

    if "DevType" in df.columns:
        df["DevType"] = df["DevType"].apply(clean_devtype)

    # Salary range filter
    df = df[(df["Salary"] >= 5_000) & (df["Salary"] <= 500_000)]

    return df


# Load once at module level so all functions share it
df = load_data()

# ── Shared colour palette (used across all charts) ──
PALETTE = [
    "#5B9BD5", "#10b981", "#f472b6", "#fbbf24", "#34d399",
    "#818cf8", "#fb923c", "#a78bfa", "#22d3ee", "#f87171",
    "#4ade80", "#60a5fa", "#e879f9", "#facc15", "#2dd4bf",
]


# ══════════════════════════════════════════════════════════════
# CHART STYLE HELPER
# ══════════════════════════════════════════════════════════════

def _style_ax(ax, title, xlabel="", ylabel=""):
    """
    Apply a consistent visual style to a matplotlib Axes object.

    - Light blue-grey background
    - Subtle grid lines on the value axis only
    - Muted axis labels and tick colours
    """
    ax.set_facecolor("#f8faff")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#1e293b", pad=12)
    ax.set_xlabel(xlabel, fontsize=10, color="#64748b")
    ax.set_ylabel(ylabel, fontsize=10, color="#64748b")
    ax.tick_params(colors="#64748b", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


# ══════════════════════════════════════════════════════════════
# 3. PAGE FUNCTION  (called from app.py)
# ══════════════════════════════════════════════════════════════

def show_explore_page():
    """
    Render the full Explore page inside Streamlit.

    Layout
    ──────
    Header + 4 KPI pills
    Row 1 : Country pie  |  Avg salary by country
    Row 2 : Salary vs experience  |  Salary by education
    Row 3 : Salary by employment  |  Salary by undergrad major
    Row 4 : Salary by web framework  (full width)
    Row 5 : Salary by developer type (full width)   ← new
    Row 6 : Top languages by salary  (full width)   ← new
    """

    # ── Page-level CSS (typography + card styles) ──
    st.html("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
        .main .block-container { padding-top: 1.5rem !important; max-width: 100% !important; }
        .ep-header   { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#0f172a; letter-spacing:-0.02em; margin-bottom:0.2rem; }
        .ep-sub      { font-family:'DM Sans',sans-serif; font-size:0.93rem; color:#64748b; margin-bottom:1.5rem; }
        .ep-eyebrow  { font-family:'DM Sans',sans-serif; font-size:0.7rem; font-weight:600; letter-spacing:0.15em; text-transform:uppercase; color:#6366f1; margin-bottom:0.2rem; }
        .ep-card     { background:#fff; border-radius:18px; padding:1.5rem; border:1px solid #e2e8f0; box-shadow:0 4px 20px rgba(99,102,241,0.07); margin-bottom:1rem; }
        .ep-card-title { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#0f172a; margin-bottom:0.2rem; }
        .ep-card-sub { font-family:'DM Sans',sans-serif; font-size:0.8rem; color:#94a3b8; margin-bottom:1rem; }

        </style>
    """)

    # ── a. Header ──
    st.html('<div class="ep-eyebrow">Stack Overflow Developer Survey 2025</div>')
    st.html('<div class="ep-header">Explore Developer Salaries</div>')
    st.html('<div class="ep-sub">Visual breakdown of the data behind the salary prediction model.</div>')

    # ── KPI pills — headline numbers at a glance ──


    # ══ b. ROW 1 — Country overview ══════════════════════
    col_pie, col_bar = st.columns(2, gap="large")

    with col_pie:
        # Pie chart showing share of survey respondents per country
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Responses by Country</div>')
        st.html('<div class="ep-card-sub">Distribution of survey respondents across countries</div>')

        data = df["Country"].value_counts()
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor("#f8faff")
        wedges, texts, autotexts = ax.pie(
            data,
            labels=None,
            autopct="%1.1f%%",
            startangle=90,
            colors=PALETTE[:len(data)],
            pctdistance=0.82,
            wedgeprops={"linewidth": 2, "edgecolor": "white"},
        )
        for at in autotexts:
            at.set_fontsize(8)
            at.set_color("white")
            at.set_fontweight("bold")
        ax.axis("equal")
        ax.legend(wedges, data.index,
                  loc="lower center", bbox_to_anchor=(0.5, -0.18),
                  ncol=3, fontsize=8, frameon=False, labelcolor="#475569")
        ax.set_title("Country Distribution", fontsize=13, fontweight="bold",
                     color="#1e293b", pad=10)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    with col_bar:
        # Horizontal bar — mean salary per country, sorted highest first
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Average Salary by Country</div>')
        st.html('<div class="ep-card-sub">Mean annual salary (USD) sorted highest to lowest</div>')

        data = df.groupby("Country")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.barh(data.index, data.values,
                       color=PALETTE[:len(data)],
                       edgecolor="white", linewidth=1.5, height=0.65)
        _style_ax(ax, "Mean Salary by Country", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 800, bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f}", va="center", fontsize=8, color="#475569")
        ax.tick_params(axis="y", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    # ══ c. ROW 2 — Experience & Education ════════════════
    col_exp, col_edu = st.columns(2, gap="large")

    with col_exp:
        # Line chart — salary trend as experience grows (area fill for depth)
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Salary vs Experience</div>')
        st.html('<div class="ep-card-sub">How average salary grows with years of professional coding</div>')

        data = df.groupby("Experience")["Salary"].mean().sort_index()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor("#f8faff")
        ax.fill_between(data.index, data.values, alpha=0.15, color="#5B9BD5")
        ax.plot(data.index, data.values,
                color="#5B9BD5", linewidth=2.5, marker="o",
                markersize=5, markerfacecolor="white",
                markeredgewidth=2, markeredgecolor="#5B9BD5")
        _style_ax(ax, "Salary Growth by Experience",
                  xlabel="Years of Experience", ylabel="Avg Salary (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    with col_edu:
        # Horizontal bar — mean salary by education bucket
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Salary by Education Level</div>')
        st.html('<div class="ep-card-sub">Impact of academic qualification on average salary</div>')

        data = df.groupby("EdLevel")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor("#f8faff")
        colors = ["#10b981", "#5B9BD5", "#f472b6", "#fbbf24"]
        bars = ax.barh(data.index, data.values,
                       color=colors[:len(data)],
                       edgecolor="white", linewidth=1.5, height=0.55)
        _style_ax(ax, "Mean Salary by Education", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 500, bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f}", va="center", fontsize=8.5, color="#475569")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    # ══ d. ROW 3 — Employment & Major ════════════════════
    col_emp, col_maj = st.columns(2, gap="large")

    with col_emp:
        # Vertical bar — full-time vs part-time vs other
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Salary by Employment Type</div>')
        st.html('<div class="ep-card-sub">Full-time vs part-time average earnings</div>')

        data = df.groupby("Employment")["Salary"].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.bar(data.index, data.values,
                      color=["#5B9BD5", "#10b981", "#f472b6"][:len(data)],
                      edgecolor="white", linewidth=2, width=0.45)
        _style_ax(ax, "Salary by Employment Type", ylabel="Avg Salary (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 500,
                    f"${h:,.0f}", ha="center", fontsize=9,
                    color="#475569", fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    with col_maj:
        # Horizontal bar — median salary by education level
        st.html('<div class="ep-card">')
        st.html('<div class="ep-card-title">Median Salary by Education</div>')
        st.html('<div class="ep-card-sub">How education level influences earning potential in 2025</div>')

        data = df.groupby("EdLevel")["Salary"].median().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.barh(data.index, data.values,
                       color=["#10b981", "#5B9BD5", "#f472b6", "#fbbf24"][:len(data)],
                       edgecolor="white", linewidth=1.5, height=0.55)
        _style_ax(ax, "Median Salary by Education Level", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 400, bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f}", va="center", fontsize=8, color="#475569")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.html('</div>')

    # ══ e. ROW 4 — Web Framework (full width) ════════════
    # Full-width vertical bar so all framework names fit along the x-axis
    st.html('<div class="ep-card">')
    st.html('<div class="ep-card-title">Salary by Web Framework</div>')
    st.html('<div class="ep-card-sub">Average salary across different web frameworks used</div>')

    if "WebframeHaveWorkedWith" in df.columns:
        data = df.groupby("WebframeHaveWorkedWith")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(14, 4))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.bar(data.index, data.values,
                      color=PALETTE[:len(data)],
                      edgecolor="white", linewidth=2, width=0.55)
        _style_ax(ax, "Mean Salary by Web Framework", ylabel="Avg Salary (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 300,
                    f"${h:,.0f}", ha="center", fontsize=8.5,
                    color="#475569", fontweight="bold", rotation=45)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("WebframeHaveWorkedWith column not found in dataset.")

    st.html('</div>')

    # ══ f. ROW 5 — Developer Type (full width) ═══════════
    # NEW: horizontal bar chart so long role names are readable
    # DevType was already cleaned to take the first listed role
    st.html('<div class="ep-card">')
    st.html('<div class="ep-card-title">Salary by Developer Type</div>')
    st.html('<div class="ep-card-sub">Average salary grouped by primary developer role</div>')

    if "DevType" in df.columns:
        # Calculate global median and counts per role
        dev_df = df[df["DevType"] != "Unknown"]
        global_median = dev_df["Salary"].mean()

        # Group data and filter for sample size
        dev_stats = dev_df.groupby("DevType")["Salary"].agg(["mean", "count"]).reset_index()
        dev_stats = dev_stats[dev_stats["count"] >= 50]
        dev_stats = dev_stats.sort_values("mean", ascending=True).tail(18)

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor("#f8faff")

        # Ensure visibility by starting the gradient range at 0.4 (avoiding near-white)
        v_min, v_max = dev_stats["mean"].min(), dev_stats["mean"].max()
        # Scale values into the 0.4 - 0.9 range of the Blues colormap
        if v_max > v_min:
            vals = 0.4 + 0.5 * (dev_stats["mean"].values - v_min) / (v_max - v_min)
        else:
            vals = [0.7] * len(dev_stats)
        colors = plt.cm.Blues(vals)
        colors = [plt.cm.colors.to_hex(c) for c in colors]

        bars = ax.barh(dev_stats["DevType"], dev_stats["mean"],
                       color=colors, edgecolor="white", linewidth=1, height=0.7)

        _style_ax(ax, "Mean Salary by Developer Type", xlabel="Avg Salary (USD)")

        # Global median reference line
        ax.axvline(global_median, color="#f43f5e", linestyle="--", alpha=0.5, linewidth=1.5)
        ax.text(global_median + 2000, -0.5, f"Global Avg: ${global_median:,.0f}",
                color="#f43f5e", fontweight="bold", fontsize=9, va="bottom")

        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

        # Labels including sample size (n=...)
        for i, bar in enumerate(bars):
            w = bar.get_width()
            n = dev_stats.iloc[i]["count"]
            ax.text(w + 1000, bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f} (n={int(n)})", va="center", fontsize=9,
                    color="#475569", fontweight="500")

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("DevType column not found in dataset.")

    st.html('</div>')

    # ══ g. ROW 6 — Programming Languages (full width) ════
    # NEW: LanguageHaveWorkedWith is semicolon-separated (one respondent can
    # list many languages).  We explode the column so each language gets
    # its own row, then compute the mean salary per language.
    st.html('<div class="ep-card">')
    st.html('<div class="ep-card-title">Salary by Programming Language</div>')
    st.html('<div class="ep-card-sub">Average salary of developers who use each language (top 15)</div>')

    if "LanguageHaveWorkedWith" in df.columns:
        # Explode semicolon-separated language lists into individual rows
        lang_df = df[["LanguageHaveWorkedWith", "Salary"]].dropna(subset=["LanguageHaveWorkedWith"])
        lang_df = lang_df.copy()
        lang_df["LanguageHaveWorkedWith"] = lang_df["LanguageHaveWorkedWith"].str.split(";")
        lang_df = lang_df.explode("LanguageHaveWorkedWith")
        lang_df["LanguageHaveWorkedWith"] = lang_df["LanguageHaveWorkedWith"].str.strip()
        lang_df = lang_df[lang_df["LanguageHaveWorkedWith"] != ""]

        # Keep only languages used by at least 50 respondents (removes noise)
        lang_counts = lang_df["LanguageHaveWorkedWith"].value_counts()
        common_langs = lang_counts[lang_counts >= 50].index
        lang_df = lang_df[lang_df["LanguageHaveWorkedWith"].isin(common_langs)]

        # Mean salary per language, top 18 for readability
        lang_data = (
            lang_df.groupby("LanguageHaveWorkedWith")["Salary"]
            .agg(["mean", "count"])
            .sort_values("mean", ascending=True)
            .tail(18)
        )
        global_avg_lang = df["Salary"].mean()

        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor("#f8faff")

        # Ensure visibility by starting the gradient range at 0.4
        v_min, v_max = lang_data["mean"].min(), lang_data["mean"].max()
        if v_max > v_min:
            vals = 0.4 + 0.5 * (lang_data["mean"].values - v_min) / (v_max - v_min)
        else:
            vals = [0.7] * len(lang_data)
        colors = plt.cm.Blues(vals)
        colors = [plt.cm.colors.to_hex(c) for c in colors]

        bars = ax.barh(lang_data.index, lang_data["mean"],
                       color=colors, edgecolor="white", linewidth=1.5, height=0.7)

        _style_ax(ax, "Mean Salary by Programming Language", xlabel="Avg Salary (USD)")

        # Global average benchmark line
        ax.axvline(global_avg_lang, color="#f43f5e", linestyle="--", alpha=0.5, linewidth=1.5)
        ax.text(global_avg_lang + 2000, -0.5, f"Global Avg: ${global_avg_lang:,.0f}",
                color="#f43f5e", fontweight="bold", fontsize=9, va="bottom")

        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

        # Labels including sample size (n=...)
        for i, bar in enumerate(bars):
            w = bar.get_width()
            n = lang_data.iloc[i]["count"]
            ax.text(w + 1000, bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f} (n={int(n)})", va="center", fontsize=9,
                    color="#475569", fontweight="500")

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("LanguageHaveWorkedWith column not found in dataset.")

    st.html('</div>')
