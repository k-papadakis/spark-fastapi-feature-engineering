from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

IDS = {"296", "1090"}
NON_IDS = {"1010101010"}

AGGREGATIONS = ["min", "mean"]
TRANSFORMS = ["day_of_year", "distance_to_holiday", "time_since_previous"]


def test_health():
    response = client.get("/status")
    assert response.json()["status"] == "UP"


def test_raw_data():
    response = client.get("/features/raw", params={"customer_id": list(IDS | NON_IDS)})
    assert {record['customer_ID'] for record in response.json()} == IDS


def test_feat_eng():
    response = client.post(
        "/features/engineer",
        json={
            "transforms": TRANSFORMS,
            "aggregations": AGGREGATIONS
        },
        params={"customer_id": list(IDS | NON_IDS)}
    )

    expected = [
        {
            "customer_ID": "1090",
            "annual_income": 41333,
            "MEAN(loans.amount)": 2426,
            "MEAN(loans.fee)": 199,
            "MIN(loans.amount)": 2426,
            "MIN(loans.fee)": 199,
            "MEAN(loans.DISTANCE_TO_HOLIDAY(loan_date))": 47,
            "MEAN(loans.TIME_SINCE_PREVIOUS(loan_date))": 39312000,
            "MIN(loans.DISTANCE_TO_HOLIDAY(loan_date))": 47,
            "MIN(loans.TIME_SINCE_PREVIOUS(loan_date))": 39312000
        }, {
            "customer_ID": "296",
            "annual_income": 41557,
            "MEAN(loans.amount)": 2003,
            "MEAN(loans.fee)": 24,
            "MIN(loans.amount)": 2003,
            "MIN(loans.fee)": 24,
            "MEAN(loans.DISTANCE_TO_HOLIDAY(loan_date))": 137,
            "MEAN(loans.TIME_SINCE_PREVIOUS(loan_date))": None,
            "MIN(loans.DISTANCE_TO_HOLIDAY(loan_date))": 137,
            "MIN(loans.TIME_SINCE_PREVIOUS(loan_date))": None
        }
    ]

    assert response.json() == expected
