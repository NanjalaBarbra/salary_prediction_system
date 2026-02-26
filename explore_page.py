import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def shorten_categories(categories, cutoff):
    categorical_map = {}
    for i in range(len(categories)):
        if categories.values[i] >= cutoff:
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            categorical_map[categories.index[i]] = "other"
    return categorical_map


def clean_experience(x):
    if x == "More than 50 years":
        return 50
    if x == "Less than 1 year":
        return 0.5
    return float(x)


def clean_education(x):
    if "Bachelor's degree" in x:
        return "Bachelor's degree"
    if "Master's degree" in x:
        return "Master's degree"
    if "Professional degree" in x or "Other doctoral" in x:
        return "Post grad"
    return "Less than Bachelor's"


def clean_undergrad_major(x):
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


@st.cache_data
def load_data():
    df = pd.read_csv("data/survey_results_public.csv")
    df = df[["Country", "EdLevel", "YearsCodePro", "Employment",
              "WebframeWorkedWith", "UndergradMajor", "ConvertedComp"]]
    df = df.rename(columns={"ConvertedComp": "Salary", "YearsCodePro": "Experience"})
    df = df[df["Salary"].notnull()].dropna()
    df["Experience"] = df["Experience"].apply(clean_experience)
    df["Employment"] = df["Employment"].map({
        "Employed full-time": "full-time",
        "Employed part-time": "part-time"
    }).fillna("other")
    country_map = shorten_categories(df["Country"].value_counts(), 400)
    df["Country"] = df["Country"].map(country_map)
    web_map = shorten_categories(df["WebframeWorkedWith"].value_counts(), 400)
    df["WebframeWorkedWith"] = df["WebframeWorkedWith"].map(web_map)
    df["UndergradMajor"] = df["UndergradMajor"].apply(clean_undergrad_major)
    df["EdLevel"] = df["EdLevel"].apply(clean_education)
    df = df[(df["Salary"] >= 10_000) & (df["Salary"] <= 250_000)]
    return df


df = load_data()

# ── Shared matplotlib style ──
PALETTE = ["#6366f1", "#10b981", "#f472b6", "#fbbf24", "#34d399",
           "#818cf8", "#fb923c", "#a78bfa", "#22d3ee", "#f87171"]

def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.set_facecolor("#f8faff")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#1e293b", pad=12)
    ax.set_xlabel(xlabel, fontsize=10, color="#64748b")
    ax.set_ylabel(ylabel, fontsize=10, color="#64748b")
    ax.tick_params(colors="#64748b", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def show_explore_page():

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
        .main .block-container { padding-top: 1.5rem !important; max-width: 100% !important; }
        .ep-header { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#0f172a; letter-spacing:-0.02em; margin-bottom:0.2rem; }
        .ep-sub { font-family:'DM Sans',sans-serif; font-size:0.93rem; color:#64748b; margin-bottom:1.5rem; }
        .ep-eyebrow { font-family:'DM Sans',sans-serif; font-size:0.7rem; font-weight:600; letter-spacing:0.15em; text-transform:uppercase; color:#6366f1; margin-bottom:0.2rem; }
        .ep-card { background:#fff; border-radius:18px; padding:1.5rem; border:1px solid #e2e8f0; box-shadow:0 4px 20px rgba(99,102,241,0.07); margin-bottom:1rem; }
        .ep-card-title { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#0f172a; margin-bottom:0.2rem; }
        .ep-card-sub { font-family:'DM Sans',sans-serif; font-size:0.8rem; color:#94a3b8; margin-bottom:1rem; }
        .ep-metric { background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:14px; padding:1.2rem 1.5rem; text-align:center; }
        .ep-metric-num { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#fff; }
        .ep-metric-label { font-family:'DM Sans',sans-serif; font-size:0.72rem; color:rgba(255,255,255,0.75); text-transform:uppercase; letter-spacing:0.08em; }
        </style>
    """, unsafe_allow_html=True)

    # ── Header ──
    st.markdown('<div class="ep-eyebrow">Stack Overflow Developer Survey 2020</div>', unsafe_allow_html=True)
    st.markdown('<div class="ep-header">Explore Developer Salaries</div>', unsafe_allow_html=True)
    st.markdown('<div class="ep-sub">Visual breakdown of the data behind the salary prediction model.</div>', unsafe_allow_html=True)

    # ── KPI row ──
    k1, k2, k3, k4 = st.columns(4)
    avg_sal = f"${df['Salary'].mean():,.0f}"
    max_sal = f"${df['Salary'].max():,.0f}"
    countries = df['Country'].nunique()
    total = f"{len(df):,}"

    for col, num, label in [
        (k1, total, "Responses"),
        (k2, avg_sal, "Avg Salary"),
        (k3, max_sal, "Max Salary"),
        (k4, str(countries), "Countries"),
    ]:
        col.markdown(f'<div class="ep-metric"><div class="ep-metric-num">{num}</div><div class="ep-metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══ ROW 1: Pie + Bar side by side ══
    col_pie, col_bar = st.columns(2, gap="large")

    with col_pie:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Responses by Country</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">Distribution of survey respondents across countries</div>', unsafe_allow_html=True)

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
        ax.legend(
            wedges, data.index,
            loc="lower center", bbox_to_anchor=(0.5, -0.18),
            ncol=3, fontsize=8, frameon=False,
            labelcolor="#475569",
        )
        ax.set_title("Country Distribution", fontsize=13, fontweight="bold", color="#1e293b", pad=10)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_bar:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Average Salary by Country</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">Mean annual salary (USD) sorted highest to lowest</div>', unsafe_allow_html=True)

        data = df.groupby("Country")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.barh(data.index, data.values, color=PALETTE[:len(data)], edgecolor="white", linewidth=1.5, height=0.65)
        _style_ax(ax, "Mean Salary by Country", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 800, bar.get_y() + bar.get_height()/2,
                    f"${w:,.0f}", va="center", fontsize=8, color="#475569")
        ax.tick_params(axis="y", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 2: Line + Bar side by side ══
    col_exp, col_edu = st.columns(2, gap="large")

    with col_exp:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Salary vs Experience</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">How average salary grows with years of professional coding</div>', unsafe_allow_html=True)

        data = df.groupby("Experience")["Salary"].mean().sort_index()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor("#f8faff")
        ax.fill_between(data.index, data.values, alpha=0.15, color="#6366f1")
        ax.plot(data.index, data.values, color="#6366f1", linewidth=2.5, marker="o",
                markersize=5, markerfacecolor="white", markeredgewidth=2, markeredgecolor="#6366f1")
        _style_ax(ax, "Salary Growth by Experience", xlabel="Years of Experience", ylabel="Avg Salary (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_edu:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Salary by Education Level</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">Impact of academic qualification on average salary</div>', unsafe_allow_html=True)

        data = df.groupby("EdLevel")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor("#f8faff")
        colors = ["#10b981", "#6366f1", "#f472b6", "#fbbf24"]
        bars = ax.barh(data.index, data.values, color=colors[:len(data)],
                       edgecolor="white", linewidth=1.5, height=0.55)
        _style_ax(ax, "Mean Salary by Education", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 500, bar.get_y() + bar.get_height()/2,
                    f"${w:,.0f}", va="center", fontsize=8.5, color="#475569")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 3: Employment + Major side by side ══
    col_emp, col_maj = st.columns(2, gap="large")

    with col_emp:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Salary by Employment Type</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">Full-time vs part-time average earnings</div>', unsafe_allow_html=True)

        data = df.groupby("Employment")["Salary"].mean().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.bar(data.index, data.values,
                      color=["#6366f1", "#10b981", "#f472b6"][:len(data)],
                      edgecolor="white", linewidth=2, width=0.45)
        _style_ax(ax, "Salary by Employment Type", ylabel="Avg Salary (USD)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 500,
                    f"${h:,.0f}", ha="center", fontsize=9, color="#475569", fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_maj:
        st.markdown('<div class="ep-card">', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-title">Salary by Undergrad Major</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-card-sub">How your field of study influences earning potential</div>', unsafe_allow_html=True)

        data = df.groupby("UndergradMajor")["Salary"].mean().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor("#f8faff")
        bars = ax.barh(data.index, data.values,
                       color=PALETTE[:len(data)],
                       edgecolor="white", linewidth=1.5, height=0.6)
        _style_ax(ax, "Mean Salary by Major", xlabel="USD")
        ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
        ax.grid(axis="y", visible=False)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 400, bar.get_y() + bar.get_height()/2,
                    f"${w:,.0f}", va="center", fontsize=8, color="#475569")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 4: Web Framework salary (full width) ══
    st.markdown('<div class="ep-card">', unsafe_allow_html=True)
    st.markdown('<div class="ep-card-title">Salary by Web Framework</div>', unsafe_allow_html=True)
    st.markdown('<div class="ep-card-sub">Average salary across different web frameworks used</div>', unsafe_allow_html=True)

    data = df.groupby("WebframeWorkedWith")["Salary"].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#f8faff")
    bars = ax.bar(data.index, data.values,
                  color=PALETTE[:len(data)],
                  edgecolor="white", linewidth=2, width=0.55)
    _style_ax(ax, "Mean Salary by Web Framework", ylabel="Avg Salary (USD)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 300,
                f"${h:,.0f}", ha="center", fontsize=8.5, color="#475569", fontweight="bold", rotation=45)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown('</div>', unsafe_allow_html=True)
