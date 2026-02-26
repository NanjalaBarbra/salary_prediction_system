import streamlit as st
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from database import get_connection


@st.cache_resource
def load_model():
    model = joblib.load("best_salary_model.pkl")
    return model


regressor_loaded = load_model()


def show_predict_page():

    if "predict_step" not in st.session_state:
        st.session_state.predict_step = 1

    # =========================================================
    # STEP 1: Background Info
    # =========================================================
    if st.session_state.predict_step == 1:
        st.markdown(
            """
            <h3 style="text-align: center; font-weight: 700; margin-bottom: 2.5rem; font-size: 1.8rem;
                background: linear-gradient(120deg, #10b981, #3b82f6, #8b5cf6);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                💰 We need some information to Estimate the salary
            </h3>
            """,
            unsafe_allow_html=True,
        )

        Countries = (
            "United States", "India", "United Kingdom", "Germany", "Canada",
            "France", "Brazil", "Spain", "Australia", "Netherlands", "Poland", "other",
        )
        undergradmajor = (
            "CS/Software Eng", "Math/Stats", "IT/Systems", "Natural Sciences", "Arts",
            "Other Engineering", "Humanities", "Health Sciences", "Social Sciences",
            "Web Dev/Design", "Business", "Other", "Unknown", "Undeclared",
        )
        education_levels = (
            "less than a Bachelor's",
            "Bachelor's degree",
            "Master's degree",
            "Post grad",
        )

        st.markdown(
            """
            <style>
            .predict-image-wrapper img {
                border-radius: 20px;
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                border: 4px solid rgba(251, 191, 36, 0.6);
            }
            .predict-form-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 24px;
                padding: 2rem 1.5rem;
                box-shadow: 0 20px 50px rgba(139, 92, 246, 0.3);
                border: 3px solid rgba(251, 191, 36, 0.4);
                backdrop-filter: blur(10px);
            }
            .form-header {
                font-size: 1.5rem;
                font-weight: 700;
                background: linear-gradient(120deg, #10b981, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1.5rem;
                padding-bottom: 0.75rem;
                border-bottom: 3px solid #fbbf24;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown('<div class="predict-image-wrapper">', unsafe_allow_html=True)
            st.image("Images/image1.jpeg", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="predict-form-container">', unsafe_allow_html=True)
            st.markdown('<div class="form-header">📋 Background Information</div>', unsafe_allow_html=True)
            st.session_state.country = st.selectbox("🌍 Country", Countries)
            st.session_state.education = st.selectbox("🎓 Education Level", education_levels)
            st.session_state.undergradmajor = st.selectbox("📚 Your Undergraduate Major", undergradmajor)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        def go_to_step2():
            st.session_state.predict_step = 2
            st.session_state.nav_selectbox = "Predict"

        st.button("Next ➡️", on_click=go_to_step2, use_container_width=True)

    # =========================================================
    # STEP 2: Work Info
    # =========================================================
    elif st.session_state.predict_step == 2:
        employment = ("full-time", "part-time")
        webframeworkedwith = ("React.js", "J Query", "Spring", "Flask", "other")

        st.markdown(
            """
            <style>
            .predict-image-wrapper-right img {
                border-radius: 20px;
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
                border: 4px solid rgba(251, 191, 36, 0.6);
            }
            .predict-work-form-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 24px;
                padding: 2rem 1.5rem;
                box-shadow: 0 20px 50px rgba(139, 92, 246, 0.3);
                border: 3px solid rgba(251, 191, 36, 0.4);
                backdrop-filter: blur(10px);
            }
            .work-form-header {
                font-size: 1.5rem;
                font-weight: 700;
                background: linear-gradient(120deg, #8b5cf6, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1.5rem;
                padding-bottom: 0.75rem;
                border-bottom: 3px solid #fbbf24;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown('<div class="predict-work-form-container">', unsafe_allow_html=True)
            st.markdown('<div class="work-form-header">💼 Work Information</div>', unsafe_allow_html=True)
            st.session_state.employment = st.selectbox("💻 Employment Status", employment)
            st.session_state.Experience = st.slider("📅 Years of Experience", 0, 50, 1)
            st.session_state.webframeworkedwith = st.selectbox("🔧 Web Framework conversant With", webframeworkedwith)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="predict-image-wrapper-right">', unsafe_allow_html=True)
            st.image("Images/image2.jpeg", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_back, col_calc = st.columns([1, 1], gap="medium")

        def go_to_step1():
            st.session_state.predict_step = 1
            st.session_state.nav_selectbox = "Predict"

        with col_back:
            st.button("⬅️ Back", on_click=go_to_step1, use_container_width=True)

        with col_calc:
            calculate_clicked = st.button("💰 Calculate Salary", use_container_width=True, type="primary")

        if calculate_clicked:
            X = pd.DataFrame([{
                "Country": st.session_state.country,
                "EdLevel": st.session_state.education,
                "Employment": st.session_state.employment,
                "Experience": float(st.session_state.Experience),
                "WebframeWorkedWith": st.session_state.webframeworkedwith,
                "UndergradMajor": st.session_state.undergradmajor,
            }])

            salary = regressor_loaded.predict(X)
            predicted = float(salary[0])

            # ---- Styled result banner ----
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                    border-radius:16px; padding:1.5rem 2rem; text-align:center;
                    margin:1rem 0; box-shadow:0 8px 24px rgba(102,126,234,0.35);">
                    <div style="font-size:0.85rem; font-weight:600; color:rgba(255,255,255,0.75);
                        text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.3rem;">
                        💰 Your Estimated Annual Salary
                    </div>
                    <div style="font-size:2.8rem; font-weight:800; color:#ffffff; line-height:1.1;">
                        ${predicted:,.0f}
                    </div>
                    <div style="font-size:0.8rem; color:rgba(255,255,255,0.6); margin-top:0.3rem;">
                        Range: ${max(0, predicted-10000):,.0f} – ${predicted+10000:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Save to database
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO predictions
                                (username, country, education, employment, experience,
                                 webframework, undergradmajor, predicted_salary)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                st.session_state.get("username", "guest"),
                                st.session_state.country,
                                st.session_state.education,
                                st.session_state.employment,
                                st.session_state.Experience,
                                st.session_state.webframeworkedwith,
                                st.session_state.undergradmajor,
                                predicted,
                            ),
                        )
                        conn.commit()
                st.success("✅ Prediction saved to database")
            except Exception as e:
                st.error(f"Database error: {str(e)}")

            # ================================================================
            # SALARY COMPARISON TOOL
            # ================================================================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                """
                <h3 style="font-weight:800; font-size:1.2rem; color:#1a202c; margin-bottom:0.2rem;">
                    📊 How Do You Compare?
                </h3>
                <p style="font-size:0.85rem; color:#6b7280; margin-bottom:1rem;">
                    See how your salary stacks up against others in your country
                    and at your experience level.
                </p>
                """,
                unsafe_allow_html=True,
            )

            try:
                survey = pd.read_csv("data/survey_results_public.csv")
                if "ConvertedComp" in survey.columns:
                    survey = survey.rename(columns={"ConvertedComp": "Salary"})
                elif "ConvertedCompYearly" in survey.columns:
                    survey = survey.rename(columns={"ConvertedCompYearly": "Salary"})

                survey = survey[["Country", "YearsCodePro", "Salary"]].dropna()
                survey = survey[(survey["Salary"] >= 10_000) & (survey["Salary"] <= 400_000)]
                survey["YearsCodePro"] = pd.to_numeric(survey["YearsCodePro"], errors="coerce")
                survey = survey.dropna(subset=["YearsCodePro"])

                user_country = st.session_state.country
                user_exp = float(st.session_state.Experience)

                country_df = survey[survey["Country"] == user_country]
                country_avg = country_df["Salary"].mean() if not country_df.empty else None

                exp_low = max(0, user_exp - 2)
                exp_high = user_exp + 2
                exp_df = survey[
                    (survey["YearsCodePro"] >= exp_low) &
                    (survey["YearsCodePro"] <= exp_high)
                ]
                exp_avg = exp_df["Salary"].mean() if not exp_df.empty else None

                country_exp_df = country_df[
                    (country_df["YearsCodePro"] >= exp_low) &
                    (country_df["YearsCodePro"] <= exp_high)
                ] if country_avg else pd.DataFrame()
                country_exp_avg = country_exp_df["Salary"].mean() if not country_exp_df.empty else None

                # ---- Comparison cards ----
                comp_cols = st.columns(3)
                benchmarks = [
                    ("🌍 Country Avg", country_avg, f"in {user_country}"),
                    ("📅 Experience Avg", exp_avg, f"{int(user_exp)}±2 yrs globally"),
                    ("🎯 Country + Exp Avg", country_exp_avg, f"{int(user_exp)}±2 yrs in {user_country}"),
                ]
                for col, (label, avg, sublabel) in zip(comp_cols, benchmarks):
                    if avg:
                        diff = predicted - avg
                        diff_pct = (diff / avg) * 100
                        color = "#10b981" if diff >= 0 else "#ef4444"
                        arrow = "▲" if diff >= 0 else "▼"
                        col.markdown(
                            f"""
                            <div style="background:rgba(255,255,255,0.95); border-radius:14px;
                                padding:1rem 1.1rem; border-top:4px solid {color};
                                box-shadow:0 4px 14px rgba(0,0,0,0.07); text-align:center;">
                                <div style="font-size:0.7rem; font-weight:600; color:#6b7280;
                                    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.3rem;">
                                    {label}
                                </div>
                                <div style="font-size:1.1rem; font-weight:800; color:#1a202c;">
                                    ${avg:,.0f}
                                </div>
                                <div style="font-size:0.78rem; font-weight:700; color:{color}; margin-top:0.2rem;">
                                    {arrow} {abs(diff_pct):.1f}% {"above" if diff >= 0 else "below"} avg
                                </div>
                                <div style="font-size:0.68rem; color:#9ca3af; margin-top:0.15rem;">
                                    {sublabel}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        col.markdown(
                            f"""
                            <div style="background:rgba(255,255,255,0.8); border-radius:14px;
                                padding:1rem; text-align:center; color:#9ca3af; font-size:0.82rem;">
                                {label}<br><b>No data</b>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.markdown("<br>", unsafe_allow_html=True)

                # ---- Bar chart ----
                bar_labels = ["You"]
                bar_values = [predicted]
                bar_colors = ["#764ba2"]

                if country_avg:
                    bar_labels.append(f"Country Avg\n({user_country})")
                    bar_values.append(country_avg)
                    bar_colors.append("#667eea")
                if exp_avg:
                    bar_labels.append(f"Experience Avg\n({int(user_exp)}±2 yrs)")
                    bar_values.append(exp_avg)
                    bar_colors.append("#10b981")
                if country_exp_avg:
                    bar_labels.append(f"Country+Exp Avg\n({user_country}, {int(user_exp)}±2 yrs)")
                    bar_values.append(country_exp_avg)
                    bar_colors.append("#f59e0b")

                fig, ax = plt.subplots(figsize=(8, 3.5))
                fig.patch.set_facecolor("#fafbff")
                ax.set_facecolor("#fafbff")
                bars = ax.bar(
                    bar_labels, bar_values,
                    color=bar_colors, edgecolor="none",
                    width=0.5, alpha=0.92,
                )
                for bar, val in zip(bars, bar_values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        val + max(bar_values) * 0.015,
                        f"${val:,.0f}",
                        ha="center", va="bottom",
                        fontsize=8.5, fontweight="700", color="#374151",
                    )
                ax.set_ylabel("Annual Salary (USD)", fontsize=9, color="#6b7280")
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_color("#e5e7eb")
                ax.spines["bottom"].set_color("#e5e7eb")
                ax.tick_params(axis="both", labelsize=8, colors="#6b7280")
                ax.grid(axis="y", color="#e5e7eb", linewidth=0.7, linestyle="--", alpha=0.8)
                ax.set_axisbelow(True)
                plt.tight_layout(pad=1.5)
                st.pyplot(fig)
                plt.close(fig)

                # ---- Percentile gauge ----
                if country_df is not None and not country_df.empty:
                    pct_rank = int((country_df["Salary"] < predicted).mean() * 100)
                    gauge_color = "#10b981" if pct_rank >= 60 else "#f59e0b" if pct_rank >= 35 else "#ef4444"
                    st.markdown(
                        f"""
                        <div style="background:rgba(255,255,255,0.9); border-radius:12px;
                            padding:1rem 1.4rem; margin-top:0.5rem;
                            border:1.5px solid rgba(102,126,234,0.15);
                            box-shadow:0 2px 8px rgba(102,126,234,0.08);">
                            <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                                <span style="font-size:0.83rem; font-weight:600; color:#374151;">
                                    🎯 Your Salary Percentile in {user_country}
                                </span>
                                <span style="font-size:0.83rem; font-weight:800; color:{gauge_color};">
                                    Top {100 - pct_rank}%
                                </span>
                            </div>
                            <div style="background:#e5e7eb; border-radius:999px; height:12px; overflow:hidden;">
                                <div style="width:{pct_rank}%;
                                    background:linear-gradient(90deg,{gauge_color},{gauge_color}bb);
                                    height:100%; border-radius:999px;">
                                </div>
                            </div>
                            <div style="font-size:0.74rem; color:#9ca3af; margin-top:0.35rem;">
                                You earn more than <b>{pct_rank}%</b> of developers in {user_country}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            except Exception as e:
                st.info(f"Comparison data unavailable: {str(e)}")