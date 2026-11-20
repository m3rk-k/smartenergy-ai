import numpy as np
import pandas as pd


class Predictor:
    """predicts the next days of usage from the daily totals"""

    def __init__(self, daily, window=7):
        if len(daily) < window:
            raise ValueError(
                f"Need at least {window} days of data to make a forecast, but only got {len(daily)} days"
            )

        # copy so we dont change the original df, and make sure days are in order
        self.daily = daily.copy()
        self.daily["date"] = pd.to_datetime(self.daily["date"])
        self.daily = self.daily.sort_values("date").reset_index(drop=True)
        self.window = window

    def moving_average(self):
        """average of the last `window` days, for every day"""
        return self.daily["kwh"].rolling(self.window).mean()

    def fit_trend(self):
        """fits a straight line through the daily kwh and returns slope and intercept"""
        # day numbers 0, 1, 2, ... because polyfit needs numbers not dates
        x = np.arange(len(self.daily))
        y = self.daily["kwh"].values
        slope, intercept = np.polyfit(x, y, 1)
        return slope, intercept

    def forecast(self, days):
        """predicts the next days as the average of the moving average and the trend line"""
        last_avg = self.moving_average().iloc[-1]
        slope, intercept = self.fit_trend()

        last_date = self.daily["date"].iloc[-1]
        last_day_num = len(self.daily) - 1

        rows = []
        for i in range(1, days + 1):
            day_num = last_day_num + i
            trend_value = slope * day_num + intercept
            predicted = (last_avg + trend_value) / 2

            rows.append({
                "date": last_date + pd.Timedelta(days=i),
                "predicted_kwh": round(predicted, 2),
            })

        return pd.DataFrame(rows)
