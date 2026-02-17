import os

import numpy as np
import pandas as pd

# Scikit-learn utilities for preprocessing and modeling
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Regression models to compare
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

# For saving the trained model
import joblib


# Path to the raw survey dataset
DATA_PATH = os.path.join("data", "survey_results_public.csv")

#the target variable
TARGET_COL = "Salary"


def shorten_categories(categories, cutoff):
    """
    Reduce high-cardinality categorical features.
    Categories appearing fewer than `cutoff` times are grouped as 'other'.
    """
    categorical_map = {}
    for i in range(len(categories)):
        if categories.values[i] >= cutoff:
            categorical_map[categories.index[i]] = categories.index[i]
        else:
            categorical_map[categories.index[i]] = "other"
    return categorical_map


def clean_experience(x):
    """
    Convert experience from string labels to numeric values.
    """
    if x == "More than 50 years":
        return 50
    if x == "Less than 1 year":
        return 0.5
    try:
        return float(x)
    except Exception:
        return np.nan


def clean_education(x):
    """
    Standardize education levels into fewer, consistent categories.
    """
    if "Bachelor’s degree" in x:
        return "Bachelor’s degree"
    if "Master’s degree" in x:
        return "Master’s degree"
    if "Professional degree" in x or "Other doctoral" in x:
        return "Post grad"
    return "less than a Bachelor’s"


def clean_employment(x):
    """
    Keep only full-time and part-time employment.
    All other employment types are removed later by dropping NaNs.
    """
    if x == "Employed full-time":
        return "full-time"
    if x == "Employed part-time":
        return "part-time"
    return np.nan


def clean_undergrad_major(x):
    """
    Group free-text undergraduate majors into broader, meaningful buckets.
    """
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
    elif "health science" in x:
        return "Health Sciences"
    else:
        return "Other"


def load_and_clean_data():
    """
    Load the dataset, clean and preprocess raw survey responses,
    and return a modeling-ready DataFrame.
    """
    print(f"Loading data from {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)

    # Selecting only columns that are used by the model and UI
    df = df[
        [
            "Country",
            "EdLevel",
            "YearsCodePro",
            "Employment",
            "WebframeWorkedWith",
            "UndergradMajor",
            "ConvertedComp",
        ]
    ]

    # Renaming columns for clarity
    df = df.rename(
        columns={
            "ConvertedComp": "Salary",
            "YearsCodePro": "Experience",
        }
    )

    # Inspecting raw data
    print("\n=== Raw Data Info (selected columns) ===")
    print(df.info())
    print("\n=== Target description (Salary) ===")
    print(df["Salary"].describe())

    # Removing rows with missing target or features
    df = df.dropna(subset=["Salary"])
    df = df.dropna()

    # Apply cleaning transformations
    df["Experience"] = df["Experience"].apply(clean_experience)
    df["Employment"] = df["Employment"].apply(clean_employment)

    # Drop rows that are not full-time or part-time
    df = df.dropna(subset=["Employment"])

    # Reduce rare categories
    country_map = shorten_categories(df["Country"].value_counts(), 400)
    df["Country"] = df["Country"].map(country_map)

    web_map = shorten_categories(df["WebframeWorkedWith"].value_counts(), 400)
    df["WebframeWorkedWith"] = df["WebframeWorkedWith"].map(web_map)

    # Clean remaining categorical fields
    df["UndergradMajor"] = df["UndergradMajor"].apply(clean_undergrad_major)
    df["EdLevel"] = df["EdLevel"].apply(clean_education)

    # Remove extreme salary outliers
    df = df[(df["Salary"] >= 10_000) & (df["Salary"] <= 250_000)]

    print("\n=== After Cleaning ===")
    print(df.describe(include="all").T.head(30))
    print(f"\nRemaining rows after cleaning: {len(df)}")

    return df


def build_preprocessor(df):
    """
    Build preprocessing pipeline for numeric and categorical features.
    """
    numeric_features = ["Experience"]
    categorical_features = [
        "Country",
        "EdLevel",
        "Employment",
        "WebframeWorkedWith",
        "UndergradMajor",
    ]

    # Applying scaling to numeric data and one-hot encoding to categorical data
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    X = df[numeric_features + categorical_features]
    y = df[TARGET_COL]

    return X, y, preprocessor


def evaluate_models(X, y, preprocessor):
    """
    Train multiple regression models, evaluate them,
    and select the best-performing one.
    """
    # Splitting the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Models to compare
    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTreeRegressor": DecisionTreeRegressor(
            random_state=42, max_depth=10, min_samples_leaf=5
        ),
        "RandomForestRegressor": RandomForestRegressor(
            random_state=42, n_estimators=200, max_depth=15, n_jobs=-1
        ),
        "XGBRegressor": XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            n_jobs=-1,
            tree_method="hist",
        ),
    }

    results = {}

    print("\n=== Training and Evaluation (80% train / 20% test) ===")

    for name, model in models.items():
        # Combine preprocessing and model into a single pipeline
        pipe = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )

        print(f"\n--- {name} ---")
        pipe.fit(X_train, y_train)

        # Making predictions
        y_train_pred = pipe.predict(X_train)
        y_test_pred = pipe.predict(X_test)

        # Evaluation metrics
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)

        results[name] = {
            "pipeline": pipe,
            "train_r2": train_r2,
            "test_r2": test_r2,
            "train_mae": train_mae,
            "test_mae": test_mae,
            "train_mse": train_mse,
            "test_mse": test_mse,
        }

    # Custom scoring to balance performance and overfitting
    def score_for_selection(metrics):
        gap = max(0.0, metrics["train_r2"] - metrics["test_r2"])
        return (
            metrics["test_r2"]
            - 1e-6 * metrics["test_mae"]
            - 1e-9 * metrics["test_mse"]
            - 0.1 * gap
        )

    best_name, best_metrics = max(
        results.items(), key=lambda kv: score_for_selection(kv[1])
    )

    return best_name, best_metrics, X_train, X_test, y_train, y_test


def main():
    """
    End-to-end training pipeline:
    load data → clean → train models → save best model.
    """
    df = load_and_clean_data()
    X, y, preprocessor = build_preprocessor(df)
    best_name, best_metrics, _, _, _, _ = evaluate_models(X, y, preprocessor)

    best_pipeline = best_metrics["pipeline"]

    # Persist the trained pipeline for use in the Streamlit app
    model_path = "best_salary_model.pkl"
    joblib.dump(best_pipeline, model_path)
    print(f"\nBest model pipeline saved to: {model_path}")


if __name__ == "__main__":
    main()
