# Data dictionary: sample_usage.csv

## Where the data comes from

This data is **synthetic**. We made it ourselves with `data/make_sample_data.py` because we don't have access to a real building meter. It's not real measured data from any building.

We tried to make it look like a small campus building in Dubai (we call it Block C) with classrooms, a computer lab and offices. The script uses these rules:

- Base load of about 18 kWh every hour (servers, fridges, lab PCs on standby)
- Open hours are 8am to 6pm, Monday to Friday. During these hours lights and computers add about 40 kWh, plus AC that goes up with the outside temperature
- Outside temperature goes down from about 36C in September to about 28C in mid November, so AC use drops over time
- Some waste on purpose so the app has something to find: lights left on from 6pm to 10pm on weekdays, and AC still running on weekends from 9am to 5pm
- Random noise so it doesn't look too perfect
- `np.random.seed(42)` so the file comes out the same every time

## Columns

| Column | Type | Unit | Description | Example |
| --- | --- | --- | --- | --- |
| timestamp | text, format `YYYY-MM-DD HH:MM` | local time (Asia/Dubai) | Start of the hour the reading covers | 2026-09-01 14:00 |
| kwh | number, 2 decimals | kWh | Electricity used by the whole building in that hour | 112.37 |

## Size

- 1 Sep 2026 00:00 to 15 Nov 2026 23:00, one row per hour
- 1,825 rows (1,824 hours plus 1 duplicate)

## Bad rows we added on purpose

These are here to test the validator. The app should catch all of them and keep going with the rest.

| Row (0 based, after header) | Problem |
| --- | --- |
| 100 | kwh is empty |
| 250 | kwh is negative (-14.2) |
| 600 | kwh is the text "error" |
| 900 | timestamp has month 13 |
| 1300 | kwh is empty |
| 1500 and 1501 | same timestamp twice |

## Limitations

- Synthetic data, so the patterns are cleaner than a real building
- One meter for the whole building, so we can't tell which room or device used the energy
- No public holidays included
