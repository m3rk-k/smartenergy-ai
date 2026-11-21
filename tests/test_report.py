import os
import pandas as pd
from smartenergy.recommender import Recommendation
from smartenergy.report import ReportGenerator


def make_report(output_dir):
    # small made up results so the test doesnt need the whole pipeline
    metrics = {
        "total_kwh": 1000.0,
        "avg_daily_kwh": 100.0,
        "cost": 440.0,
        "peak_hours": [15, 14, 16],
        "weekday_avg": 120.0,
        "weekend_avg": 50.0,
    }
    forecast = pd.DataFrame({
        "date": pd.date_range("2026-01-11", periods=3),
        "predicted_kwh": [101.5, 102.0, 102.5],
    })
    tips = [Recommendation("Turn off the AC at weekends", "Weekend use is high.", 300.0)]
    scenario = pd.DataFrame({
        "metric": ["kWh per month (estimated)"],
        "baseline": [3000.0],
        "proposed": [2700.0],
        "saving": [300.0],
    })
    return ReportGenerator(metrics, forecast, tips, scenario, "2026-01-01", "2026-01-10", output_dir=str(output_dir))


def test_export_txt_creates_file(tmp_path):
    path = make_report(tmp_path).export_txt()
    assert os.path.exists(path)
    assert path.endswith(".txt")


def test_export_csv_creates_file(tmp_path):
    path = make_report(tmp_path).export_csv()
    assert os.path.exists(path)
    assert path.endswith(".csv")
    df = pd.read_csv(path)
    assert list(df.columns) == ["section", "name", "value"]


def test_txt_says_predicted_and_estimated(tmp_path):
    path = make_report(tmp_path).export_txt()
    with open(path, encoding="utf-8") as f:
        text = f.read()
    assert "PREDICTED" in text
    assert "ESTIMATED" in text


def test_reports_folder_is_created_if_missing(tmp_path):
    folder = tmp_path / "reports"
    assert not os.path.exists(folder)
    make_report(folder).export_txt()
    assert os.path.isdir(folder)
