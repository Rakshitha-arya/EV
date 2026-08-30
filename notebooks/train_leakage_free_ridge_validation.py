"""Train one isolated, leakage-free Ridge SOH validation experiment."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_DIR / "processed" / "soh" / "combined_soh_dataset.csv"
OUTPUT_DIR = (
    PROJECT_DIR / "processed" / "soh" / "models" / "leakage_free_validation"
)

TARGET_COLUMN = "SOH_percent"
GROUP_COLUMNS = ["Source_Dataset", "Battery_ID"]
RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "Cycle",
    "Capacity_Ah",
    "Voltage_Min_V",
    "Voltage_Max_V",
    "Voltage_Mean_V",
    "Voltage_Final_V",
    "Current_Min_A",
    "Current_Max_A",
    "Current_Mean_A",
    "Temperature_Min_C",
    "Temperature_Max_C",
    "Temperature_Mean_C",
    "Temperature_Final_C",
    "Discharge_Time_s",
    "Voltage_Range_V",
    "Current_Range_A",
    "Temperature_Range_C",
    "Source_Dataset",
]


def create_split(dataframe: pd.DataFrame):
    groups = dataframe[GROUP_COLUMNS].drop_duplicates().reset_index(drop=True)
    shuffled_indices = np.random.RandomState(RANDOM_STATE).permutation(len(groups))
    test_group_count = max(1, int(round(len(groups) * 0.25)))

    test_groups = groups.iloc[shuffled_indices[:test_group_count]].copy()
    train_groups = groups.iloc[shuffled_indices[test_group_count:]].copy()

    train_keys = set(map(tuple, train_groups[GROUP_COLUMNS].to_numpy()))
    test_keys = set(map(tuple, test_groups[GROUP_COLUMNS].to_numpy()))
    overlap = train_keys.intersection(test_keys)
    if overlap:
        raise RuntimeError(f"Group overlap detected: {overlap}")

    keys = list(zip(dataframe[GROUP_COLUMNS[0]], dataframe[GROUP_COLUMNS[1]]))
    train_dataframe = dataframe.loc[[key in train_keys for key in keys]].copy()
    test_dataframe = dataframe.loc[[key in test_keys for key in keys]].copy()

    return train_dataframe, test_dataframe, train_groups, test_groups


def main():
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise RuntimeError(
            "Validation output directory is not empty; refusing to overwrite it."
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataframe = pd.read_csv(DATASET_PATH)
    numeric_columns = [
        "Cycle",
        "Capacity_Ah",
        "Voltage_Min_V",
        "Voltage_Max_V",
        "Voltage_Mean_V",
        "Voltage_Final_V",
        "Current_Min_A",
        "Current_Max_A",
        "Current_Mean_A",
        "Temperature_Min_C",
        "Temperature_Max_C",
        "Temperature_Mean_C",
        "Temperature_Final_C",
        "Discharge_Time_s",
        TARGET_COLUMN,
    ]
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe = dataframe.loc[
        dataframe[TARGET_COLUMN].notna()
        & dataframe[TARGET_COLUMN].between(0, 100)
        & dataframe["Capacity_Ah"].gt(0)
        & dataframe["Cycle"].ge(0)
        & dataframe["Battery_ID"].notna()
    ].copy()
    dataframe = dataframe.drop_duplicates().drop_duplicates(
        subset=GROUP_COLUMNS + ["Cycle"]
    )

    dataframe["Voltage_Range_V"] = (
        dataframe["Voltage_Max_V"] - dataframe["Voltage_Min_V"]
    )
    dataframe["Current_Range_A"] = (
        dataframe["Current_Max_A"] - dataframe["Current_Min_A"]
    )
    dataframe["Temperature_Range_C"] = (
        dataframe["Temperature_Max_C"] - dataframe["Temperature_Min_C"]
    )

    train_dataframe, test_dataframe, train_groups, test_groups = create_split(dataframe)
    if len(train_dataframe) != 1010 or len(test_dataframe) != 345:
        raise RuntimeError("Unexpected established train/test row counts.")

    numeric_features = FEATURE_COLUMNS[:-1]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                ["Source_Dataset"],
            ),
        ]
    )
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", Ridge(alpha=1.0)),
    ])

    pipeline.fit(train_dataframe[FEATURE_COLUMNS], train_dataframe[TARGET_COLUMN])
    predictions = np.clip(pipeline.predict(test_dataframe[FEATURE_COLUMNS]), 0, 100)
    target = test_dataframe[TARGET_COLUMN]
    metrics = {
        "MAE": float(mean_absolute_error(target, predictions)),
        "RMSE": float(np.sqrt(mean_squared_error(target, predictions))),
        "R2": float(r2_score(target, predictions)),
        "MAPE": float(np.mean(np.abs((target - predictions) / target)) * 100.0),
    }

    leakage_checks = {
        "group_overlap": False,
        "duplicate_dataset_battery_cycle_records": int(
            dataframe.duplicated(subset=GROUP_COLUMNS + ["Cycle"]).sum()
        ),
        "feature_count": len(FEATURE_COLUMNS),
        "preprocessing_in_pipeline": True,
        "preprocessor_fit_on_training_data_only": True,
        "fixed_single_model_configuration": True,
        "test_set_used_for_model_selection": False,
    }
    metadata = {
        "experiment": "leakage-free fixed Ridge validation",
        "target_column": TARGET_COLUMN,
        "grouping_key": GROUP_COLUMNS,
        "random_state": RANDOM_STATE,
        "feature_columns": FEATURE_COLUMNS,
        "metrics": metrics,
        "training_rows": len(train_dataframe),
        "testing_rows": len(test_dataframe),
        "training_groups": train_groups.sort_values(GROUP_COLUMNS).to_dict("records"),
        "testing_groups": test_groups.sort_values(GROUP_COLUMNS).to_dict("records"),
        "leakage_checks": leakage_checks,
    }

    with (OUTPUT_DIR / "ridge_pipeline.pkl").open("wb") as file:
        pickle.dump(pipeline, file)
    (OUTPUT_DIR / "feature_columns.json").write_text(
        json.dumps({"feature_columns": FEATURE_COLUMNS}, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
