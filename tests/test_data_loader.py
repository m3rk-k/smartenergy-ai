import pytest
from smartenergy.data_loader import DataLoader


def test_sample_csv_loads():
    df = DataLoader("data/sample_usage.csv").load()
    assert len(df) == 1825
    assert "timestamp" in df.columns
    assert "kwh" in df.columns


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        DataLoader("data/this_file_doesnt_exist.csv").load()


def test_empty_file_raises_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(ValueError, match="empty"):
        DataLoader(str(path)).load()


def test_csv_without_kwh_column_raises_error(tmp_path):
    path = tmp_path / "no_kwh.csv"
    path.write_text("timestamp,power\n2026-09-01 00:00,19.5\n")
    # check the message says which column
    with pytest.raises(ValueError, match="kwh"):
        DataLoader(str(path)).load()
