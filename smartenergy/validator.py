import pandas as pd


class Validator:
    """cleans the raw data and keeps a list of what was wrong"""

    def __init__(self):
        self.errors = []

    def validate(self, df):
        """removes bad rows and returns the clean df sorted by time"""
        self.errors = []
        df = df.copy()
        df = df.reset_index(drop=True)

        # bad dates turn into NaT
        dates = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M", errors="coerce")
        bad_rows = []
        for i in df.index:
            if pd.isna(dates[i]):
                self.errors.append(f"Row {i + 1}: timestamp is not a valid date ({df.loc[i, 'timestamp']})")
                bad_rows.append(i)
        df["timestamp"] = dates
        df = df.drop(bad_rows)

        # text in kwh like "error" becomes NaN, empty ones are already NaN so we skip them here
        numbers = pd.to_numeric(df["kwh"], errors="coerce")
        bad_rows = []
        for i in df.index:
            if not pd.isna(df.loc[i, "kwh"]) and pd.isna(numbers[i]):
                self.errors.append(f"Row {i + 1}: kwh is not a number ({df.loc[i, 'kwh']})")
                bad_rows.append(i)
        df["kwh"] = numbers
        df = df.drop(bad_rows)

        bad_rows = []
        for i in df.index:
            if pd.isna(df.loc[i, "kwh"]):
                self.errors.append(f"Row {i + 1}: kwh is missing")
                bad_rows.append(i)
        df = df.drop(bad_rows)

        bad_rows = []
        for i in df.index:
            if df.loc[i, "kwh"] < 0:
                self.errors.append(f"Row {i + 1}: kwh is negative ({df.loc[i, 'kwh']})")
                bad_rows.append(i)
        df = df.drop(bad_rows)

        # keep the first one
        dups = df.duplicated(subset="timestamp", keep="first")
        bad_rows = []
        for i in df.index:
            if dups[i]:
                time_text = df.loc[i, "timestamp"].strftime("%Y-%m-%d %H:%M")
                self.errors.append(f"Row {i + 1}: duplicate timestamp ({time_text}), kept the first one")
                bad_rows.append(i)
        df = df.drop(bad_rows)

        df = df.sort_values("timestamp")
        df = df.reset_index(drop=True)
        return df

    def has_errors(self):
        return len(self.errors) > 0
