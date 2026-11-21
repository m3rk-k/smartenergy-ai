import argparse
import sys

from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator
from smartenergy.analyzer import Analyzer
from smartenergy.predictor import Predictor
from smartenergy.recommender import Recommender
from smartenergy.report import ReportGenerator


def run(args):
    if args.tariff < 0:
        raise ValueError(f"--tariff cant be negative, got {args.tariff}")
    if args.days < 1:
        raise ValueError(f"--days has to be at least 1, got {args.days}")

    loader = DataLoader(args.csv)
    raw = loader.load()
    print(f"Loaded {len(raw)} rows from {args.csv}")

    validator = Validator()
    clean = validator.validate(raw)
    print(f"\nData check: {len(validator.errors)} bad rows removed, {len(clean)} rows left")
    for msg in validator.errors:
        print(f"  {msg}")

    if len(clean) == 0:
        raise ValueError("No good rows left after the data check, cant continue")

    analyzer = Analyzer(clean, args.tariff)
    metrics = analyzer.get_metrics()
    hours = []
    for h in metrics["peak_hours"]:
        hours.append(f"{h}:00")

    print("\nUsage")
    print(f"  Total: {metrics['total_kwh']:.2f} kWh")
    print(f"  Average per day: {metrics['avg_daily_kwh']:.2f} kWh")
    print(f"  ESTIMATED cost: {metrics['cost']:.2f} AED (at {args.tariff} AED per kWh)")
    print(f"  Peak hours: {', '.join(hours)}")
    print(f"  Average weekday: {metrics['weekday_avg']:.2f} kWh")
    print(f"  Average weekend day: {metrics['weekend_avg']:.2f} kWh")

    predictor = Predictor(analyzer.daily_usage())
    forecast = predictor.forecast(args.days)
    print(f"\nForecast for next {args.days} days (PREDICTED, not measured)")
    for i in forecast.index:
        day = forecast.loc[i, "date"].strftime("%Y-%m-%d")
        print(f"  {day}: {forecast.loc[i, 'predicted_kwh']:.2f} kWh PREDICTED")

    recommender = Recommender(analyzer)
    tips = recommender.get_recommendations()
    print("\nRecommendations")
    number = 1
    for tip in tips:
        print(f"  {number}. {tip.title}")
        print(f"     {tip.reason}")
        print(f"     ESTIMATED saving: {tip.saving_kwh:.1f} kWh per month")
        number = number + 1

    scenario = recommender.baseline_vs_proposed(args.cut)
    print(f"\nBaseline vs proposed, cutting {args.cut}% of the waste (ESTIMATED, per 30 day month)")
    print(scenario.to_string(index=False))

    if args.export:
        start = clean["timestamp"].iloc[0]
        end = clean["timestamp"].iloc[-1]
        report = ReportGenerator(metrics, forecast, tips, scenario, start, end)
        txt_path = report.export_txt()
        csv_path = report.export_csv()
        print("\nReport saved:")
        print(f"  {txt_path}")
        print(f"  {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="SmartEnergy AI: analyze hourly electricity usage")
    # nargs ? means the csv is optional so the default works
    parser.add_argument("csv", nargs="?", default="data/sample_usage.csv", help="path to the csv file")
    parser.add_argument("--tariff", type=float, default=0.44, help="price in AED per kWh")
    parser.add_argument("--days", type=int, default=7, help="how many days to forecast")
    parser.add_argument("--cut", type=float, default=100, help="percent of the waste to cut, 0 to 100")
    parser.add_argument("--export", action="store_true", help="save the report as txt and csv")
    args = parser.parse_args()

    try:
        run(args)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
