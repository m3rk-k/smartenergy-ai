import pandas as pd
import pytest
from smartenergy.analyzer import Analyzer


# fri 4 sep is a weekday, sat 5 sep is weekend
# fri: 10 + 30 + 5 = 45, sat: 4 + 10 + 1 = 15, total 60
def make_df():
    times = [
        "2026-09-04 10:00", "2026-09-04 14:00", "2026-09-04 20:00",
        "2026-09-05 10:00", "2026-09-05 14:00", "2026-09-05 20:00",
    ]
    kwh = [10, 30, 5, 4, 10, 1]
    return pd.DataFrame({"timestamp": pd.to_datetime(times), "kwh": kwh})


def test_total_kwh():
    a = Analyzer(make_df())
    assert a.total_kwh() == 60


def test_daily_usage_has_one_row_per_day():
    daily = Analyzer(make_df()).daily_usage()
    assert len(daily) == 2
    assert list(daily["kwh"]) == [45, 15]


def test_average_daily():
    a = Analyzer(make_df())
    assert a.average_daily() == 30


def test_estimated_cost_uses_tariff():
    # 60 * 0.44 = 26.4, approx because of float rounding
    assert Analyzer(make_df()).estimated_cost() == pytest.approx(26.4)
    assert Analyzer(make_df(), tariff=0.5).estimated_cost() == pytest.approx(30)


def test_peak_hours_sorted_by_average():
    # hour 14 avg 20, hour 10 avg 7, hour 20 avg 3
    a = Analyzer(make_df())
    assert a.peak_hours() == [14, 10, 20]
    assert a.peak_hours(n=1) == [14]


def test_weekday_vs_weekend():
    weekday_avg, weekend_avg = Analyzer(make_df()).weekday_vs_weekend()
    assert weekday_avg == 45
    assert weekend_avg == 15


def test_get_metrics_has_all_keys():
    metrics = Analyzer(make_df()).get_metrics()
    assert metrics == {
        "total_kwh": 60,
        "avg_daily_kwh": 30,
        "cost": 26.4,
        "peak_hours": [14, 10, 20],
        "weekday_avg": 45,
        "weekend_avg": 15,
    }


def test_all_zero_kwh_gives_zero_and_no_crash():
    df = make_df()
    df["kwh"] = 0
    metrics = Analyzer(df).get_metrics()
    assert metrics["total_kwh"] == 0
    assert metrics["avg_daily_kwh"] == 0
    assert metrics["cost"] == 0
    assert metrics["weekday_avg"] == 0
    assert metrics["weekend_avg"] == 0
    # all hours tie so we only check we still get 3
    assert len(metrics["peak_hours"]) == 3
