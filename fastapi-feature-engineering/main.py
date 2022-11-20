from typing import Any, Iterable, Literal
import json
import datetime
import os

import pandas as pd
import featuretools as ft
from featuretools.feature_base import IdentityFeature
from fastapi import FastAPI, Query, Path
from pydantic import BaseModel, create_model
from pydantic.main import ModelMetaclass


CUSTOMER_ID_COL = "customer_ID"
LOAN_ID_COL = "loan_ID"  # This gets created by the script.
LOAN_DATE_COL = "loan_date"
DATETIME_COLS = [LOAN_DATE_COL]
NUMERIC_COLS = ["amount", "fee", "annual_income"]
CATEGORICAL_COLS = ["loan_status", "term"]
CUSTOMER_COLS = ["annual_income"]
AGG_PRIMITIVES=[
    "max",
    "min",
    "mean",
    "count",
    "percent_true",
    "num_unique",
    "mode",
]
TRANS_PRIMITIVES=[
    "year",
    "month",
    "day",
    "day_of_year",
    "distance_to_holiday",
    "is_month_end",
    "is_month_start",
    "time_since_previous",
]


class RawFeatures(BaseModel):
    customer_ID: str
    loan_date: datetime.date
    amount: int
    fee: int
    loan_status: Literal[0, 1]
    term: Literal["short", "long"]
    annual_income: int


def load_raw_features(path: str | os.PathLike) -> pd.DataFrame:
    """Loads the json file into a pandas dataframe"""
    with open(path) as f:
        d = json.load(f)
        records = [loan for dd in d["data"] for loan in dd["loans"]]
        df = pd.DataFrame.from_records(records)

    df[DATETIME_COLS] = df[DATETIME_COLS].apply(pd.to_datetime, format="%d/%m/%Y")
    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric)
    df[CATEGORICAL_COLS] = df[CATEGORICAL_COLS].apply(pd.Categorical)

    return df


def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, IdentityFeature]:
    customers = df[[CUSTOMER_ID_COL, *CUSTOMER_COLS]].drop_duplicates(subset=[CUSTOMER_ID_COL])
    loans = df.drop(columns=CUSTOMER_COLS).reset_index(names=LOAN_ID_COL)
    es = ft.EntitySet(
        id="customer_loans",
        dataframes={
            "customers": (customers, CUSTOMER_ID_COL),
            "loans": (loans, LOAN_ID_COL, LOAN_DATE_COL)
        },
        relationships=[
            ("customers", CUSTOMER_ID_COL, "loans", CUSTOMER_ID_COL)
        ]
    )

    # Features for each customer
    customer_features: pd.DataFrame
    customer_defs: IdentityFeature
    customer_features, customer_defs = ft.dfs(
        entityset=es,
        target_dataframe_name="customers",
        agg_primitives=AGG_PRIMITIVES,
        trans_primitives=TRANS_PRIMITIVES,
        max_depth=2,
    )
    
    return customer_features.reset_index(), customer_defs


def model_from_dataframe(df: pd.DataFrame) -> ModelMetaclass:
    """Dynamically creates a pydantic model"""
    record = df_eng.iloc[0, :].to_dict()
    record_types = {name: (type(v), ...) for name, v in record.items()}
    model = create_model("EngineeredFeatures", **record_types)
    return model


def fetch_records(df: pd.DataFrame, vals: Iterable | None = None, col: str = CUSTOMER_ID_COL) -> dict:
    if vals is not None:
        df = df.loc[df[col].isin(vals)]
    return df.to_dict("records")


df_raw = load_raw_features("cvas_data.json")

df_eng, _ = engineer_features(df_raw)
EngineeredFeatures = model_from_dataframe(df_eng)

app = FastAPI()

# TODO:
#   - Get original data. Optional parameter: list[user_ID]  (UUID)
#   - Post aggs and trans to get different eng data each time new data.



@app.get("/")
def root():
    return {"message": "Welcome to the Feature Engineering API"}


# @app.get("/features/{features_type}")
# def get_features(
#     features_type: Literal["raw", "engineered"] = Path(), 
#     customer_id: list[str] | None = Query(default=None)
# ):
#     data = df_raw if features_type == "raw" else df_eng
#     if customer_id is not None:
#         data = data.loc[data[CUSTOMER_ID_COL].isin(customer_id)]
#     return data.to_dict("records")


@app.get("/features/raw", response_model=RawFeatures, tags=['features'])
def get_features(
    customer_id: list[str] | None = Query(default=None)
):
    records = fetch_records(df_raw, customer_id)
    return records


@app.get("/features/engineered", response_model=EngineeredFeatures, tags=['features'])
def get_features(
    customer_id: list[str] | None = Query(default=None)
):
    records = fetch_records(df_eng, customer_id)
    return records


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
