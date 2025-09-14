from io import BytesIO

import pandas as pd

from tests.utils import (generate_uuid7, read_fixture, simulate_db_state,
                         simulate_redis_state)


def test_read_fixture_json():
    data = read_fixture("providers/coingecko_rate_limit.json")
    assert data["status"] == 429


def test_read_fixture_csv():
    content = read_fixture("csv/transactions_dst.csv")
    assert "2021-03-14T01:30:00-05:00" in content


def test_read_fixture_parquet():
    raw = read_fixture("parquet/dst_transition.parquet.b64", mode="rb")
    df = pd.read_parquet(BytesIO(raw))
    assert df.iloc[0]["value"] == 100


def test_generate_uuid7():
    uid = generate_uuid7()
    assert len(uid) == 36 and uid[14] == "7"


def test_simulated_states():
    redis = simulate_redis_state({"a": "1"})
    db = simulate_db_state({"records": []})
    assert redis["a"] == "1"
    assert db["records"] == []
