from typing import Literal
import json
import datetime
import os
import logging
import logging.config

import pandas as pd
import featuretools as ft
from featuretools.primitives import AggregationPrimitive, TransformPrimitive
from featuretools.feature_base import IdentityFeature
from fastapi import FastAPI, Query
from pydantic import BaseModel, create_model
from pydantic.main import ModelMetaclass

# Logging set up
with open('logconfig.json') as f:
    logconfig = json.load(f)
logging.config.dictConfig(logconfig)
logging.raiseExceptions = False
logger = logging.getLogger(__name__)
logger.info("Starting new session")

# Constants related to the data and its schema
DATA_PATH = "/data/cvas_data.json"
CUSTOMER_ID_COL = "customer_ID"
LOAN_ID_COL = "loan_ID"  # This gets created by the script.
LOAN_DATE_COL = "loan_date"
DATE_COLS = [LOAN_DATE_COL]
DATE_COLS_FORMAT = "%d/%m/%Y"
NUMERIC_COLS = ["amount", "fee", "annual_income", "loan_status"]
CATEGORICAL_COLS = ["loan_status", "term"]
CUSTOMER_COLS = ["annual_income"]

# Default parameters for feature engineering
AGG_PRIMITIVES_DEFAULT = [
    "max",
    "min",
    "mean",
    "count",
    "percent_true",
    "num_unique",
    "mode",
]
TRANS_PRIMITIVES_DEFAULT = [
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


def model_from_dataframe(df: pd.DataFrame) -> ModelMetaclass:
    """Dynamically creates a pydantic model from a pandas.DataFrame"""
    record = df.iloc[0, :].to_dict()
    record_types = {name: (type(v), ...) for name, v in record.items()}
    model = create_model("EngineeredFeatures", **record_types)
    return model


def load_raw_features(path: str | os.PathLike) -> pd.DataFrame:
    """Loads the json file into a pandas dataframe"""
    with open(path) as f:
        d = json.load(f)
        records = [loan for dd in d["data"] for loan in dd["loans"]]
        df = pd.DataFrame.from_records(records)

    df[DATE_COLS] = df[DATE_COLS].apply(pd.to_datetime, format=DATE_COLS_FORMAT)
    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric)
    df[CATEGORICAL_COLS] = df[CATEGORICAL_COLS].apply(pd.Categorical)

    return df


def engineer_features(
    df: pd.DataFrame, transforms: list[str | TransformPrimitive], aggregations: list[str | AggregationPrimitive]
) -> tuple[pd.DataFrame, IdentityFeature]:
    """Engineers features for each customer with the specified transforms and aggregations on the loans"""

    customers = df[[CUSTOMER_ID_COL, *CUSTOMER_COLS]].drop_duplicates(subset=[CUSTOMER_ID_COL])
    loans = df.drop(columns=CUSTOMER_COLS).reset_index(names=LOAN_ID_COL)

    es = ft.EntitySet(
        id="customer_loans",
        dataframes={
            "customers": (customers, CUSTOMER_ID_COL),
            "loans": (loans, LOAN_ID_COL, LOAN_DATE_COL)
        },
        relationships=[("customers", CUSTOMER_ID_COL, "loans", CUSTOMER_ID_COL)]
    )

    customer_features: pd.DataFrame
    customer_defs: IdentityFeature
    customer_features, customer_defs = ft.dfs(
        entityset=es,
        target_dataframe_name="customers",
        trans_primitives=transforms,
        agg_primitives=aggregations,
        max_depth=2,
    )

    return customer_features.reset_index(), customer_defs


logger.info("Loading the data from the json file")
df_raw = load_raw_features(DATA_PATH)

app = FastAPI()
logger.info("Initialized the API")


@app.get("/")
async def root():
    return {"message": "Welcome to the Feature Engineering API"}


@app.get("/features/raw", response_model=list[RawFeatures], tags=["features"])
async def read_raw_features(customer_id: list[str] | None = Query(default=None)):
    df = df_raw
    if customer_id is not None:
        df = df.loc[df[CUSTOMER_ID_COL].isin(customer_id)]

    df = df.astype(object).where(df.notna(), None)  # for JSON compatibility
    records = df.to_dict("records")

    return records


@app.post("/features/engineer", tags=["features"])
def fetch_engineer_features(
    transforms: list[str] = TRANS_PRIMITIVES_DEFAULT,
    aggregations: list[str] = AGG_PRIMITIVES_DEFAULT,
    customer_id: list[str] | None = Query(default=None)
):
    df = df_raw
    if customer_id is not None:
        df = df.loc[df[CUSTOMER_ID_COL].isin(customer_id)]

    df_eng, _ = engineer_features(df, aggregations=aggregations, transforms=transforms)

    df_eng = df_eng.astype(object).where(df_eng.notna(), None)  # for JSON compatibility
    records = df_eng.to_dict("records")

    logger.info(
        "Engineered customer features with "
        "customer_id=%s, transforms=%s, aggregations=%s", customer_id, aggregations, transforms
    )

    return records


@app.get("/status", tags=["checks"])
async def check_status():
    # TODO: ?
    return {"status": "UP"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
