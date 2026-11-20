import pandas as pd
from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator


def make_df(timestamps, kwh):
    return pd.DataFrame({"timestamp": timestamps, "kwh": kwh})


def test_clean_df_stays_same_size():
    df = make_df(["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 02:00"], ["10.5", "12.0", "11.2"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 3
    assert v.errors == []
    assert v.has_errors() == False


def test_missing_kwh_is_removed():
    df = make_df(["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 02:00"], ["10.5", None, "11.2"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 2
    assert v.errors == ["Row 2: kwh is missing"]


def test_negative_kwh_is_removed():
    df = make_df(["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 02:00"], ["10.5", "-14.2", "11.2"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 2
    assert v.errors == ["Row 2: kwh is negative (-14.2)"]


def test_text_kwh_is_removed():
    df = make_df(["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 02:00"], ["10.5", "error", "11.2"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 2
    assert v.errors == ["Row 2: kwh is not a number (error)"]


def test_bad_date_is_removed():
    df = make_df(["2026-09-01 00:00", "2026-13-05 10:00", "2026-09-01 02:00"], ["10.5", "12.0", "11.2"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 2
    assert v.errors == ["Row 2: timestamp is not a valid date (2026-13-05 10:00)"]


def test_duplicate_timestamp_is_removed():
    df = make_df(["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 01:00"], ["10.5", "12.0", "12.0"])
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 2
    assert v.errors == ["Row 3: duplicate timestamp (2026-09-01 01:00), kept the first one"]


def test_each_problem_adds_a_message():
    # one of each problem, 5 bad rows and 1 good
    df = make_df(
        ["2026-09-01 00:00", "2026-09-01 01:00", "2026-09-01 02:00", "2026-09-01 03:00", "2026-13-05 10:00", "2026-09-01 00:00"],
        ["10.5", None, "-3", "abc", "12.0", "10.5"],
    )
    v = Validator()
    clean = v.validate(df)
    assert len(clean) == 1
    assert len(v.errors) == 5
    assert v.has_errors() == True


def test_sample_csv_removes_6_rows():
    raw = DataLoader("data/sample_usage.csv").load()
    v = Validator()
    clean = v.validate(raw)
    assert len(raw) - len(clean) == 6
    assert len(v.errors) == 6
