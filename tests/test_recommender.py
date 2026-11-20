import pandas as pd
from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator
from smartenergy.analyzer import Analyzer
from smartenergy.recommender import Recommender


def make_flat_building():
    # 2 weeks, every hour uses exactly 10 kwh so there is no waste anywhere
    times = pd.date_range("2026-01-05", periods=14 * 24, freq="h")
    return pd.DataFrame({"timestamp": times, "kwh": 10.0})


def make_weekend_ac_building():
    # 5 jan 2026 is a monday, base load is 10, open hours 9am to 5pm use 50 on weekdays
    # and 40 on weekends, like the AC was left on
    times = pd.date_range("2026-01-05", periods=14 * 24, freq="h")
    rows = []
    for t in times:
        kwh = 10.0
        if t.hour >= 9 and t.hour < 17:
            if t.dayofweek < 5:
                kwh = 50.0
            else:
                kwh = 40.0
        rows.append({"timestamp": t, "kwh": kwh})
    return pd.DataFrame(rows)


def load_sample():
    df = DataLoader("data/sample_usage.csv").load()
    return Validator().validate(df)


def test_high_weekend_use_gives_weekend_recommendation():
    df = make_weekend_ac_building()
    tips = Recommender(Analyzer(df)).get_recommendations()
    titles = []
    for tip in tips:
        titles.append(tip.title)
    assert "Turn off the AC at weekends" in titles


def test_no_waste_gives_general_tip():
    df = make_flat_building()
    tips = Recommender(Analyzer(df)).get_recommendations()
    assert len(tips) == 1
    assert tips[0].title == "Keep tracking your usage"
    assert tips[0].saving_kwh == 0


def test_savings_are_never_negative():
    recommender = Recommender(Analyzer(load_sample()))
    for tip in recommender.get_recommendations():
        assert tip.saving_kwh >= 0
    table = recommender.baseline_vs_proposed()
    for value in table["saving"]:
        assert value >= 0


def test_zero_percent_cut_gives_zero_saving():
    table = Recommender(Analyzer(load_sample())).baseline_vs_proposed(0)
    for i in table.index:
        assert table.loc[i, "saving"] == 0
        assert table.loc[i, "baseline"] == table.loc[i, "proposed"]


def test_sample_csv_gives_two_recommendations():
    tips = Recommender(Analyzer(load_sample())).get_recommendations()
    assert len(tips) == 2
