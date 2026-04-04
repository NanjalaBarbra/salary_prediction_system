import streamlit as st
import pandas as pd
import numpy as np
import joblib
from database import get_connection
from security import rate_limit, validate_prediction_input


# ══════════════════════════════════════════════════════════════
# LOAD MODEL
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def load_model():
    return joblib.load("best_salary_model.pkl")

_data           = load_model()
_pipeline       = _data.get("pipeline")
_best_name      = _data["best_model_name"]
_mae            = _data["test_mae"]
_r2             = _data["test_r2"]
_valid          = _data["valid_categories"]
_top_frameworks = _data["top_frameworks"]
_top_languages  = _data["top_languages"]
_framework_cols = _data["framework_cols"]
_language_cols  = _data["language_cols"]

# Metadata for feature engineering (v4.1)
_devtype_rank      = _data["devtype_salary_rank"]
_education_rank    = _data["education_salary_rank"]
_country_rank      = _data.get("country_salary_rank", {})
_orgsize_rank      = _data.get("orgsize_rank", {})
_remote_rank       = _data.get("remote_rank", {})
_age_rank          = _data.get("age_rank", {})
_lang_salary_map   = _data.get("lang_salary_map", {})
_ct_dt_median      = _data.get("country_devtype_median", {})
_country_mean_sal  = _data.get("country_mean_salary", {})
_country_std_sal   = _data.get("country_std_salary", {})
_country_ppp_mean  = _data.get("country_ppp_mean", {})
_devtype_mean_sal  = _data.get("devtype_mean_salary", {})
_edu_mean_sal      = _data.get("edu_mean_salary", {})
_ppp_factors       = _data.get("ppp_factors", {})
_lang_seniority    = _data.get("lang_seniority", {})
_global_mean_sal   = _data.get("global_mean_salary", 60000)
_global_std_sal    = _data.get("global_std_salary", 40000)
_qt                = _data.get("quantile_transformer")

# CatBoost special handling
_cb_model          = _data.get("catboost_model")
_cb_features       = _data.get("catboost_all_features", [])
_cb_cats           = _data.get("catboost_cat_features", [])

COUNTRIES   = sorted(_valid["Country"])
if "Other" not in COUNTRIES:
    COUNTRIES = ["Other"] + COUNTRIES
EDUCATIONS  = sorted(_valid["EdLevel"])
EMPLOYMENTS = sorted(_valid["Employment"])
DEVTYPES    = sorted(_valid["DevType"])
FRAMEWORKS  = _top_frameworks
LANGUAGES   = _top_languages


# ══════════════════════════════════════════════════════════════
# PREDICTION FUNCTION
# ══════════════════════════════════════════════════════════════

def predict_salary(country, education, employment, experience,
                   frameworks, languages, devtype):
    """
    Build feature row matching the enhanced training pipeline exactly.
    New features added in v3.0:
    - Exp_bucket: non-linear experience bins
    - Country_DevType_salary: interaction-based median lookup
    - Lang_value_score: average economic value per programming language
    - QuantileTransformer for target scaling
    """
    devtype_rank   = _devtype_rank.get(devtype, 4)
    education_rank = _education_rank.get(education, 2)
    exp            = float(experience)
    country_key    = country if country != "Other" else "South Africa"
    country_rank   = _country_rank.get(country_key, 3)

    # Sensible defaults for features not collected in the UI
    orgsize_rank   = _orgsize_rank.get("Medium (100-4999)", 3)
    remote_rank    = _remote_rank.get("Hybrid", 2)
    age_rank       = _age_rank.get("25-34", 2)

    # Tech stack counts
    num_languages  = len(languages) if languages else 0
    num_frameworks = len(frameworks) if frameworks else 0
    tech_breadth   = num_languages + num_frameworks

    # YearsCode default: assume total coding years ≈ experience + 3
    years_code     = min(exp + 3, 55)
    code_work_gap  = max(0, years_code - exp)

    # ▸ NEW: Experience Bucket
    if exp <= 2:    exp_bucket = 1.0
    elif exp <= 5:  exp_bucket = 2.0
    elif exp <= 10: exp_bucket = 3.0
    elif exp <= 20: exp_bucket = 4.0
    else:           exp_bucket = 5.0

    # ▸ NEW: Country x DevType median salary
    ct_dt_key = f"{country_key}_{devtype}"
    ct_dt_salary = _ct_dt_median.get(ct_dt_key, _global_mean_sal)

    # ▸ NEW v4.1: PPP factor
    ppp_factor = _ppp_factors.get(country_key, 3.0)

    # ▸ NEW v4.1: Tech seniority score
    def compute_tech_seniority(langs):
        if not langs: return 5.0
        scores = [_lang_seniority.get(l, 5) for l in langs]
        return float(np.mean(scores)) if scores else 5.0

    ts_score = compute_tech_seniority(languages)

    row = {
        # Core features
        "Experience":              exp,
        "Experience_sq":           exp ** 2,
        "Experience_log":          float(np.log1p(exp)),
        "YearsCode":               years_code,
        "Code_Work_Gap":           code_work_gap,
        "Exp_bucket":              exp_bucket,
        "Num_languages":           num_languages,
        "Num_frameworks":          num_frameworks,
        "Tech_breadth":            tech_breadth,

        # Rank features
        "DevType_rank":            devtype_rank,
        "Education_rank":          education_rank,
        "OrgSize_rank":            orgsize_rank,
        "Remote_rank":             remote_rank,
        "Age_rank":                age_rank,
        "Country_rank":            country_rank,

        # Interaction features
        "Experience_x_DevType":     exp * devtype_rank,
        "Experience_x_Education":   exp * education_rank,
        "Experience_x_OrgSize":     exp * orgsize_rank,
        "DevType_x_Education":      devtype_rank * education_rank,
        "Experience_x_TechBreadth": exp * tech_breadth,
        "Experience_x_Remote":      exp * remote_rank,
        "Age_x_Experience":         age_rank * exp,
        "Experience_x_Country":     exp * country_rank,
        "Experience_x_Country_mean": exp * _country_mean_sal.get(country_key, _global_mean_sal),

        # Target-encoded mean stats (v4.1)
        "Country_mean_salary":      _country_mean_sal.get(country_key, _global_mean_sal),
        "Country_std_salary":       _country_std_sal.get(country_key, _global_std_sal),
        "DevType_mean_salary":      _devtype_mean_sal.get(devtype, _global_mean_sal),
        "EdLevel_mean_salary":      _edu_mean_sal.get(education, _global_mean_sal),
        "Country_DevType_salary":   ct_dt_salary,
        "Country_ppp_mean":         _country_ppp_mean.get(country_key, _global_mean_sal),
        "PPP_factor":               ppp_factor,
        "Tech_seniority_score":     ts_score,
        "Tech_seniority_x_Exp":     float(ts_score * exp),

        # Categorical features
        "Country":                  country_key,
        "EdLevel":                  education,
        "Employment":               employment,
        "DevType":                  devtype,
        "RemoteWork":               "Hybrid",
        "OrgSize":                  "Medium (100-4999)",
        "Age":                      "25-34",
        "Industry":                 "Tech/Software",
    }

    # Binary framework columns
    for col in _framework_cols:
        val = col.replace("Frame__", "")
        row[col] = int(any(
            val == f.lower().replace(" ", "_").replace(".", "_")
                           .replace("/", "_").replace("#", "sharp")
                           .replace("+", "plus").replace("(", "")
                           .replace(")", "").replace("-", "_").replace(",", "")
            for f in frameworks
        ))

    # Binary language columns
    lang_sum = 0.0
    for col in _language_cols:
        val = col.replace("Lang__", "")
        is_used = int(any(
            val == l.lower().replace(" ", "_").replace(".", "_")
                           .replace("/", "_").replace("#", "sharp")
                           .replace("+", "plus").replace("(", "")
                           .replace(")", "").replace("-", "_").replace(",", "")
            for l in languages
        ))
        row[col] = is_used
        if is_used:
            lang_sum += _lang_salary_map.get(col, _global_mean_sal)

    # ▸ NEW: Language Value Score
    row["Lang_value_score"] = lang_sum / max(1, num_languages)

    X = pd.DataFrame([row])

    # Prediction logic (Ensemble pipeline OR CatBoost native)
    if _pipeline is not None:
        y_t = _pipeline.predict(X)[0]
    elif _cb_model is not None:
        # Robust filtering for CatBoost features
        # Ensure all required features exist in X before slicing
        for feat in _cb_features:
            if feat not in X.columns:
                # Add default or fallback if missing
                X[feat] = 0.0
        X_cb = X[_cb_features].copy()
        for col_cat in _cb_cats:
            X_cb[col_cat] = X_cb[col_cat].astype(str).fillna("Unknown")
        y_t = _cb_model.predict(X_cb)[0]
    else:
        raise ValueError("No valid prediction model found in pickle.")

    # Inverse transform through QuantileTransformer (v3.0)
    res_raw = _qt.inverse_transform([[y_t]])[0][0]
    return float(max(0, res_raw))


# ══════════════════════════════════════════════════════════════
# SAVE PREDICTION TO DATABASE
# ══════════════════════════════════════════════════════════════

def save_prediction(username, country, education, employment, experience,
                    devtype, frameworks, languages, predicted_salary):
    """Persist a prediction record to the predictions table."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO predictions
                        (username, country, education, employment, experience,
                         devtype, frameworks, languages, undergradmajor, predicted_salary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        country,
                        education,
                        employment,
                        int(experience),
                        devtype,
                        ", ".join(frameworks) if frameworks else "",
                        ", ".join(languages)  if languages  else "",
                        "",
                        float(predicted_salary),
                    ),
                )
                conn.commit()
        return True
    except Exception as e:
        st.error(f"Could not save prediction: {e}")
        return False


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _safe_idx(options, state_key, fallback=0):
    val = st.session_state.get(state_key)
    try:    return options.index(val)
    except: return fallback


# ══════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════

def show_predict_page():
    st.markdown("""
        <style>
        .pred-shell {
            max-width: 1240px;
            margin: 0 auto;
            padding: 0 0 1rem;
        }
        .predict-header {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at top left, rgba(240,242,244,0.18) 0%, transparent 24%),
                radial-gradient(circle at bottom right, rgba(217,228,238,0.12) 0%, transparent 28%),
                linear-gradient(135deg, #4a6b8a 0%, #3a5570 48%, #2d4a6b 100%);
            padding: 2.4rem 2.2rem;
            border-radius: 28px;
            color: white;
            margin-bottom: 1.4rem;
            box-shadow: 0 24px 55px rgba(45, 74, 107, 0.18);
        }
        .predict-header::before {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            top: -110px;
            right: -70px;
            border-radius: 50%;
            background: rgba(255,255,255,0.08);
        }
        .predict-header-grid {
            position: relative;
            z-index: 2;
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
            gap: 1.4rem;
            align-items: center;
        }
        .predict-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.08);
            font-size: 0.74rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.95rem;
        }
        .predict-header h1 {
            font-size: clamp(2rem, 4vw, 3rem);
            line-height: 1.03;
            margin: 0 0 0.7rem 0;
            letter-spacing: -0.04em;
        }
        .predict-header p {
            margin: 0;
            font-size: 1rem;
            line-height: 1.75;
            color: rgba(240,242,244,0.86);
            max-width: 560px;
        }
        .predict-header-visual {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 24px;
            padding: 1rem;
            backdrop-filter: blur(10px);
        }
        .predict-header-pillgrid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
        }
        .predict-header-pill {
            background: rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 0.9rem;
        }
        .predict-header-pill strong {
            display: block;
            font-size: 1.1rem;
            margin-bottom: 0.18rem;
        }
        .predict-header-pill span {
            font-size: 0.76rem;
            color: rgba(240,242,244,0.78);
            line-height: 1.4;
        }
        .step-card {
            background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
            border-radius: 22px;
            padding: 1.7rem;
            box-shadow: 0 18px 45px rgba(45, 74, 107, 0.08);
            border: 1px solid rgba(74,107,138,0.14);
            margin-bottom: 1.5rem;
        }
        .step-card h3 {
            color: #1a2e42;
            margin-bottom: 0.2rem;
        }
        .step-note {
            color: #6b7c8d;
            font-size: 0.9rem;
            margin-bottom: 1.15rem;
        }
        .result-shell {
            display: grid;
            grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
            gap: 1.15rem;
            margin: 1.4rem 0 1rem;
        }
        .result-card {
            background: linear-gradient(135deg, #2d4a6b 0%, #3a5570 48%, #4a6b8a 100%);
            border-radius: 24px;
            padding: 2.2rem;
            color: white;
            box-shadow: 0 24px 55px rgba(45, 74, 107, 0.18);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            min-height: 280px;
        }
        .result-sidecard {
            background: #ffffff;
            border-radius: 24px;
            padding: 1.4rem;
            border: 1px solid #dbe4eb;
            box-shadow: 0 18px 45px rgba(45, 74, 107, 0.08);
        }
        .result-side-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #6b7c8d;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        .result-list {
            display: grid;
            gap: 0.8rem;
        }
        .result-list-item {
            border-radius: 16px;
            background: #f6f9fb;
            padding: 0.9rem 1rem;
        }
        .result-list-item strong {
            display: block;
            color: #1a2e42;
            margin-bottom: 0.15rem;
        }
        .result-list-item span {
            color: #6b7c8d;
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .sim-panel {
            background: #ffffff;
            border-radius: 22px;
            padding: 1.5rem;
            border: 1px solid #dbe4eb;
            box-shadow: 0 18px 45px rgba(45, 74, 107, 0.08);
        }
        .sim-result {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbfd 100%);
            border-radius: 18px;
            padding: 1.4rem;
            box-shadow: 0 12px 30px rgba(45, 74, 107, 0.06);
            margin-top: 1rem;
            text-align: center;
        }
        @media (max-width: 900px) {
            .predict-header-grid,
            .result-shell {
                grid-template-columns: 1fr;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    if "predict_step" not in st.session_state:
        st.session_state.predict_step = 1

    step = st.session_state.predict_step

    st.markdown('<div class="pred-shell">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="predict-header">
            <div class="predict-header-grid">
                <div>
                    <div class="predict-badge">Salary Forecast Studio</div>
                    <h1>Build a sharper salary estimate with every detail you add</h1>
                    <p>Move through a guided flow, refine your developer profile, and get a more confident salary range backed by your model and survey data.</p>
                </div>
                <div class="predict-header-visual">
                    <div class="predict-header-pillgrid">
                        <div class="predict-header-pill"><strong>Step {step}/3</strong><span>Guided prediction flow</span></div>
                        <div class="predict-header-pill"><strong>{_best_name}</strong><span>Current best model</span></div>
                        <div class="predict-header-pill"><strong>{_r2:.2f} R²</strong><span>Model fit score</span></div>
                        <div class="predict-header-pill"><strong>±${_mae:,.0f}</strong><span>Average absolute error</span></div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── STEP 1: Background ───────────────────────────────────────
    if step == 1:
        st.subheader("Step 1 — Your Background")
        st.markdown('<div class="step-note">Tell us who you are in the market so we can ground the estimate in the right context.</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.session_state.country = st.selectbox(
                "Country", COUNTRIES,
                index=_safe_idx(COUNTRIES, "country")
            )
            st.session_state.education = st.selectbox(
                "Education Level", EDUCATIONS,
                index=_safe_idx(EDUCATIONS, "education")
            )
        with c2:

            st.session_state.devtype = st.selectbox(
                "Job Role / Developer Type", DEVTYPES,
                index=_safe_idx(DEVTYPES, "devtype")
            )

        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.predict_step = 2
            st.rerun()

    # ── STEP 2: Work Details ─────────────────────────────────────
    elif step == 2:
        st.subheader("Step 2 — Work Details")
        st.markdown('<div class="step-note">This is where the estimate becomes more personal. Your experience and tech stack strongly influence the final range.</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.session_state.employment = st.selectbox(
                "Employment Type", EMPLOYMENTS,
                index=_safe_idx(EMPLOYMENTS, "employment")
            )
        with c2:
            st.session_state.experience = st.slider(
                "Years of Experience", 0, 50,
                int(st.session_state.get("experience", 1))
            )

        st.session_state.frameworks = st.multiselect(
            "Web Frameworks you work with",
            options=FRAMEWORKS,
            default=st.session_state.get("frameworks", [FRAMEWORKS[0]] if FRAMEWORKS else []),
            help="Select all that apply"
        )

        st.session_state.languages = st.multiselect(
            "Programming Languages you use",
            options=LANGUAGES,
            default=st.session_state.get("languages", [LANGUAGES[0]] if LANGUAGES else []),
            help="Select all that apply"
        )

        col_back, col_next = st.columns(2)
        with col_back:
            if st.button("← Back", use_container_width=True):
                st.session_state.predict_step     = 1
                st.session_state.prediction_saved = False
                st.rerun()
        with col_next:
            if st.button("Predict My Salary →", type="primary", use_container_width=True):
                st.session_state.predict_step = 3
                st.rerun()

    # ── STEP 3: Result ───────────────────────────────────────────
    elif step == 3:
        try:
            predicted = predict_salary(
                country    = st.session_state.country,
                education  = st.session_state.education,
                employment = st.session_state.employment,
                experience = float(st.session_state.experience),
                frameworks = st.session_state.get("frameworks", []),
                languages  = st.session_state.get("languages", []),
                devtype    = st.session_state.devtype,
            )
        except Exception as e:
            st.error(f"Prediction error: {e}")
            st.stop()

        username = st.session_state.get("username", "")
        if not username:
            st.error("You must be logged in to run a prediction.")
            st.stop()

        allowed, rl_msg = rate_limit("predict", key=username.lower())
        if not allowed:
            st.warning(rl_msg)

        valid_input, val_msg = validate_prediction_input(
            country    = st.session_state.country,
            education  = st.session_state.education,
            employment = st.session_state.employment,
            experience = float(st.session_state.experience),
            devtype    = st.session_state.devtype,
            major      = "",
            frameworks = st.session_state.get("frameworks", []),
            languages  = st.session_state.get("languages", []),
            valid_countries  = COUNTRIES,
            valid_devtypes   = DEVTYPES,
            valid_majors     = [],
            valid_frameworks = FRAMEWORKS,
            valid_languages  = LANGUAGES,
        )
        if not valid_input:
            st.error(f"Input validation failed: {val_msg}")

        if allowed and valid_input and not st.session_state.get("prediction_saved", False):
            save_prediction(
                username         = username,
                country          = st.session_state.country,
                education        = st.session_state.education,
                employment       = st.session_state.employment,
                experience       = float(st.session_state.experience),
                devtype          = st.session_state.devtype,
                frameworks       = st.session_state.get("frameworks", []),
                languages        = st.session_state.get("languages", []),
                predicted_salary = predicted,
            )
            st.session_state.prediction_saved = True
            st.session_state.prediction = predicted

        low  = predicted * 0.85
        high = predicted * 1.15

        st.markdown(f"""
            <div class="result-shell">
                <div class="result-card">
                    <p style="margin:0; font-size:0.92rem; opacity:0.82; letter-spacing:0.08em; text-transform:uppercase;">Estimated Annual Salary</p>
                    <h1 style="margin:0.35rem 0; font-size:3.2rem; line-height:1; letter-spacing:-0.05em;">${predicted:,.0f}</h1>
                    <p style="margin:0; opacity:0.88; font-size:0.98rem;">Typical range: ${low:,.0f} — ${high:,.0f}</p>
                </div>
                <div class="result-sidecard">
                    <div class="result-side-title">What this means</div>
                    <div class="result-list">
                        <div class="result-list-item">
                            <strong>Your current estimate</strong>
                            <span>This is the salary benchmark that best matches the profile details you entered.</span>
                        </div>
                        <div class="result-list-item">
                            <strong>Expected range</strong>
                            <span>The range gives you a more realistic window instead of a single fixed number.</span>
                        </div>
                        <div class="result-list-item">
                            <strong>Try different scenarios</strong>
                            <span>Use the simulator below to compare how experience, location, education, or stack can change your earning potential.</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("Your inputs"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Country:** {st.session_state.country}")
                st.write(f"**Education:** {st.session_state.education}")
                st.write(f"**Job Role:** {st.session_state.devtype}")
            with c2:
                st.write(f"**Employment:** {st.session_state.employment}")
                st.write(f"**Experience:** {st.session_state.experience} years")
                st.write(f"**Frameworks:** {', '.join(st.session_state.get('frameworks', [])) or 'None'}")
                st.write(f"**Languages:** {', '.join(st.session_state.get('languages', [])) or 'None'}")

        # ── What-if simulator ──
        st.subheader("What-if Simulator")
        st.caption("Adjust any value to see how it affects your salary in real time.")

        sim_tab1, sim_tab2, sim_tab3 = st.tabs(["Location & Role", "Education", "Tech Stack"])

        with sim_tab1:
            s1c1, s1c2 = st.columns(2)
            with s1c1:
                sim_country = st.selectbox("Country", COUNTRIES,
                    index=_safe_idx(COUNTRIES, "country"), key="sim_country")
                sim_devtype = st.selectbox("Job Role", DEVTYPES,
                    index=_safe_idx(DEVTYPES, "devtype"), key="sim_devtype")
            with s1c2:
                sim_exp = st.slider("Years of Experience", 0, 50,
                    int(st.session_state.get("experience", 1)), key="sim_exp")

        with sim_tab2:
            s2c1, s2c2 = st.columns(2)
            with s2c1:
                sim_edu = st.selectbox("Education Level", EDUCATIONS,
                    index=_safe_idx(EDUCATIONS, "education"), key="sim_edu")


        with sim_tab3:
            s3c1, s3c2 = st.columns(2)
            with s3c1:
                sim_employment = st.selectbox("Employment Type", EMPLOYMENTS,
                    index=_safe_idx(EMPLOYMENTS, "employment"), key="sim_employment")
            with s3c2:
                sim_frameworks = st.multiselect("Web Frameworks", options=FRAMEWORKS,
                    default=st.session_state.get("frameworks", []), key="sim_frameworks")
            sim_languages = st.multiselect("Programming Languages", options=LANGUAGES,
                default=st.session_state.get("languages", []), key="sim_languages")

        try:
            sim_salary = predict_salary(
                country    = sim_country,
                education  = sim_edu,
                employment = sim_employment,
                experience = float(sim_exp),
                frameworks = sim_frameworks,
                languages  = sim_languages,
                devtype    = sim_devtype,
            )
            diff     = sim_salary - predicted
            diff_pct = (diff / predicted) * 100
            diff_str = f"+${diff:,.0f} (+{diff_pct:.1f}%)" if diff >= 0 else f"-${abs(diff):,.0f} ({diff_pct:.1f}%)"
            diff_col = "#10b981" if diff >= 0 else "#ef4444"

            st.markdown(f"""
                <div class="sim-result" style="border-top:4px solid {diff_col};">
                    <p style="margin:0; color:#6b7c8d; font-size:0.9rem;">Simulated Salary</p>
                    <h2 style="margin:0.25rem 0; color:#1a2e42; font-size:2rem;">${sim_salary:,.0f}</h2>
                    <p style="margin:0; color:{diff_col}; font-weight:bold;">{diff_str} vs your prediction</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Simulator error: {e}")

        st.markdown("---")
        if st.button("Start Over", use_container_width=True):
            st.session_state.predict_step     = 1
            st.session_state.prediction_saved = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
