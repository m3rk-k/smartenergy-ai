# makes fake meter data for Block C, we dont have real meter data so this is made to look like a real campus building
# run once: python data/make_sample_data.py

import numpy as np
import pandas as pd

np.random.seed(42)  # same file every time

hours = pd.date_range("2026-09-01 00:00", "2026-11-15 23:00", freq="h")

rows = []
for t in hours:
    day_num = (t - hours[0]).days

    # dubai gets cooler from sep to nov, around 36C down to 28C avg
    avg_temp = 36 - day_num * 0.105
    temp = avg_temp + 5 * np.sin((t.hour - 9) / 24 * 2 * np.pi)

    is_weekend = t.weekday() >= 5
    open_hours = 8 <= t.hour < 18

    kwh = 18  # base load

    if not is_weekend and open_hours:
        kwh += 40
        kwh += (temp - 22) * 4.5
    elif not is_weekend and 18 <= t.hour < 22:
        kwh += 12  # lights left on after closing
        kwh += (temp - 22) * 1.5
    elif is_weekend and 9 <= t.hour < 17:
        kwh += (temp - 22) * 2.5  # AC still running weekend even nobody there

    kwh += np.random.normal(0, 3)
    rows.append([t.strftime("%Y-%m-%d %H:%M"), round(max(kwh, 5), 2)])

df = pd.DataFrame(rows, columns=["timestamp", "kwh"])

# bad rows on purpose so validator have something to catch
df["kwh"] = df["kwh"].astype(object)  # or pandas wont let us put text in number column
df.loc[100, "kwh"] = None
df.loc[250, "kwh"] = -14.2
df.loc[600, "kwh"] = "error"
df.loc[900, "timestamp"] = "2026-13-05 10:00"  # month 13
df.loc[1300, "kwh"] = None
bad_dup = df.iloc[[1500]]
df = pd.concat([df.iloc[:1501], bad_dup, df.iloc[1501:]], ignore_index=True)

df.to_csv("data/sample_usage.csv", index=False)
print("saved", len(df), "rows")
