import os
import pandas as pd


class DataLoader:
    """reads the meter csv into a dataframe"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def load(self):
        """loads the csv and checks the basic stuff, cleaning is the validators job"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Could not find the file: {self.file_path}")

        if os.path.getsize(self.file_path) == 0:
            raise ValueError(f"The file is empty: {self.file_path}")

        df = pd.read_csv(self.file_path)

        # only header no data
        if len(df) == 0:
            raise ValueError(f"The file has no data rows, only the header: {self.file_path}")

        for col in ["timestamp", "kwh"]:
            if col not in df.columns:
                raise ValueError(f"Missing column '{col}' in {self.file_path}")

        self.df = df
        return df

    def get_summary(self):
        if self.df is None:
            self.load()

        summary = {
            "rows": len(self.df),
            "first_timestamp": self.df["timestamp"].iloc[0],
            "last_timestamp": self.df["timestamp"].iloc[-1],
        }
        return summary
