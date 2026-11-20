import os
from datetime import datetime
import pandas as pd


class ReportGenerator:
    """puts all the results together and saves them as a txt or csv report"""

    def __init__(self, metrics, forecast, tips, scenario, start_date=None, end_date=None, output_dir="reports"):
        self.metrics = metrics
        self.forecast = forecast
        self.tips = tips
        self.scenario = scenario
        # the metrics dict has no dates in it so the date range is passed in separately
        self.start_date = start_date
        self.end_date = end_date
        self.output_dir = output_dir

    def format_date(self, value):
        return pd.to_datetime(value).strftime("%Y-%m-%d")

    def to_text(self):
        """builds the whole report as one string"""
        lines = []
        lines.append("SmartEnergy AI report")
        lines.append("=====================")
        lines.append(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if self.start_date is not None and self.end_date is not None:
            lines.append(f"Data from {self.format_date(self.start_date)} to {self.format_date(self.end_date)}")
        else:
            lines.append("Data range: not given")
        lines.append("")

        m = self.metrics
        hours = []
        for h in m["peak_hours"]:
            hours.append(f"{h}:00")
        lines.append("Measured usage")
        lines.append("--------------")
        lines.append(f"Total usage: {m['total_kwh']:.2f} kWh")
        lines.append(f"Average per day: {m['avg_daily_kwh']:.2f} kWh")
        lines.append(f"Estimated cost: {m['cost']:.2f} AED")
        lines.append(f"Peak hours: {', '.join(hours)}")
        lines.append(f"Average weekday: {m['weekday_avg']:.2f} kWh")
        lines.append(f"Average weekend day: {m['weekend_avg']:.2f} kWh")
        lines.append("")

        lines.append("Forecast (PREDICTED, not measured)")
        lines.append("----------------------------------")
        if len(self.forecast) == 0:
            lines.append("No forecast was made.")
        else:
            first = self.format_date(self.forecast["date"].iloc[0])
            last = self.format_date(self.forecast["date"].iloc[-1])
            total = self.forecast["predicted_kwh"].sum()
            lines.append(f"Next {len(self.forecast)} days, {first} to {last}")
            for i in self.forecast.index:
                day = self.format_date(self.forecast.loc[i, "date"])
                lines.append(f"  {day}: {self.forecast.loc[i, 'predicted_kwh']:.2f} kWh (predicted)")
            lines.append(f"Predicted total: {total:.2f} kWh")
        lines.append("")

        lines.append("Recommendations")
        lines.append("---------------")
        number = 1
        for tip in self.tips:
            lines.append(f"{number}. {tip.title}")
            lines.append(f"   {tip.reason}")
            lines.append(f"   Estimated saving: {tip.saving_kwh:.1f} kWh per month")
            number = number + 1
        lines.append("")

        lines.append("Baseline vs proposed (ESTIMATED, per 30 day month)")
        lines.append("--------------------------------------------------")
        lines.append(self.scenario.to_string(index=False))
        lines.append("")

        lines.append("Assumptions and limitations")
        lines.append("---------------------------")
        lines.append("- Cost uses one flat tariff per kWh, a real bill has slabs and extra fees.")
        lines.append("- CO2 uses a fixed grid emission factor (shown in the table), not measured for this building.")
        lines.append("- Monthly numbers are scaled from the data to a 30 day month.")
        lines.append("- Savings assume wasted hours could drop to the night base load, real savings may be lower.")
        lines.append("- The forecast mixes a 7 day moving average and a straight trend line, it doesnt know about weather or holidays.")
        lines.append("- One meter for the whole building, so we cant tell which room or device used the energy.")
        lines.append("- Rows the validator found broken were removed before the analysis.")

        return "\n".join(lines)

    def make_file_path(self, extension):
        # makes the reports folder if it isnt there, time in the name so old reports dont get overwritten
        os.makedirs(self.output_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"report_{stamp}.{extension}")

    def export_txt(self):
        """saves the text report and returns the path"""
        path = self.make_file_path("txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_text())
        return path

    def export_csv(self):
        """saves all results in one csv with columns section, name, value and returns the path"""
        rows = []

        for key in self.metrics:
            value = self.metrics[key]
            # peak_hours is a list so turn it into text
            if key == "peak_hours":
                hours = []
                for h in value:
                    hours.append(str(h))
                value = " ".join(hours)
            rows.append({"section": "measured", "name": key, "value": value})

        for i in self.forecast.index:
            day = self.format_date(self.forecast.loc[i, "date"])
            rows.append({"section": "predicted", "name": day, "value": self.forecast.loc[i, "predicted_kwh"]})

        for tip in self.tips:
            rows.append({"section": "recommendation (estimated kWh per month)", "name": tip.title, "value": tip.saving_kwh})

        for i in self.scenario.index:
            metric = self.scenario.loc[i, "metric"]
            for col in ["baseline", "proposed", "saving"]:
                rows.append({"section": "scenario (estimated)", "name": f"{metric} {col}", "value": self.scenario.loc[i, col]})

        path = self.make_file_path("csv")
        pd.DataFrame(rows).to_csv(path, index=False)
        return path
