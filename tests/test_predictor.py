import pandas as pd
import pytest
from smartenergy.predictor import Predictor


def make_daily(values):
    # one row per day starting on 1 jan
    dates = pd.date_range("2026-01-01", periods=len(values))
    return pd.DataFrame({"date": dates, "kwh": values})


def test_forecast_returns_right_number_of_rows():
    daily = make_daily([10, 12, 11, 13, 12, 14, 13, 15, 14, 16])
    result = Predictor(daily).forecast(5)
    assert len(result) == 5
    assert list(result.columns) == ["date", "predicted_kwh"]


def test_forecast_dates_start_day_after_last_date():
    daily = make_daily([10, 12, 11, 13, 12, 14, 13, 15, 14, 16])
    result = Predictor(daily).forecast(3)
    # last date in the data is 10 jan
    assert result["date"].iloc[0] == pd.Timestamp("2026-01-11")
    assert result["date"].iloc[1] == pd.Timestamp("2026-01-12")
    assert result["date"].iloc[2] == pd.Timestamp("2026-01-13")


def test_flat_input_gives_flat_forecast():
    daily = make_daily([20] * 10)
    result = Predictor(daily).forecast(4)
    for value in result["predicted_kwh"]:
        assert value == 20


def test_rising_input_gives_rising_forecast():
    daily = make_daily([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
    result = Predictor(daily).forecast(4)
    values = list(result["predicted_kwh"])
    for i in range(1, len(values)):
        assert values[i] > values[i - 1]


def test_fewer_than_7_days_raises_error():
    daily = make_daily([10, 11, 12])
    with pytest.raises(ValueError, match="at least 7 days"):
        Predictor(daily)
