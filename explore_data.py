"""Quick data exploration — saves results to explore_output.txt"""
import pandas as pd
import numpy as np
import sys

sys.stdout = open("explore_output.txt", "w", encoding="utf-8")

COLS = [
    'ConvertedCompYearly','WorkExp','EdLevel','Employment','Country','DevType',
    'Industry','OrgSize','RemoteWork','YearsCode','LearnCode','Age',
    'LanguageHaveWorkedWith','WebframeHaveWorkedWith'
]

df = pd.read_csv('data/survey_results_public.csv', usecols=COLS)
print(f"Total rows: {len(df)}")
print(f"\n=== ConvertedCompYearly ===")
print(f"Non-null: {df['ConvertedCompYearly'].notna().sum()}")
print(df['ConvertedCompYearly'].describe())

# Filter to only rows with salary
dfs = df[df['ConvertedCompYearly'].notna()].copy()
print(f"\nRows with salary: {len(dfs)}")

for col in COLS:
    if col == 'ConvertedCompYearly':
        continue
    print(f"\n=== {col} ===")
    print(f"Nulls: {dfs[col].isna().sum()} / {len(dfs)} ({dfs[col].isna().mean()*100:.1f}%)")
    if dfs[col].dtype == 'object':
        print(dfs[col].value_counts().head(15))
    else:
        print(dfs[col].describe())

# Salary distribution
print("\n=== Salary percentiles ===")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  {p}th: ${dfs['ConvertedCompYearly'].quantile(p/100):,.0f}")

# Check duplicates
print(f"\n=== Duplicates ===")
print(f"Total duplicates: {dfs.duplicated().sum()}")

print("\nDONE")
sys.stdout.close()
