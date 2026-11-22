# SmartEnergy AI

This is our project for DSAI455. It takes hourly electricity readings from a CSV file and tells you how much energy a building is using, where it is being wasted and what might happen in the next few days.

## What the app does

1. Loads the readings from a CSV file
2. Checks the data and removes bad rows (missing values, negative kWh, text instead of numbers, bad dates, duplicates) and tells you which rows it removed
3. Calculates total usage, average per day, estimated cost, peak hours and weekday vs weekend usage
4. Predicts the next days using a moving average and a trend line
5. Gives tips for saving energy based on patterns in the data
6. Compares the current usage (baseline) with a proposed scenario for kWh, cost and CO2
7. Can save everything as a txt and csv report

The forecast is only a prediction and the savings, cost and CO2 are estimates, so the app labels them that way in the output.

## Setup

You need Python 3.10 or newer. Run these from inside the project folder.

### Windows

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Mac

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the CLI

Run it on our sample data:

```
python main.py
```

Forecast 14 days instead of 7:

```
python main.py --days 14
```

See what happens if we cut 50% of the waste (default is 100):

```
python main.py --cut 50
```

Save the report as txt and csv in the `reports/` folder:

```
python main.py --export
```

You can use them together:

```
python main.py --days 3 --cut 50 --export
```

Use a different CSV file or tariff (default tariff is 0.44 AED per kWh):

```
python main.py path/to/your_file.csv --tariff 0.5
```

See all the options:

```
python main.py --help
```

## Running the dashboard

```
streamlit run app.py
```

It should open in your browser. If it doesnt, copy the local link from the terminal.

## The data

We dont have access to a real building meter, so `data/sample_usage.csv` is synthetic data we made to look like a small campus building in Dubai. It also has a few bad rows on purpose to test the validator.

The columns and how we made the data are explained in [data/data_dictionary.md](data/data_dictionary.md).

## Project structure

```
smartenergy-ai/
    main.py                  command line app
    app.py                   streamlit dashboard
    requirements.txt         packages we need
    data/
        sample_usage.csv     sample readings
        data_dictionary.md   explains the data
        make_sample_data.py  script that made the sample data
    smartenergy/
        data_loader.py       reads the csv
        validator.py         finds and removes bad rows
        analyzer.py          calculates the metrics
        predictor.py         forecasts the next days
        recommender.py       saving tips and baseline vs proposed
        report.py            exports the txt and csv report
    tests/                   pytest tests, one file per module
    reports/                 exported reports go here
    .github/workflows/       runs the tests on GitHub
```

## Running tests

From the project folder with the venv activated:

```
pytest -v
```

The tests also run on GitHub on every push and pull request.

## Team

- **Moustafa (m3rk-k):** data_loader, validator, analyzer, main.py and CI
- **Abdullah (3kalj):** predictor, recommender, report and app.py
