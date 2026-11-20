import pandas as pd


class Recommendation:
    """one energy saving tip"""

    def __init__(self, title, reason, saving_kwh):
        self.title = title
        self.reason = reason
        self.saving_kwh = saving_kwh


class Recommender:
    """looks for waste patterns in the data and suggests fixes"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.df = analyzer.df.copy()
        self.df["hour"] = self.df["timestamp"].dt.hour
        # 0 is monday so 5 and 6 is sat and sun, same as the analyzer
        self.df["day_num"] = self.df["timestamp"].dt.dayofweek
        self.num_days = self.df["timestamp"].dt.date.nunique()

    def base_load(self):
        """average kwh per hour between midnight and 6am"""
        night = self.df[self.df["hour"] < 6]
        return night["kwh"].mean()

    def per_month(self, kwh):
        # turns a total over the whole data into a 30 day month
        return kwh / self.num_days * 30

    def weekend_day_rows(self):
        # 9am to 5pm, the 16:00 reading covers 16:00 to 17:00
        df = self.df
        return df[(df["day_num"] >= 5) & (df["hour"] >= 9) & (df["hour"] < 17)]

    def weekday_evening_rows(self):
        # 6pm to 10pm
        df = self.df
        return df[(df["day_num"] < 5) & (df["hour"] >= 18) & (df["hour"] < 22)]

    def weekend_waste(self):
        """weekend kwh between 9am and 5pm above base load, over the whole data"""
        extra = self.weekend_day_rows()["kwh"] - self.base_load()
        # an hour below base load isnt negative waste, it just counts as 0
        extra = extra.clip(lower=0)
        return extra.sum()

    def evening_waste(self):
        """weekday kwh between 6pm and 10pm above base load, over the whole data"""
        extra = self.weekday_evening_rows()["kwh"] - self.base_load()
        extra = extra.clip(lower=0)
        return extra.sum()

    def get_recommendations(self):
        """checks 3 waste patterns and returns a list of Recommendation"""
        tips = []
        base = self.base_load()

        weekday_avg, weekend_avg = self.analyzer.weekday_vs_weekend()
        saving = self.per_month(self.weekend_waste())
        # saving above 0 so a building with no waste doesnt get a tip that saves nothing
        if weekend_avg > 0.4 * weekday_avg and saving > 0:
            percent = weekend_avg / weekday_avg * 100
            reason = (
                f"A weekend day uses {weekend_avg:.1f} kWh on average, that is {percent:.0f}% of a "
                f"weekday ({weekday_avg:.1f} kWh). The building is closed so this should be much lower, "
                f"the AC is probably left on."
            )
            tips.append(Recommendation("Turn off the AC at weekends", reason, round(saving, 1)))

        evening_avg = self.weekday_evening_rows()["kwh"].mean()
        # "well above" means more than 1.5 times the night base load, our own choice
        saving = self.per_month(self.evening_waste())
        if evening_avg > 1.5 * base and saving > 0:
            reason = (
                f"Between 6pm and 10pm on weekdays the building uses {evening_avg:.1f} kWh per hour, "
                f"but the night base load is only {base:.1f} kWh per hour. Lights or PCs are probably "
                f"left on after closing."
            )
            tips.append(Recommendation("Switch off lights after closing", reason, round(saving, 1)))

        by_hour = self.df.groupby("hour")["kwh"].mean()
        peak_hour = self.analyzer.peak_hours(1)[0]
        peak_kwh = by_hour[peak_hour]
        hourly_avg = self.analyzer.average_daily() / 24
        # "much higher" means more than 2 times the average hour, our own choice
        if peak_kwh > 2 * hourly_avg:
            # assumption: pre cooling and moving some load cuts about 10% of the extra use in the peak hour
            saving = (peak_kwh - hourly_avg) * 0.10 * 30
            reason = (
                f"The peak hour is {peak_hour}:00 with {peak_kwh:.1f} kWh on average, that is "
                f"{peak_kwh / hourly_avg:.1f} times the average hour ({hourly_avg:.1f} kWh). Pre cooling "
                f"the building earlier in the morning or moving some load out of this hour can help."
            )
            tips.append(Recommendation("Pre cool or shift load away from the peak", reason, round(saving, 1)))

        if len(tips) == 0:
            reason = "No clear waste pattern was found in this data. Keep checking your usage every month."
            tips.append(Recommendation("Keep tracking your usage", reason, 0))

        return tips

    def baseline_vs_proposed(self, cut_percent=100, co2_factor=0.4041):
        """estimated monthly kwh, cost and co2 now vs after removing cut_percent of the waste"""
        if cut_percent < 0 or cut_percent > 100:
            raise ValueError(f"cut_percent has to be between 0 and 100, got {cut_percent}")

        baseline_kwh = self.per_month(self.df["kwh"].sum())
        waste = self.per_month(self.weekend_waste() + self.evening_waste())
        saving_kwh = waste * cut_percent / 100
        proposed_kwh = baseline_kwh - saving_kwh

        tariff = self.analyzer.tariff
        # co2_factor is DEWA's grid emission factor, an assumption, we didnt measure it for this building
        rows = [
            {
                "metric": "kWh per month (estimated)",
                "baseline": baseline_kwh,
                "proposed": proposed_kwh,
                "saving": saving_kwh,
            },
            {
                "metric": "Cost AED per month (estimated)",
                "baseline": baseline_kwh * tariff,
                "proposed": proposed_kwh * tariff,
                "saving": saving_kwh * tariff,
            },
            {
                "metric": f"CO2 kg per month (estimated, assumes {co2_factor} kg per kWh)",
                "baseline": baseline_kwh * co2_factor,
                "proposed": proposed_kwh * co2_factor,
                "saving": saving_kwh * co2_factor,
            },
        ]
        table = pd.DataFrame(rows)
        table = table.round(2)
        return table
