"""
Salary Prediction Model — 2025 Stack Overflow Survey
Enhanced Training Pipeline v4.1 — Target R² 0.75+

Changes from v3.0:
  1. Salary cap kept at $15k–$400k (reverted v4.0 tightening — more data wins)
  2. QuantileTransformer only on raw salary (removed double log+QT transform)
  3. Added 3 high-value features: Tech_seniority_score, PPP_factor, Country_ppp_mean
  4. Optuna increased to 300 trials with wider search space + colsample_bylevel
  5. CatBoost tuned: 2000 iters, depth=7, stronger regularization
  6. Stacking kept as v3 (XGB + LGBM + GBM → BayesianRidge) — MLP removed

Run: python train_models.py
Saves best model to best_salary_model.pkl
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler, QuantileTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression, BayesianRidge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                               StackingRegressor)
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("  ⚠️  CatBoost not installed. Run: pip install catboost")

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("  ⚠️  Optuna not installed. Run: pip install optuna")
    from sklearn.model_selection import RandomizedSearchCV

DATA_PATH  = os.path.join("data", "survey_results_public.csv")
MODEL_PATH = "best_salary_model.pkl"

# ══════════════════════════════════════════════════════════════════════
# PPP FACTORS  (World Bank 2024 approximate)
# Factor > 1 means local currency buys more than USD → salary worth more
# ══════════════════════════════════════════════════════════════════════

PPP_FACTORS = {
    "United States":         1.00, "Switzerland":           0.85,
    "Norway":                0.87, "Denmark":               0.88,
    "Australia":             0.92, "Canada":                0.93,
    "United Kingdom":        0.93, "Germany":               0.94,
    "Sweden":                0.91, "Netherlands":           0.93,
    "Finland":               0.95, "Austria":               0.95,
    "Belgium":               0.95, "France":                0.97,
    "New Zealand":           0.97, "Ireland":               0.90,
    "Israel":                0.96, "Singapore":             0.90,
    "Japan":                 1.10, "South Korea":           1.12,
    "Italy":                 1.08, "Spain":                 1.14,
    "Czech Republic":        1.55, "Portugal":              1.30,
    "Poland":                1.65, "Hungary":               1.70,
    "Romania":               1.75, "Bulgaria":              2.10,
    "Croatia":               1.55, "Slovakia":              1.50,
    "Lithuania":             1.60, "Latvia":                1.65,
    "Estonia":               1.45, "Slovenia":              1.30,
    "Greece":                1.40, "Turkey":                2.20,
    "Russia":                2.20, "Ukraine":               3.00,
    "Brazil":                2.30, "Argentina":             3.50,
    "Mexico":                2.40, "Colombia":              3.20,
    "Chile":                 2.00, "Peru":                  2.80,
    "India":                 4.00, "Pakistan":              5.00,
    "Bangladesh":            5.50, "Sri Lanka":             4.50,
    "Nepal":                 6.00, "China":                 2.40,
    "Indonesia":             3.50, "Philippines":           3.80,
    "Vietnam":               4.20, "Thailand":              2.80,
    "Malaysia":              2.20, "South Africa":          3.20,
    "Nigeria":               4.50, "Kenya":                 5.00,
    "Egypt":                 4.20, "Morocco":               4.00,
    "Ghana":                 5.50, "Iran":                  5.00,
    "Saudi Arabia":          1.50, "United Arab Emirates":  1.30,
    "Qatar":                 1.20, "Kuwait":                1.40,
    "Jordan":                2.50, "Iraq":                  3.00,
}

# ══════════════════════════════════════════════════════════════════════
# TECH SENIORITY SCORE
# Weights languages by market value / seniority signal
# ══════════════════════════════════════════════════════════════════════

LANG_SENIORITY = {
    "Rust":          10, "Go":             9, "Kotlin":          8,
    "Scala":          9, "Swift":           8, "TypeScript":      8,
    "Python":         8, "C++":             7, "C":               7,
    "Java":           7, "C#":              7, "Ruby":            6,
    "JavaScript":     6, "Bash/Shell (all shells)": 6,
    "PowerShell":     5, "SQL":             5, "HTML/CSS":        3,
    "PHP":            4, "R":               6, "MATLAB":          5,
    "Dart":           6, "Lua":             5, "Perl":            4,
    "Elixir":         8, "Haskell":         9, "Clojure":         9,
    "F#":             8, "Julia":           7, "Assembly":        7,
    "Groovy":         5, "VBA":             3, "COBOL":           4,
    "Objective-C":    5, "Erlang":          8,
}

# ══════════════════════════════════════════════════════════════════════
# CLEANING HELPERS
# ══════════════════════════════════════════════════════════════════════

def clean_education(x):
    if pd.isnull(x): return np.nan
    x = str(x)
    if "Professional degree" in x or "Ph.D" in x: return "Post grad"
    if "Master" in x:                              return "Master's degree"
    if "Bachelor" in x:                            return "Bachelor's degree"
    if "Associate" in x or "Some college" in x or "Secondary" in x or "Primary" in x:
        return "Less than Bachelor's"
    return np.nan

def clean_employment(x):
    if pd.isnull(x): return np.nan
    x = str(x)
    if x.startswith("Employed"):                                        return "Full-time"
    if "contractor" in x or "freelancer" in x or "self-employed" in x: return "Freelancer/Contractor"
    if x == "Student":                                                  return "Student"
    return np.nan

def clean_devtype(x):
    if pd.isnull(x): return "Other"
    x = x.lower()
    if "engineering manager" in x or "manager" in x: return "Engineering Manager"
    if "data scientist"      in x:                   return "Data Scientist"
    if "machine learning"    in x or "ai/" in x:     return "ML/AI Engineer"
    if "devops"              in x or "site reliability" in x: return "DevOps Engineer"
    if "full-stack"          in x:                   return "Full-Stack Developer"
    if "back-end"            in x:                   return "Back-End Developer"
    if "front-end"           in x:                   return "Front-End Developer"
    if "mobile"              in x:                   return "Mobile Developer"
    if "embedded"            in x:                   return "Embedded Developer"
    if "data engineer"       in x:                   return "Data Engineer"
    if "database"            in x or "dba" in x:     return "Database Administrator"
    if "cloud"               in x:                   return "Cloud Engineer"
    if "security"            in x:                   return "Security Engineer"
    if "designer"            in x:                   return "Designer"
    if "student"             in x:                   return "Student"
    if "academic"            in x or "research" in x: return "Academic/Research"
    return "Other Developer"

def clean_remote(x):
    if pd.isnull(x): return "Unknown"
    x = str(x).lower()
    if "remote" in x and "hybrid" not in x and "in-person" not in x: return "Remote"
    if "hybrid" in x:     return "Hybrid"
    if "in-person" in x or "office" in x: return "In-person"
    return "Unknown"

def clean_orgsize(x):
    if pd.isnull(x): return "Unknown"
    x = str(x)
    if "10,000" in x or "5,000" in x:               return "Large (5000+)"
    if "1,000" in x or "500" in x or "100 to" in x: return "Medium (100-4999)"
    if "20 to" in x or "10 to" in x or "2 to" in x: return "Small (2-99)"
    if "one" in x.lower() or "just me" in x.lower() or "1 " in x: return "Solo"
    if "freelance" in x.lower() or "contractor" in x.lower():      return "Solo"
    return "Unknown"

def clean_age(x):
    if pd.isnull(x): return "Unknown"
    x = str(x)
    if "Under 18" in x or "18-24" in x: return "18-24"
    if "25-34" in x: return "25-34"
    if "35-44" in x: return "35-44"
    if "45-54" in x: return "45-54"
    if "55-64" in x or "65" in x: return "55+"
    return "Unknown"

def clean_industry(x):
    if pd.isnull(x): return "Other"
    x = str(x).lower()
    if "software" in x or "information technology" in x or "saas" in x: return "Tech/Software"
    if "financial" in x or "banking" in x or "fintech" in x: return "Finance"
    if "health" in x or "medical" in x:    return "Healthcare"
    if "education" in x or "academic" in x: return "Education"
    if "government" in x or "public" in x: return "Government"
    if "consulting" in x:                  return "Consulting"
    if "retail" in x or "ecommerce" in x or "e-commerce" in x: return "Retail/Ecommerce"
    if "media" in x or "entertainment" in x or "gaming" in x:  return "Media/Entertainment"
    if "manufacturing" in x or "automotive" in x or "aerospace" in x: return "Manufacturing"
    if "telecom" in x: return "Telecom"
    return "Other"

def clean_yearscode(x):
    if pd.isnull(x): return np.nan
    x = str(x).strip()
    if "less than" in x.lower() or "fewer" in x.lower(): return 0.5
    if "more than" in x.lower(): return 51
    try:    return float(x)
    except: return np.nan

def make_binary_cols(series, prefix, top_n):
    from collections import Counter
    counts = Counter()
    for row in series.dropna():
        for tech in str(row).split(";"):
            tech = tech.strip()
            if tech: counts[tech] += 1
    top_techs = [t for t, _ in counts.most_common(top_n)]
    cols = {}
    for tech in top_techs:
        safe = (tech.lower()
                .replace(" ", "_").replace(".", "_").replace("/", "_")
                .replace("#", "sharp").replace("+", "plus")
                .replace("(", "").replace(")", "").replace("-", "_").replace(",", ""))
        col_name = f"{prefix}__{safe}"
        cols[col_name] = series.apply(
            lambda x, t=tech: 1 if pd.notna(x) and t in str(x).split(";") else 0)
    return pd.DataFrame(cols), top_techs


# ══════════════════════════════════════════════════════════════════════
# RANK MAPS
# ══════════════════════════════════════════════════════════════════════

DEVTYPE_SALARY_RANK = {
    "Engineering Manager":   10, "ML/AI Engineer":         9,
    "Data Scientist":          9, "Cloud Engineer":          8,
    "Security Engineer":       8, "Data Engineer":           8,
    "DevOps Engineer":         8, "Back-End Developer":      7,
    "Full-Stack Developer":    7, "Embedded Developer":      7,
    "Mobile Developer":        6, "Front-End Developer":     6,
    "Database Administrator":  6, "Other Developer":         5,
    "Academic/Research":       4, "Designer":                4,
    "Student":                 2, "Other":                   4,
}

EDUCATION_SALARY_RANK = {
    "Post grad": 4, "Master's degree": 3,
    "Bachelor's degree": 2, "Less than Bachelor's": 1,
}

ORGSIZE_RANK = {
    "Solo": 1, "Small (2-99)": 2, "Medium (100-4999)": 3,
    "Large (5000+)": 4, "Unknown": 2,
}

REMOTE_RANK = {"In-person": 1, "Hybrid": 2, "Remote": 3, "Unknown": 2}
AGE_RANK    = {"18-24": 1, "25-34": 2, "35-44": 3, "45-54": 4, "55+": 5, "Unknown": 2}


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  SALARY PREDICTION — 2025 Stack Overflow Survey")
    print("  Enhanced Training Pipeline v4.1  (Target R² 0.75+)")
    print("=" * 65)

    from multiprocessing import cpu_count
    n_cores = max(1, cpu_count() - 1)

    # ── 1. Load ────────────────────────────────────────────────────
    print("\n[1/9] Loading data...")
    KEEP_COLS = [
        "ConvertedCompYearly", "WorkExp", "EdLevel", "Employment",
        "Country", "DevType", "LanguageHaveWorkedWith",
        "WebframeHaveWorkedWith", "RemoteWork", "OrgSize",
        "Age", "YearsCode", "Industry",
    ]
    df = pd.read_csv(DATA_PATH, usecols=KEEP_COLS)
    print(f"      Raw rows: {len(df):,}")

    # ── 2. Clean ───────────────────────────────────────────────────
    print("\n[2/9] Cleaning data...")
    df["EdLevel"]    = df["EdLevel"].apply(clean_education)
    df["Employment"] = df["Employment"].apply(clean_employment)
    df["DevType"]    = df["DevType"].apply(clean_devtype)
    df["RemoteWork"] = df["RemoteWork"].apply(clean_remote)
    df["OrgSize"]    = df["OrgSize"].apply(clean_orgsize)
    df["Age"]        = df["Age"].apply(clean_age)
    df["Industry"]   = df["Industry"].apply(clean_industry)
    df["YearsCode"]  = df["YearsCode"].apply(clean_yearscode)

    df = df[df["Employment"] == "Full-time"]
    df = df.dropna(subset=["ConvertedCompYearly"])

    # Keep v3 salary cap — wider range = more training data
    df = df[df["ConvertedCompYearly"] >= 15_000]
    df = df[df["ConvertedCompYearly"] <= 400_000]
    df.rename(columns={"ConvertedCompYearly": "Salary"}, inplace=True)

    df = df.dropna(subset=["WorkExp"])
    df.rename(columns={"WorkExp": "Experience"}, inplace=True)
    df["Experience"] = pd.to_numeric(df["Experience"], errors="coerce")
    df = df.dropna(subset=["Experience"])
    df["Experience"] = df["Experience"].clip(0, 50)
    df = df.dropna(subset=["EdLevel", "Employment", "Country", "DevType"])

    country_counts = df["Country"].value_counts()
    df = df[df["Country"].isin(country_counts[country_counts >= 50].index)]

    n_before = len(df)
    df = df.drop_duplicates()
    print(f"      Duplicates removed: {n_before - len(df):,}")
    print(f"      Clean rows: {len(df):,}")
    print(f"      Salary range: ${df['Salary'].min():,.0f} — ${df['Salary'].max():,.0f}")
    print(f"      Median salary: ${df['Salary'].median():,.0f}")

    # ── 3. Tech stack binary features ─────────────────────────────
    print("\n[3/9] Engineering tech stack features...")
    lang_df,  TOP_LANGUAGES  = make_binary_cols(df["LanguageHaveWorkedWith"], "Lang",  15)
    frame_df, TOP_FRAMEWORKS = make_binary_cols(df["WebframeHaveWorkedWith"], "Frame", 12)
    LANGUAGE_COLS  = lang_df.columns.tolist()
    FRAMEWORK_COLS = frame_df.columns.tolist()
    df = pd.concat([df.reset_index(drop=True),
                    lang_df.reset_index(drop=True),
                    frame_df.reset_index(drop=True)], axis=1)
    print(f"      Languages : {len(LANGUAGE_COLS)} cols — {TOP_LANGUAGES}")
    print(f"      Frameworks: {len(FRAMEWORK_COLS)} cols — {TOP_FRAMEWORKS}")

    # ── 4. Feature engineering (leak-safe) ────────────────────────
    print("\n[4/9] Feature engineering (leak-safe)...")
    df["DevType_rank"]   = df["DevType"].map(DEVTYPE_SALARY_RANK).fillna(4)
    df["Education_rank"] = df["EdLevel"].map(EDUCATION_SALARY_RANK).fillna(2)
    df["OrgSize_rank"]   = df["OrgSize"].map(ORGSIZE_RANK).fillna(2)
    df["Remote_rank"]    = df["RemoteWork"].map(REMOTE_RANK).fillna(2)
    df["Age_rank"]       = df["Age"].map(AGE_RANK).fillna(2)

    df["Experience_sq"]  = df["Experience"] ** 2
    df["Experience_log"] = np.log1p(df["Experience"])
    df["Num_languages"]  = df["LanguageHaveWorkedWith"].apply(
        lambda x: len(str(x).split(";")) if pd.notna(x) else 0)
    df["Num_frameworks"] = df["WebframeHaveWorkedWith"].apply(
        lambda x: len(str(x).split(";")) if pd.notna(x) else 0)
    df["Tech_breadth"]   = df["Num_languages"] + df["Num_frameworks"]

    df["YearsCode"] = df["YearsCode"].fillna(df["Experience"])
    df["YearsCode"] = pd.to_numeric(df["YearsCode"], errors="coerce").fillna(df["Experience"])
    df["YearsCode"] = df["YearsCode"].clip(0, 55)
    df["Code_Work_Gap"] = (df["YearsCode"] - df["Experience"]).clip(0, 30)

    df["Exp_bucket"] = pd.cut(
        df["Experience"],
        bins=[-1, 2, 5, 10, 20, 51],
        labels=[1, 2, 3, 4, 5]
    ).astype(float).fillna(1)

    # v3 interaction features
    df["Experience_x_DevType"]     = df["Experience"] * df["DevType_rank"]
    df["Experience_x_Education"]   = df["Experience"] * df["Education_rank"]
    df["Experience_x_OrgSize"]     = df["Experience"] * df["OrgSize_rank"]
    df["DevType_x_Education"]      = df["DevType_rank"] * df["Education_rank"]
    df["Experience_x_TechBreadth"] = df["Experience"] * df["Tech_breadth"]
    df["Experience_x_Remote"]      = df["Experience"] * df["Remote_rank"]
    df["Age_x_Experience"]         = df["Age_rank"] * df["Experience"]

    # NEW v4.1: PPP factor (cost-of-living normalization per country)
    df["PPP_factor"] = df["Country"].map(PPP_FACTORS).fillna(3.0)

    # NEW v4.1: Tech seniority score (language quality, not just count)
    def compute_tech_seniority(langs_str):
        if pd.isnull(langs_str) or str(langs_str) == "nan":
            return 5.0
        scores = [LANG_SENIORITY.get(l.strip(), 5)
                  for l in str(langs_str).split(";") if l.strip()]
        return float(np.mean(scores)) if scores else 5.0

    df["Tech_seniority_score"] = df["LanguageHaveWorkedWith"].apply(compute_tech_seniority)
    df["Tech_seniority_x_Exp"] = df["Tech_seniority_score"] * df["Experience"]

    print("      Base features added")

    # ── 5. Train / Val / Test split ────────────────────────────────
    print("\n[5/9] Splitting data 70/15/15...")

    NUMERIC_FEATURES_BASE = (
        ["Experience", "Experience_sq", "Experience_log",
         "YearsCode", "Code_Work_Gap", "Exp_bucket",
         "Num_languages", "Num_frameworks", "Tech_breadth",
         "Tech_seniority_score", "Tech_seniority_x_Exp", "PPP_factor"]
        + LANGUAGE_COLS + FRAMEWORK_COLS
        + ["DevType_rank", "Education_rank", "OrgSize_rank",
           "Remote_rank", "Age_rank",
           "Experience_x_DevType", "Experience_x_Education",
           "Experience_x_OrgSize", "DevType_x_Education",
           "Experience_x_TechBreadth", "Experience_x_Remote",
           "Age_x_Experience"]
    )

    CATEGORICAL_FEATURES = ["Country", "EdLevel", "Employment", "DevType",
                             "RemoteWork", "OrgSize", "Age", "Industry"]

    X_all  = df.copy()
    y_raw  = df["Salary"].values

    X_train_full, X_temp, y_train_raw, y_temp_raw = train_test_split(
        X_all, y_raw, test_size=0.30, random_state=42)
    X_val, X_test, y_val_raw, y_test_raw = train_test_split(
        X_temp, y_temp_raw, test_size=0.50, random_state=42)

    print(f"      Train: {len(X_train_full):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")

    # ── 5b. Target transformation ──────────────────────────────────
    # QuantileTransformer only on raw salary — no log pre-transform
    print("      Fitting QuantileTransformer on train salaries...")
    qt = QuantileTransformer(output_distribution="normal",
                             n_quantiles=min(1000, len(X_train_full)),
                             random_state=42)
    y_train_t = qt.fit_transform(y_train_raw.reshape(-1, 1)).ravel()
    y_val_t   = qt.transform(y_val_raw.reshape(-1, 1)).ravel()
    y_test_t  = qt.transform(y_test_raw.reshape(-1, 1)).ravel()

    # ── 5c. Country rank (train-only, no leakage) ──────────────────
    print("      Computing Country_rank from train set only...")
    country_median_train = X_train_full.groupby("Country")["Salary"].median()
    country_rank_series  = pd.qcut(country_median_train.rank(method="first"),
                                   q=5, labels=[1, 2, 3, 4, 5]).astype(float)
    COUNTRY_SALARY_RANK  = country_rank_series.to_dict()

    country_mean_train = X_train_full.groupby("Country")["Salary"].mean().to_dict()
    country_std_train  = X_train_full.groupby("Country")["Salary"].std().fillna(0).to_dict()
    devtype_mean_train = X_train_full.groupby("DevType")["Salary"].mean().to_dict()
    edu_mean_train     = X_train_full.groupby("EdLevel")["Salary"].mean().to_dict()
    global_mean        = float(X_train_full["Salary"].mean())
    global_std         = float(X_train_full["Salary"].std())

    # NEW v4.1: PPP-adjusted country mean (train-only)
    country_ppp_mean_train = (
        X_train_full
        .assign(Salary_PPP=X_train_full["Salary"] * X_train_full["PPP_factor"])
        .groupby("Country")["Salary_PPP"].mean()
        .to_dict()
    )

    print("      Computing Country×DevType median salary (train-only)...")
    X_train_full["Country_DevType"] = X_train_full["Country"] + "_" + X_train_full["DevType"]
    country_devtype_median = X_train_full.groupby("Country_DevType")["Salary"].median().to_dict()

    for split_df in [X_train_full, X_val, X_test]:
        split_df["Country_rank"]              = split_df["Country"].map(COUNTRY_SALARY_RANK).fillna(3)
        split_df["Experience_x_Country"]      = split_df["Experience"] * split_df["Country_rank"]
        split_df["Country_mean_salary"]       = split_df["Country"].map(country_mean_train).fillna(global_mean)
        split_df["Country_std_salary"]        = split_df["Country"].map(country_std_train).fillna(global_std)
        split_df["Experience_x_Country_mean"] = split_df["Experience"] * split_df["Country_mean_salary"]
        split_df["DevType_mean_salary"]       = split_df["DevType"].map(devtype_mean_train).fillna(global_mean)
        split_df["EdLevel_mean_salary"]       = split_df["EdLevel"].map(edu_mean_train).fillna(global_mean)
        split_df["Country_ppp_mean"]          = split_df["Country"].map(country_ppp_mean_train).fillna(global_mean)

        split_df["Country_DevType"]           = split_df["Country"] + "_" + split_df["DevType"]
        split_df["Country_DevType_salary"]    = split_df["Country_DevType"].map(
            country_devtype_median).fillna(global_mean)

    print("      Computing language value scores (train-only)...")
    lang_salary_map = {}
    for lang_col in LANGUAGE_COLS:
        mask = X_train_full[lang_col] == 1
        lang_salary_map[lang_col] = (X_train_full.loc[mask, "Salary"].median()
                                     if mask.sum() > 10 else global_mean)

    for split_df in [X_train_full, X_val, X_test]:
        num_langs = split_df["Num_languages"].replace(0, 1)
        split_df["Lang_value_score"] = sum(
            split_df[col] * lang_salary_map[col] for col in LANGUAGE_COLS
        ) / num_langs

    NUMERIC_FEATURES = NUMERIC_FEATURES_BASE + [
        "Country_rank", "Experience_x_Country", "Experience_x_Country_mean",
        "Country_mean_salary", "Country_std_salary", "Country_ppp_mean",
        "DevType_mean_salary", "EdLevel_mean_salary",
        "Country_DevType_salary", "Lang_value_score",
    ]
    ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

    print(f"      Numeric    : {len(NUMERIC_FEATURES)}")
    print(f"      Categorical: {len(CATEGORICAL_FEATURES)}")
    print(f"      Total      : {len(ALL_FEATURES)}")

    X_train  = X_train_full[ALL_FEATURES]
    X_val_f  = X_val[ALL_FEATURES]
    X_test_f = X_test[ALL_FEATURES]

    # ── 6. Preprocessor ────────────────────────────────────────────
    preprocessor = ColumnTransformer(transformers=[
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
         CATEGORICAL_FEATURES),
    ])

    # ── 7. Baseline models ─────────────────────────────────────────
    print("\n[6/9] Training baseline models...")

    MODELS = {
        "Linear Regression":  LinearRegression(),
        "Bayesian Ridge":     BayesianRidge(max_iter=500, tol=1e-6),
        "Decision Tree":      DecisionTreeRegressor(random_state=42, max_depth=10,
                                                    min_samples_leaf=8, min_samples_split=20),
        "Random Forest":      RandomForestRegressor(random_state=42, n_estimators=200,
                                                    max_depth=12, min_samples_leaf=8,
                                                    n_jobs=n_cores),
        "XGBoost":            XGBRegressor(n_estimators=400, learning_rate=0.02, max_depth=6,
                                           subsample=0.8, colsample_bytree=0.8,
                                           min_child_weight=5, reg_alpha=0.1, reg_lambda=1.0,
                                           objective="reg:squarederror",
                                           n_jobs=n_cores, tree_method="hist",
                                           verbosity=0, random_state=42),
        "LightGBM":           LGBMRegressor(n_estimators=400, learning_rate=0.02, max_depth=8,
                                            num_leaves=63, subsample=0.8, colsample_bytree=0.8,
                                            min_child_samples=20, reg_alpha=0.1, reg_lambda=1.0,
                                            n_jobs=n_cores, verbose=-1, random_state=42),
        "Gradient Boosting":  GradientBoostingRegressor(n_estimators=200, learning_rate=0.03,
                                                        max_depth=6, subsample=0.8,
                                                        min_samples_leaf=10, random_state=42),
    }

    results = {}
    print(f"\n  {'Model':<22} {'Train R2':>9} {'Val R2':>9} {'Test R2':>9} "
          f"{'Test MAE':>12} {'Test RMSE':>12} {'Overfit':>10}")
    print("  " + "-" * 95)

    def evaluate(name, pipe):
        pipe.fit(X_train, y_train_t)
        tr_r2 = r2_score(y_train_t, pipe.predict(X_train))
        va_r2 = r2_score(y_val_t,   pipe.predict(X_val_f))
        te_r2 = r2_score(y_test_t,  pipe.predict(X_test_f))

        y_pred_t  = qt.inverse_transform(pipe.predict(X_test_f).reshape(-1, 1)).ravel()
        y_pred_tr = qt.inverse_transform(pipe.predict(X_train).reshape(-1, 1)).ravel()

        mae   = mean_absolute_error(y_test_raw, y_pred_t)
        rmse  = np.sqrt(mean_squared_error(y_test_raw, y_pred_t))
        overf = max(0.0, tr_r2 - te_r2)

        print(f"  {name:<22} {tr_r2:>9.4f} {va_r2:>9.4f} {te_r2:>9.4f} "
              f"  ${mae:>9,.0f}   ${rmse:>9,.0f} {overf:>10.4f}")

        results[name] = dict(
            pipeline=pipe, train_r2=tr_r2, val_r2=va_r2, test_r2=te_r2,
            test_mae=mae, test_rmse=rmse, overfit=overf,
            y_pred=y_pred_t, y_actual=y_test_raw,
            y_pred_train=y_pred_tr, y_actual_train=y_train_raw,
        )

    for name, model in MODELS.items():
        pipe = Pipeline([("preprocess", preprocessor), ("model", model)])
        evaluate(name, pipe)

    # ── 8. Optuna tuning — 300 trials ─────────────────────────────
    print("\n[7/9] Optuna hyperparameter search (300 trials each)...")

    preprocessor.fit(X_train)
    X_train_proc = preprocessor.transform(X_train)
    X_val_proc   = preprocessor.transform(X_val_f)
    X_test_proc  = preprocessor.transform(X_test_f)

    def tune_xgboost():
        def objective(trial):
            params = dict(
                n_estimators      = trial.suggest_int("n_estimators", 600, 2500),
                max_depth         = trial.suggest_int("max_depth", 3, 8),
                learning_rate     = trial.suggest_float("learning_rate", 0.003, 0.05, log=True),
                subsample         = trial.suggest_float("subsample", 0.5, 1.0),
                colsample_bytree  = trial.suggest_float("colsample_bytree", 0.4, 1.0),
                colsample_bylevel = trial.suggest_float("colsample_bylevel", 0.5, 1.0),
                min_child_weight  = trial.suggest_int("min_child_weight", 3, 30),
                reg_alpha         = trial.suggest_float("reg_alpha", 0.01, 20.0, log=True),
                reg_lambda        = trial.suggest_float("reg_lambda", 0.1, 30.0, log=True),
                gamma             = trial.suggest_float("gamma", 0.0, 2.0),
            )
            model = XGBRegressor(
                **params, objective="reg:squarederror",
                n_jobs=n_cores, tree_method="hist", verbosity=0, random_state=42)
            model.fit(X_train_proc, y_train_t,
                      eval_set=[(X_val_proc, y_val_t)],
                      verbose=False)
            return r2_score(y_val_t, model.predict(X_val_proc))

        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=300, show_progress_bar=False)
        best = study.best_params
        print(f"      XGBoost best val R²: {study.best_value:.4f}  params: {best}")
        return XGBRegressor(
            **best, objective="reg:squarederror",
            n_jobs=n_cores, tree_method="hist", verbosity=0, random_state=42)

    def tune_lightgbm():
        def objective(trial):
            params = dict(
                n_estimators      = trial.suggest_int("n_estimators", 600, 2500),
                max_depth         = trial.suggest_int("max_depth", 3, 8),
                num_leaves        = trial.suggest_int("num_leaves", 20, 200),
                learning_rate     = trial.suggest_float("learning_rate", 0.003, 0.05, log=True),
                subsample         = trial.suggest_float("subsample", 0.5, 1.0),
                colsample_bytree  = trial.suggest_float("colsample_bytree", 0.4, 1.0),
                min_child_samples = trial.suggest_int("min_child_samples", 5, 150),
                reg_alpha         = trial.suggest_float("reg_alpha", 0.01, 20.0, log=True),
                reg_lambda        = trial.suggest_float("reg_lambda", 0.1, 30.0, log=True),
                min_split_gain    = trial.suggest_float("min_split_gain", 0.0, 1.0),
            )
            model = LGBMRegressor(**params, n_jobs=n_cores, verbose=-1, random_state=42)
            model.fit(X_train_proc, y_train_t,
                      eval_set=[(X_val_proc, y_val_t)])
            return r2_score(y_val_t, model.predict(X_val_proc))

        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=300, show_progress_bar=False)
        best = study.best_params
        print(f"      LightGBM best val R²: {study.best_value:.4f}  params: {best}")
        return LGBMRegressor(**best, n_jobs=n_cores, verbose=-1, random_state=42)

    def tune_randomized(ModelClass, param_grid, name):
        pipe_t = Pipeline([("preprocess", preprocessor), ("model", ModelClass)])
        search = RandomizedSearchCV(pipe_t, param_grid, n_iter=30, cv=3,
                                    scoring="r2", random_state=42, n_jobs=1, verbose=0)
        search.fit(X_train, y_train_t)
        print(f"      {name} best val R²: {search.best_score_:.4f}")
        return search.best_estimator_.named_steps["model"]

    if OPTUNA_AVAILABLE:
        print("  🔍 Tuning XGBoost (Optuna 300 trials)...")
        best_xgb_model = tune_xgboost()
        print("  🔍 Tuning LightGBM (Optuna 300 trials)...")
        best_lgbm_model = tune_lightgbm()
    else:
        print("  🔍 Tuning XGBoost (RandomizedSearchCV fallback)...")
        best_xgb_model = tune_randomized(
            XGBRegressor(objective="reg:squarederror", n_jobs=n_cores,
                         tree_method="hist", verbosity=0, random_state=42),
            {"model__n_estimators": [600, 1000, 1500], "model__max_depth": [4, 5, 6, 7],
             "model__learning_rate": [0.005, 0.01, 0.02], "model__subsample": [0.6, 0.7, 0.8],
             "model__reg_alpha": [0.5, 1.0, 5.0], "model__reg_lambda": [3.0, 5.0, 10.0]},
            "XGBoost"
        )
        print("  🔍 Tuning LightGBM (RandomizedSearchCV fallback)...")
        best_lgbm_model = tune_randomized(
            LGBMRegressor(n_jobs=n_cores, verbose=-1, random_state=42),
            {"model__n_estimators": [600, 1000, 1500], "model__max_depth": [4, 5, 6, 7],
             "model__num_leaves": [31, 63, 100], "model__learning_rate": [0.005, 0.01, 0.02],
             "model__subsample": [0.6, 0.7, 0.8], "model__reg_alpha": [0.5, 1.0, 5.0]},
            "LightGBM"
        )

    for name, model in [("XGBoost Tuned", best_xgb_model),
                         ("LightGBM Tuned", best_lgbm_model)]:
        pipe = Pipeline([("preprocess", preprocessor), ("model", model)])
        evaluate(name, pipe)

    # ── 9. CatBoost ────────────────────────────────────────────────
    if CATBOOST_AVAILABLE:
        print("\n[8/9] Training CatBoost (native categoricals)...")
        cat_feature_names = CATEGORICAL_FEATURES
        cb_model = CatBoostRegressor(
            iterations=2000, learning_rate=0.015, depth=7,
            loss_function="RMSE", eval_metric="R2",
            cat_features=cat_feature_names,
            l2_leaf_reg=5.0,
            min_data_in_leaf=15,
            early_stopping_rounds=100,
            random_seed=42, verbose=100,
        )

        X_train_cb = X_train_full[ALL_FEATURES].copy()
        X_val_cb   = X_val[ALL_FEATURES].copy()
        X_test_cb  = X_test[ALL_FEATURES].copy()

        for split_df in [X_train_cb, X_val_cb, X_test_cb]:
            for col in CATEGORICAL_FEATURES:
                split_df[col] = split_df[col].astype(str).fillna("Unknown")

        cb_model.fit(
            X_train_cb, y_train_t,
            eval_set=(X_val_cb, y_val_t),
            use_best_model=True,
        )

        tr_r2 = r2_score(y_train_t, cb_model.predict(X_train_cb))
        va_r2 = r2_score(y_val_t,   cb_model.predict(X_val_cb))
        te_r2 = r2_score(y_test_t,  cb_model.predict(X_test_cb))
        y_pred_cb    = qt.inverse_transform(cb_model.predict(X_test_cb).reshape(-1, 1)).ravel()
        y_pred_cb_tr = qt.inverse_transform(cb_model.predict(X_train_cb).reshape(-1, 1)).ravel()
        mae   = mean_absolute_error(y_test_raw, y_pred_cb)
        rmse  = np.sqrt(mean_squared_error(y_test_raw, y_pred_cb))
        overf = max(0.0, tr_r2 - te_r2)

        print(f"  {'CatBoost':<22} {tr_r2:>9.4f} {va_r2:>9.4f} {te_r2:>9.4f} "
              f"  ${mae:>9,.0f}   ${rmse:>9,.0f} {overf:>10.4f}")

        results["CatBoost"] = dict(
            pipeline=None,
            catboost_model=cb_model,
            catboost_cat_features=cat_feature_names,
            catboost_all_features=ALL_FEATURES,
            train_r2=tr_r2, val_r2=va_r2, test_r2=te_r2,
            test_mae=mae, test_rmse=rmse, overfit=overf,
            y_pred=y_pred_cb, y_actual=y_test_raw,
            y_pred_train=y_pred_cb_tr, y_actual_train=y_train_raw,
        )

    # ── 10. Stacking ensemble ──────────────────────────────────────
    print("\n[9/9] Building stacking ensemble...")

    xgb_pipe_tuned  = results["XGBoost Tuned"]["pipeline"]
    lgbm_pipe_tuned = results["LightGBM Tuned"]["pipeline"]
    gbm_pipe        = results["Gradient Boosting"]["pipeline"]

    stack = StackingRegressor(
        estimators=[
            ("xgb",  xgb_pipe_tuned),
            ("lgbm", lgbm_pipe_tuned),
            ("gbm",  gbm_pipe),
        ],
        final_estimator=BayesianRidge(),
        cv=5,
        n_jobs=1,
        passthrough=False,
    )
    print("      Fitting stacking ensemble (cv=5) — this may take a few minutes...")
    stack.fit(X_train, y_train_t)

    tr_r2 = r2_score(y_train_t, stack.predict(X_train))
    va_r2 = r2_score(y_val_t,   stack.predict(X_val_f))
    te_r2 = r2_score(y_test_t,  stack.predict(X_test_f))
    y_pred_s    = qt.inverse_transform(stack.predict(X_test_f).reshape(-1, 1)).ravel()
    y_pred_s_tr = qt.inverse_transform(stack.predict(X_train).reshape(-1, 1)).ravel()
    mae   = mean_absolute_error(y_test_raw, y_pred_s)
    rmse  = np.sqrt(mean_squared_error(y_test_raw, y_pred_s))
    overf = max(0.0, tr_r2 - te_r2)

    print(f"  {'Stacking Ensemble':<22} {tr_r2:>9.4f} {va_r2:>9.4f} {te_r2:>9.4f} "
          f"  ${mae:>9,.0f}   ${rmse:>9,.0f} {overf:>10.4f}")

    results["Stacking Ensemble"] = dict(
        pipeline=stack,
        train_r2=tr_r2, val_r2=va_r2, test_r2=te_r2,
        test_mae=mae, test_rmse=rmse, overfit=overf,
        y_pred=y_pred_s, y_actual=y_test_raw,
        y_pred_train=y_pred_s_tr, y_actual_train=y_train_raw,
    )

    # ── Final summary ──────────────────────────────────────────────
    print(f"\n  {'='*95}")
    print(f"  {'Model':<22} {'Train R2':>9} {'Val R2':>9} {'Test R2':>9} "
          f"{'Test MAE':>12} {'Test RMSE':>12} {'Overfit':>10}")
    print(f"  {'-'*95}")

    best_name = max(results, key=lambda n: results[n]["test_r2"])
    for name, r in results.items():
        marker = " 🏆" if name == best_name else ""
        print(f"  {name:<22} {r['train_r2']:>9.4f} {r.get('val_r2', 0):>9.4f} "
              f"{r['test_r2']:>9.4f}   ${r['test_mae']:>9,.0f}   "
              f"${r['test_rmse']:>9,.0f} {r['overfit']:>10.4f}{marker}")

    best = results[best_name]
    print(f"\n  🏆 Overall Best  : {best_name}")
    print(f"      Train R²     : {best['train_r2']:.4f}")
    print(f"      Val R²       : {best.get('val_r2', 0):.4f}")
    print(f"      Test R²      : {best['test_r2']:.4f}")
    print(f"      Test MAE     : ${best['test_mae']:,.0f}")
    print(f"      Test RMSE    : ${best['test_rmse']:,.0f}")

    # ── Charts ─────────────────────────────────────────────────────
    names  = list(results.keys())
    colors = ["#6366f1","#8b5cf6","#10b981","#f472b6","#fbbf24",
              "#38bdf8","#ef4444","#14b8a6","#f97316","#a3e635","#fb7185"]

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Model Comparison — 2025 Survey (Pipeline v4.1)", fontsize=14, fontweight="bold")
    fig.patch.set_facecolor("#f8faff")
    for ax, (key, title, fmt) in zip(axes, [
        ("test_r2",   "Test R²\n(higher = better)",        "{:.3f}"),
        ("test_mae",  "Test MAE (USD)\n(lower = better)",  "${:,.0f}"),
        ("test_rmse", "Test RMSE (USD)\n(lower = better)", "${:,.0f}"),
    ]):
        vals = [results[n][key] for n in names]
        hi   = ["#1e293b" if n == best_name else colors[i % len(colors)]
                for i, n in enumerate(names)]
        bars = ax.bar(names, vals, color=hi, edgecolor="white", linewidth=2, width=0.55)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_facecolor("#f0f4ff")
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", rotation=35, labelsize=7)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()*1.015,
                    fmt.format(v), ha="center", fontsize=7, fontweight="bold")
    plt.tight_layout()
    plt.savefig("model_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n  📊 Saved: model_comparison.png")

    fig_tt, ax_tt = plt.subplots(figsize=(16, 6))
    fig_tt.patch.set_facecolor("#f8faff")
    x_pos = np.arange(len(names)); width = 0.35
    bars_tr = ax_tt.bar(x_pos - width/2, [results[n]["train_r2"] for n in names],
                        width, label="Train R²", color="#6366f1", alpha=0.8)
    bars_te = ax_tt.bar(x_pos + width/2, [results[n]["test_r2"]  for n in names],
                        width, label="Test R²",  color="#10b981", alpha=0.8)
    ax_tt.set_xlabel("Model"); ax_tt.set_ylabel("R² Score")
    ax_tt.set_title("Train vs Test R² — All Models (v4.1)", fontweight="bold")
    ax_tt.set_xticks(x_pos)
    ax_tt.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    ax_tt.legend(); ax_tt.set_facecolor("#f0f4ff")
    ax_tt.spines["top"].set_visible(False); ax_tt.spines["right"].set_visible(False)
    for bar in bars_tr:
        ax_tt.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                   f"{bar.get_height():.3f}", ha="center", fontsize=7)
    for bar in bars_te:
        ax_tt.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                   f"{bar.get_height():.3f}", ha="center", fontsize=7)
    plt.tight_layout()
    plt.savefig("train_vs_test_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  📊 Saved: train_vs_test_comparison.png")

    y_pred_best = best["y_pred"]; y_actual = best["y_actual"]
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
    fig2.patch.set_facecolor("#f8faff")
    axes2[0].scatter(y_actual, y_pred_best, alpha=0.25, color="#6366f1", s=12)
    lim = [min(y_actual.min(), y_pred_best.min()), max(y_actual.max(), y_pred_best.max())]
    axes2[0].plot(lim, lim, "r--", linewidth=1.5, label="Perfect fit")
    axes2[0].set_xlabel("Actual Salary (USD)"); axes2[0].set_ylabel("Predicted Salary (USD)")
    axes2[0].set_title(f"Actual vs Predicted — {best_name}", fontweight="bold")
    axes2[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    axes2[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    axes2[0].set_facecolor("#f0f4ff"); axes2[0].spines["top"].set_visible(False)
    axes2[0].spines["right"].set_visible(False); axes2[0].legend()
    residuals = y_actual - y_pred_best
    axes2[1].hist(residuals, bins=60, color="#6366f1", alpha=0.75, edgecolor="white")
    axes2[1].axvline(0, color="red", linestyle="--", linewidth=1.5)
    axes2[1].set_xlabel("Residual (Actual − Predicted, USD)"); axes2[1].set_ylabel("Count")
    axes2[1].set_title(f"Residuals — {best_name}", fontweight="bold")
    axes2[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    axes2[1].set_facecolor("#f0f4ff"); axes2[1].spines["top"].set_visible(False)
    axes2[1].spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig("actual_vs_predicted.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  📊 Saved: actual_vs_predicted.png")

    # ── Save model ─────────────────────────────────────────────────
    VALID_CATEGORIES = {
        "Country":       sorted(df["Country"].unique().tolist()),
        "EdLevel":       sorted(df["EdLevel"].dropna().unique().tolist()),
        "Employment":    sorted(df["Employment"].unique().tolist()),
        "DevType":       sorted(df["DevType"].unique().tolist()),
        "TopFrameworks": TOP_FRAMEWORKS,
        "TopLanguages":  TOP_LANGUAGES,
        "RemoteWork":    sorted(df["RemoteWork"].unique().tolist()),
        "OrgSize":       sorted(df["OrgSize"].unique().tolist()),
        "Age":           sorted(df["Age"].unique().tolist()),
        "Industry":      sorted(df["Industry"].unique().tolist()),
    }

    save_dict = {
        "best_model_name":          best_name,
        "test_r2":                  best["test_r2"],
        "test_mae":                 best["test_mae"],
        "test_rmse":                best["test_rmse"],
        "train_r2":                 best["train_r2"],
        "val_r2":                   best.get("val_r2", 0),
        "quantile_transformer":     qt,
        "valid_categories":         VALID_CATEGORIES,
        "numeric_features":         NUMERIC_FEATURES,
        "categorical_features":     CATEGORICAL_FEATURES,
        "framework_cols":           FRAMEWORK_COLS,
        "language_cols":            LANGUAGE_COLS,
        "top_frameworks":           TOP_FRAMEWORKS,
        "top_languages":            TOP_LANGUAGES,
        "devtype_salary_rank":      DEVTYPE_SALARY_RANK,
        "education_salary_rank":    EDUCATION_SALARY_RANK,
        "country_salary_rank":      COUNTRY_SALARY_RANK,
        "orgsize_rank":             ORGSIZE_RANK,
        "remote_rank":              REMOTE_RANK,
        "age_rank":                 AGE_RANK,
        "ppp_factors":              PPP_FACTORS,
        "lang_seniority":           LANG_SENIORITY,
        "country_mean_salary":      country_mean_train,
        "country_std_salary":       country_std_train,
        "country_ppp_mean":         country_ppp_mean_train,
        "country_devtype_median":   country_devtype_median,
        "devtype_mean_salary":      devtype_mean_train,
        "edu_mean_salary":          edu_mean_train,
        "lang_salary_map":          lang_salary_map,
        "global_mean_salary":       global_mean,
        "global_std_salary":        global_std,
        "all_results": {
            n: {"train_r2": r["train_r2"], "val_r2": r.get("val_r2", 0),
                "test_r2": r["test_r2"], "test_mae": r["test_mae"],
                "test_rmse": r["test_rmse"]}
            for n, r in results.items()
        },
    }

    if best["pipeline"] is not None:
        save_dict["pipeline"] = best["pipeline"]
    else:
        save_dict["pipeline"]              = None
        save_dict["catboost_model"]        = best.get("catboost_model")
        save_dict["catboost_cat_features"] = best.get("catboost_cat_features")
        save_dict["catboost_all_features"] = best.get("catboost_all_features")

    joblib.dump(save_dict, MODEL_PATH)
    print(f"\n  💾 Saved: {MODEL_PATH}")

    print("\n" + "=" * 65)
    print(f"  DONE — Best: {best_name}")
    print(f"         R²:  {best['test_r2']:.4f}  |  MAE: ${best['test_mae']:,.0f}")
    print("=" * 65 + "\n")

    missing = []
    if not OPTUNA_AVAILABLE:   missing.append("optuna")
    if not CATBOOST_AVAILABLE: missing.append("catboost")
    if missing:
        print(f"  💡 To unlock all improvements, install: pip install {' '.join(missing)}")
        print("     Then re-run train_models.py\n")


if __name__ == "__main__":
    main()
