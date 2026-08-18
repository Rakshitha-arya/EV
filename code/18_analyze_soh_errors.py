import os
import pandas as pd

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FILE = os.path.join(
    BASE_DIR,
    "processed",
    "NASA_SOH_predictions.csv"
)

df = pd.read_csv(FILE)

print("=" * 65)
print("NASA SOH MODEL - ERROR ANALYSIS")
print("=" * 65)

# --------------------------------------------------
# OVERALL
# --------------------------------------------------

print("\nOverall results:")
print(f"Rows: {len(df)}")

print(
    f"Mean absolute error: "
    f"{df['absolute_error_percent'].mean():.4f}%"
)

print(
    f"Maximum absolute error: "
    f"{df['absolute_error_percent'].max():.4f}%"
)

# --------------------------------------------------
# BATTERY-WISE ERROR
# --------------------------------------------------

battery_error = (
    df.groupby("battery_id")
    .agg(
        cycles=("cycle_number", "count"),
        actual_mean=("SOH_percent", "mean"),
        predicted_mean=("predicted_SOH_percent", "mean"),
        MAE=("absolute_error_percent", "mean"),
        max_error=("absolute_error_percent", "max"),
        mean_error=("error_percent", "mean")
    )
    .reset_index()
)

print("\n" + "=" * 65)
print("BATTERY-WISE PERFORMANCE")
print("=" * 65)

print(
    battery_error.to_string(index=False)
)

# --------------------------------------------------
# WORST PREDICTIONS
# --------------------------------------------------

worst = (
    df.sort_values(
        "absolute_error_percent",
        ascending=False
    )
    .head(15)
)

print("\n" + "=" * 65)
print("15 WORST PREDICTIONS")
print("=" * 65)

print(
    worst[
        [
            "battery_id",
            "cycle_number",
            "SOH_percent",
            "predicted_SOH_percent",
            "error_percent",
            "absolute_error_percent"
        ]
    ].to_string(index=False)
)

# --------------------------------------------------
# ERROR BY SOH RANGE
# --------------------------------------------------

df["SOH_range"] = pd.cut(
    df["SOH_percent"],
    bins=[0, 70, 80, 90, 100, 110, 150],
    labels=[
        "<70%",
        "70-80%",
        "80-90%",
        "90-100%",
        "100-110%",
        ">110%"
    ]
)

range_error = (
    df.groupby("SOH_range", observed=False)
    .agg(
        samples=("SOH_percent", "count"),
        MAE=("absolute_error_percent", "mean")
    )
    .reset_index()
)

print("\n" + "=" * 65)
print("ERROR BY SOH RANGE")
print("=" * 65)

print(
    range_error.to_string(index=False)
)

# --------------------------------------------------
# BIAS
# --------------------------------------------------

print("\n" + "=" * 65)
print("MODEL BIAS")
print("=" * 65)

mean_bias = df["error_percent"].mean()

print(
    f"\nMean prediction error: {mean_bias:.4f}%"
)

if mean_bias < 0:
    print(
        "Model tendency: UNDER-PREDICTION"
    )
elif mean_bias > 0:
    print(
        "Model tendency: OVER-PREDICTION"
    )
else:
    print(
        "Model tendency: NO SIGNIFICANT BIAS"
    )

print("\n" + "=" * 65)
print("ERROR ANALYSIS COMPLETE")
print("=" * 65)