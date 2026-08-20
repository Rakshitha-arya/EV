import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_health_features.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_feature_importance.csv"
)

print("=" * 65)
print("NASA SOH - HEALTH FEATURE ANALYSIS")
print("=" * 65)

df = pd.read_csv(INPUT_FILE)

# --------------------------------------------------
# IMPORTANT:
# Do NOT use SOH itself or SOH-derived features
# --------------------------------------------------

exclude = [
    "battery_id",
    "SOH_percent",
    "SOH_rolling_mean_5",
    "reference_capacity_Ah"
]

features = [
    c for c in df.columns
    if c not in exclude
]

X = df[features].copy()
y = df["SOH_percent"].copy()

# Make sure everything is numeric
X = X.apply(pd.to_numeric, errors="coerce")

# Remove invalid values
valid = X.notnull().all(axis=1) & y.notnull()

X = X.loc[valid]
y = y.loc[valid]

print("\nRows used:", len(X))
print("Number of features:", len(features))

print("\nFeatures:")
for f in features:
    print("  -", f)

# --------------------------------------------------
# Correlation with SOH
# --------------------------------------------------

correlation = X.copy()
correlation["SOH_percent"] = y

corr = (
    correlation.corr(numeric_only=True)["SOH_percent"]
    .drop("SOH_percent")
    .sort_values(key=abs, ascending=False)
)

print("\n" + "=" * 65)
print("FEATURE CORRELATION WITH SOH")
print("=" * 65)

for feature, value in corr.items():
    print(f"{feature:35s} {value: .4f}")

# --------------------------------------------------
# Random Forest feature importance
# --------------------------------------------------

print("\n" + "=" * 65)
print("RANDOM FOREST FEATURE IMPORTANCE")
print("=" * 65)

model = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)

model.fit(X, y)

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
).reset_index(drop=True)

for i, row in importance.iterrows():
    print(
        f"{i+1:2d}. "
        f"{row['feature']:35s} "
        f"{row['importance']:.6f}"
    )

# --------------------------------------------------
# Permutation importance
# --------------------------------------------------

print("\n" + "=" * 65)
print("PERMUTATION IMPORTANCE")
print("=" * 65)

perm = permutation_importance(
    model,
    X,
    y,
    n_repeats=10,
    random_state=42,
    n_jobs=-1
)

perm_df = pd.DataFrame({
    "feature": features,
    "permutation_importance_mean":
        perm.importances_mean,
    "permutation_importance_std":
        perm.importances_std
})

perm_df = perm_df.sort_values(
    "permutation_importance_mean",
    ascending=False
).reset_index(drop=True)

for i, row in perm_df.iterrows():
    print(
        f"{i+1:2d}. "
        f"{row['feature']:35s} "
        f"{row['permutation_importance_mean']:.6f}"
    )

# --------------------------------------------------
# Combine results
# --------------------------------------------------

result = importance.merge(
    perm_df,
    on="feature"
)

result["correlation_with_SOH"] = [
    corr.get(feature, np.nan)
    for feature in result["feature"]
]

result.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved feature analysis to:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("FEATURE ANALYSIS COMPLETE")
print("=" * 65)