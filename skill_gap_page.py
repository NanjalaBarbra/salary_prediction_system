import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import joblib


# ══════════════════════════════════════════════════════════════
# LOAD MODEL — used to predict salaries per skill combination
# so that country context (e.g. Kenya vs USA) is baked in
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def load_model():
    return joblib.load("best_salary_model.pkl")


def _predict(country, education, employment, experience,
             languages, frameworks, devtype):
    """
    Run a single prediction using the trained model.
    Returns predicted salary in USD.
    """
    data        = load_model()
    pipeline    = data["pipeline"]
    devtype_r   = data["devtype_salary_rank"]
    edu_r       = data["education_salary_rank"]
    country_r   = data.get("country_salary_rank", {})
    fw_cols     = data["framework_cols"]
    lang_cols   = data["language_cols"]

    dr = devtype_r.get(devtype, 4)
    er = edu_r.get(education, 2)
    cr = country_r.get(country if country != "Other" else "South Africa", 3)

    row = {
        "Experience":              float(experience),
        "DevType_rank":            dr,
        "Education_rank":          er,
        "Country_rank":            cr,
        "Experience_x_DevType":    float(experience) * dr,
        "Experience_x_Education":  float(experience) * er,
        "Experience_x_Country":    float(experience) * cr,
        "Country":                 country if country != "Other" else "South Africa",
        "EdLevel":                 education,
        "Employment":              employment,
        "DevType":                 devtype,
    }

    for col in fw_cols:
        val = col.replace("Frame__", "")
        row[col] = 1 if any(
            val == f.lower().replace(" ","_").replace(".","_")
                          .replace("/","_").replace("#","sharp")
                          .replace("+","plus").replace("(","")
                          .replace(")","").replace("-","_").replace(",","")
            for f in frameworks
        ) else 0

    for col in lang_cols:
        val = col.replace("Lang__", "")
        row[col] = 1 if any(
            val == l.lower().replace(" ","_").replace(".","_")
                          .replace("/","_").replace("#","sharp")
                          .replace("+","plus").replace("(","")
                          .replace(")","").replace("-","_").replace(",","")
            for l in languages
        ) else 0

    X = pd.DataFrame([row])
    return float(np.expm1(pipeline.predict(X)[0]))


def _skill_salaries(country, education, employment, experience,
                    base_langs, base_fws, devtype, all_langs, all_fws):
    """
    For each skill (language or framework), predict the salary
    when that skill is added to the user's current stack.
    This uses the model so country context is fully respected —
    a Kenyan developer sees Kenyan salary levels, not US levels.
    """
    base_salary = _predict(country, education, employment, experience,
                           base_langs, base_fws, devtype)

    lang_results = []
    for lang in all_langs:
        if lang not in base_langs:
            new_langs = base_langs + [lang]
            sal = _predict(country, education, employment, experience,
                           new_langs, base_fws, devtype)
            lang_results.append({
                "skill": lang,
                "salary": sal,
                "uplift": sal - base_salary,
                "pct": ((sal - base_salary) / base_salary * 100) if base_salary > 0 else 0
            })

    fw_results = []
    for fw in all_fws:
        if fw not in base_fws:
            new_fws = base_fws + [fw]
            sal = _predict(country, education, employment, experience,
                           base_langs, new_fws, devtype)
            fw_results.append({
                "skill": fw,
                "salary": sal,
                "uplift": sal - base_salary,
                "pct": ((sal - base_salary) / base_salary * 100) if base_salary > 0 else 0
            })

    lang_df = pd.DataFrame(lang_results).sort_values("salary", ascending=False)
    fw_df   = pd.DataFrame(fw_results).sort_values("salary", ascending=False)

    return base_salary, lang_df, fw_df


def _draw_chart(df, my_skills, color, title):
    top    = df.head(10)
    labels = top["skill"].tolist()
    values = top["salary"].tolist()
    colors = ["#f59e0b" if l in my_skills else color for l in labels]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.5)))
    fig.patch.set_facecolor("#fafbff")
    ax.set_facecolor("#fafbff")
    bars = ax.barh(labels, values, color=colors,
                   edgecolor="none", height=0.6, alpha=0.9)
    ax.invert_yaxis()
    ax.set_xlabel("Predicted Annual Salary (USD)", fontsize=9, color="#6b7280")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    ax.tick_params(axis="y", labelsize=9, colors="#374151")
    ax.tick_params(axis="x", labelsize=8, colors="#9ca3af")
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.7, linestyle="--", alpha=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=11, fontweight="bold", color="#1e293b", pad=10)
    max_v = max(values) if values else 1
    for bar, val, lbl in zip(bars, values, labels):
        tag = " <- You" if lbl in my_skills else ""
        ax.text(val + max_v * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}{tag}", va="center", fontsize=7.5,
                color="#f59e0b" if lbl in my_skills else "#374151",
                fontweight="700" if lbl in my_skills else "500")
    plt.tight_layout(pad=1.5)
    return fig


def show_skill_gap_page():

    st.markdown("""
        <h2 style="font-weight:800; font-size:1.8rem;
            background:linear-gradient(120deg,#10b981,#3b82f6,#8b5cf6);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin-bottom:0.2rem;">Skill Gap Analyser</h2>
        <p style="color:#6b7280; font-size:0.95rem; margin-bottom:1.5rem;">
            See how adding each skill changes your predicted salary in your country.
            Salaries are generated by the model so they reflect your local market.
        </p>""", unsafe_allow_html=True)

    # Load model metadata for dropdowns
    try:
        model_data  = load_model()
    except FileNotFoundError:
        st.error("Model not found. Run python train_model.py first.")
        return

    valid       = model_data["valid_categories"]
    all_langs   = model_data["top_languages"]
    all_fws     = model_data["top_frameworks"]
    COUNTRIES   = sorted(valid["Country"])
    if "Other" not in COUNTRIES:
        COUNTRIES = ["Other"] + COUNTRIES
    EDUCATIONS  = sorted(valid["EdLevel"])
    EMPLOYMENTS = sorted(valid["Employment"])
    DEVTYPES    = sorted(valid["DevType"])

    st.markdown("### Your Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        country = st.selectbox("Country", COUNTRIES,
            index=COUNTRIES.index(st.session_state.get("country", COUNTRIES[0]))
            if st.session_state.get("country") in COUNTRIES else 0)
        education = st.selectbox("Education Level", EDUCATIONS,
            index=EDUCATIONS.index(st.session_state.get("education", EDUCATIONS[0]))
            if st.session_state.get("education") in EDUCATIONS else 0)
    with c2:
        employment = st.selectbox("Employment Type", EMPLOYMENTS,
            index=EMPLOYMENTS.index(st.session_state.get("employment", EMPLOYMENTS[0]))
            if st.session_state.get("employment") in EMPLOYMENTS else 0)
        devtype = st.selectbox("Job Role", DEVTYPES,
            index=DEVTYPES.index(st.session_state.get("devtype", DEVTYPES[0]))
            if st.session_state.get("devtype") in DEVTYPES else 0)
    with c3:
        experience = st.slider("Years of Experience", 0, 50,
            int(st.session_state.get("experience", 3)))

    st.markdown("### Your Current Skills")
    s1, s2 = st.columns(2)
    with s1:
        my_langs = st.multiselect("Languages you already use", all_langs,
            default=st.session_state.get("languages", [all_langs[0]] if all_langs else []))
    with s2:
        my_fws = st.multiselect("Frameworks you already use", all_fws,
            default=st.session_state.get("frameworks", [all_fws[0]] if all_fws else []))

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Analyse My Skill Gap", type="primary", use_container_width=True):
        with st.spinner("Running predictions for all skills in your country..."):
            base_sal, lang_df, fw_df = _skill_salaries(
                country, education, employment, experience,
                my_langs or [], my_fws or [], devtype,
                all_langs, all_fws
            )

        st.session_state["sg_base"]    = base_sal
        st.session_state["sg_lang_df"] = lang_df
        st.session_state["sg_fw_df"]   = fw_df
        st.session_state["sg_country"] = country
        st.session_state["sg_langs"]   = my_langs
        st.session_state["sg_fws"]     = my_fws

    # Show results if available
    if "sg_base" in st.session_state:
        base_sal = st.session_state["sg_base"]
        lang_df  = st.session_state["sg_lang_df"]
        fw_df    = st.session_state["sg_fw_df"]
        loc      = st.session_state["sg_country"]
        my_langs = st.session_state["sg_langs"]
        my_fws   = st.session_state["sg_fws"]

        # Current salary card
        st.markdown(f"""
            <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                border-radius:16px; padding:1.5rem 2rem; text-align:center;
                margin-bottom:1.5rem;">
                <div style="font-size:0.8rem; color:rgba(255,255,255,0.75);
                    text-transform:uppercase; letter-spacing:0.1em;">
                    Your Current Predicted Salary in {loc}</div>
                <div style="font-size:2.5rem; font-weight:800; color:#fff;
                    margin:0.3rem 0;">${base_sal:,.0f}</div>
                <div style="font-size:0.85rem; color:rgba(255,255,255,0.7);">
                    Based on your current profile and skills</div>
            </div>
        """, unsafe_allow_html=True)

        # Charts
        st.markdown("### How Each New Skill Changes Your Salary")
        st.caption("Yellow bars = skills you already have. Adding the top skills could increase your predicted salary.")

        tab_lang, tab_fw = st.tabs(["Languages", "Frameworks"])

        with tab_lang:
            if lang_df.empty:
                st.info("No language data available.")
            else:
                fig = _draw_chart(lang_df, my_langs or [], "#667eea",
                                  f"Predicted Salary by Language in {loc}")
                st.pyplot(fig)
                plt.close(fig)

        with tab_fw:
            if fw_df.empty:
                st.info("No framework data available.")
            else:
                fig = _draw_chart(fw_df, my_fws or [], "#10b981",
                                  f"Predicted Salary by Framework in {loc}")
                st.pyplot(fig)
                plt.close(fig)

        # Top recommendations
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Top Skills Worth Learning Next")
        st.caption("Skills that would increase your predicted salary the most.")

        r1, r2 = st.columns(2)

        with r1:
            st.markdown("**Languages**")
            top3_lang = lang_df[lang_df["uplift"] > 0].head(3)
            if top3_lang.empty:
                st.success("Your languages are already well optimised.")
            else:
                for i, (_, row) in enumerate(top3_lang.iterrows()):
                    medal = ["1.", "2.", "3."][i]
                    st.markdown(f"""
                        <div style="background:white; border-radius:12px;
                            padding:0.8rem 1rem; margin-bottom:8px;
                            border-left:4px solid #667eea;
                            box-shadow:0 2px 8px rgba(102,126,234,0.08);">
                            <div style="font-weight:700; color:#1a202c;">
                                {medal} {row['skill']}</div>
                            <div style="color:#059669; font-size:0.85rem; font-weight:600;">
                                +${row['uplift']:,.0f}/yr (+{row['pct']:.1f}%)
                            </div>
                        </div>""", unsafe_allow_html=True)

        with r2:
            st.markdown("**Frameworks**")
            top3_fw = fw_df[fw_df["uplift"] > 0].head(3)
            if top3_fw.empty:
                st.success("Your frameworks are already well optimised.")
            else:
                for i, (_, row) in enumerate(top3_fw.iterrows()):
                    medal = ["1.", "2.", "3."][i]
                    st.markdown(f"""
                        <div style="background:white; border-radius:12px;
                            padding:0.8rem 1rem; margin-bottom:8px;
                            border-left:4px solid #10b981;
                            box-shadow:0 2px 8px rgba(16,185,129,0.08);">
                            <div style="font-weight:700; color:#1a202c;">
                                {medal} {row['skill']}</div>
                            <div style="color:#059669; font-size:0.85rem; font-weight:600;">
                                +${row['uplift']:,.0f}/yr (+{row['pct']:.1f}%)
                            </div>
                        </div>""", unsafe_allow_html=True)
