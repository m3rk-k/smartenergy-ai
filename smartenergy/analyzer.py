import pandas as pd


class Analyzer:
    """works out the usage numbers from the clean data"""

    # DEWA top slab 0.38 + 0.06 fuel surcharge
    def __init__(self, df, tariff=0.44):
        self.df = df
        self.tariff = tariff

    def total_kwh(self):
        return self.df["kwh"].sum()

    def daily_usage(self):
        """total kwh for each day"""
        df = self.df.copy()
        df["date"] = df["timestamp"].dt.date
        daily = df.groupby("date")["kwh"].sum()
        daily = daily.reset_index()
        return daily

    def average_daily(self):
        daily = self.daily_usage()
        return daily["kwh"].mean()

    def estimated_cost(self):
        """estimated cost in AED, not a real bill"""
        return self.total_kwh() * self.tariff

    def peak_hours(self, n=3):
        """hours of the day with highest average kwh"""
        df = self.df.copy()
        df["hour"] = df["timestamp"].dt.hour
        by_hour = df.groupby("hour")["kwh"].mean()
        by_hour = by_hour.sort_values(ascending=False)
        top = by_hour.head(n)
        return list(top.index)

    def weekday_vs_weekend(self):
        """average daily kwh on weekdays and on weekends (sat sun)"""
        daily = self.daily_usage()
        # 0 is monday so 5 and 6 is sat and sun
        day_num = pd.to_datetime(daily["date"]).dt.dayofweek
        weekday = daily[day_num < 5]
        weekend = daily[day_num >= 5]
        return weekday["kwh"].mean(), weekend["kwh"].mean()

    def get_metrics(self):
        weekday_avg, weekend_avg = self.weekday_vs_weekend()
        # float() so it prints 98428.75 not np.float64(98428.75)
        metrics = {
            "total_kwh": round(float(self.total_kwh()), 2),
            "avg_daily_kwh": round(float(self.average_daily()), 2),
            "cost": round(float(self.estimated_cost()), 2),
            "peak_hours": self.peak_hours(),
            "weekday_avg": round(float(weekday_avg), 2),
            "weekend_avg": round(float(weekend_avg), 2),
        }
        return metrics
