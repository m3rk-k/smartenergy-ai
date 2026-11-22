import os
import tempfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator
from smartenergy.analyzer import Analyzer
from smartenergy.predictor import Predictor

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "data", "sample_usage.csv")
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HEAT_COLORS = ["#DCEFE2", "#2F7D4F", "#173024"]
ACTUAL_COLOR = "#2F7D4F"
PREDICTED_COLOR = "#C77700"


def load_raw_data(uploaded):
    """loads the uploaded csv, or the sample file if nothing was uploaded"""
    if uploaded is None:
        return DataLoader(SAMPLE_FILE).load(), "sample_usage.csv"

    # DataLoader needs a path, so save the upload to a temp file first
    temp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    temp.write(uploaded.getvalue())
    temp.close()
    try:
        raw = DataLoader(temp.name).load()
    except UnicodeDecodeError:
        raise ValueError(f"{uploaded.name} is not a plain text CSV")
    except ValueError as error:
        # show the real file name in the message, not the temp path
        raise ValueError(str(error).replace(temp.name, uploaded.name))
    finally:
        os.remove(temp.name)
    return raw, uploaded.name


def show_validation(raw, df, errors, file_name):
    """shows what was loaded and which rows were removed"""
    st.success(f"Loaded {len(raw)} rows from {file_name}")

    if len(errors) > 0:
        st.warning(f"Bad rows removed: {len(raw) - len(df)}. Rows used: {len(df)}")
        with st.expander("See the problems"):
            for error in errors:
                st.write(error)
    else:
        st.info("No problems found in the data")

    if len(df) > 0:
        first = df["timestamp"].min().strftime("%Y-%m-%d")
        last = df["timestamp"].max().strftime("%Y-%m-%d")
        st.caption(f"Data from {first} to {last}")


def show_metric_tiles(metrics):
    """shows the four main numbers in a row"""
    # peak_hours is sorted so the first one is the busiest hour
    peak = metrics["peak_hours"][0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total kWh", f"{metrics['total_kwh']:,.2f}")
    col2.metric("Average kWh per day", f"{metrics['avg_daily_kwh']:,.2f}")
    col3.metric("Estimated cost (AED)", f"{metrics['cost']:,.2f}")
    col4.metric("Peak hour", f"{peak:02d}:00")


def make_calendar_chart(daily):
    """daily kwh with weeks as columns and mon to sun as rows"""
    data = daily.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["day_num"] = data["date"].dt.dayofweek
    # go back to the monday of that week
    data["week"] = data["date"] - pd.to_timedelta(data["day_num"], unit="D")

    table = data.pivot(index="day_num", columns="week", values="kwh")
    # keep all 7 rows and every week, missing days just stay blank
    weeks = pd.date_range(data["week"].min(), data["week"].max(), freq="7D")
    table = table.reindex(index=range(7), columns=weeks)

    fig = go.Figure(go.Heatmap(
        z=table.values,
        x=table.columns,
        y=WEEKDAYS,
        colorscale=HEAT_COLORS,
        xgap=2,
        ygap=2,
        hoverongaps=False,
        colorbar={"title": "kWh"},
        hovertemplate="Week of %{x|%d %b %Y}<br>%{y}: %{z:,.1f} kWh<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickformat="%d %b")
    fig.update_layout(height=320, margin={"l": 10, "r": 10, "t": 10, "b": 10})
    return fig


def make_hour_chart(df):
    """average kwh for each hour of each weekday"""
    data = df.copy()
    data["day_num"] = data["timestamp"].dt.dayofweek
    data["hour"] = data["timestamp"].dt.hour

    table = data.pivot_table(index="day_num", columns="hour", values="kwh", aggfunc="mean")
    table = table.reindex(index=range(7), columns=range(24))

    hours = []
    for h in range(24):
        hours.append(f"{h:02d}:00")

    fig = go.Figure(go.Heatmap(
        z=table.values,
        x=hours,
        y=WEEKDAYS,
        colorscale=HEAT_COLORS,
        xgap=1,
        ygap=2,
        hoverongaps=False,
        colorbar={"title": "kWh"},
        hovertemplate="%{y} %{x}<br>Average: %{z:,.1f} kWh<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    # only every third hour so the labels dont overlap
    fig.update_xaxes(type="category", tickmode="array", tickvals=hours[::3])
    fig.update_layout(height=320, margin={"l": 10, "r": 10, "t": 10, "b": 10})
    return fig


def make_forecast_chart(daily, forecast):
    """actual daily kwh as a solid line, forecast dashed inside a PREDICTED area"""
    actual_dates = pd.to_datetime(daily["date"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=actual_dates,
        y=daily["kwh"],
        mode="lines",
        name="Actual",
        line={"color": ACTUAL_COLOR, "width": 2},
        hovertemplate="Actual: %{y:,.1f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["date"],
        y=forecast["predicted_kwh"],
        mode="lines",
        name="Predicted",
        line={"color": PREDICTED_COLOR, "width": 2, "dash": "dash"},
        hovertemplate="Predicted: %{y:,.1f} kWh<extra></extra>",
    ))

    # half a day each side so the shading covers the whole predicted days
    half_day = pd.Timedelta(hours=12)
    fig.add_vrect(
        x0=actual_dates.max() + half_day,
        x1=forecast["date"].max() + half_day,
        fillcolor=PREDICTED_COLOR,
        opacity=0.12,
        line_width=0,
        annotation_text="PREDICTED",
        annotation_position="top left",
    )
    fig.update_yaxes(title="kWh per day")
    fig.update_layout(
        height=400,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
    )
    return fig


def show_charts(df, daily, forecast_days):
    """shows the two heatmaps side by side and the forecast under them"""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Daily usage calendar")
        st.plotly_chart(make_calendar_chart(daily), width="stretch")
    with col2:
        st.subheader("Average usage by hour and weekday")
        st.plotly_chart(make_hour_chart(df), width="stretch")

    st.subheader("Forecast (predicted)")
    # the predictor raises an error if there are too few days
    try:
        forecast = Predictor(daily, window=7).forecast(forecast_days)
    except ValueError as error:
        st.info(f"No forecast for this file: {error}")
        return
    st.plotly_chart(make_forecast_chart(daily, forecast), width="stretch")


st.set_page_config(page_title="SmartEnergy AI", layout="wide")
st.title("SmartEnergy AI")

uploaded = st.sidebar.file_uploader("Upload a usage CSV", type=["csv"])
if uploaded is None:
    st.sidebar.caption("Using the sample data")
tariff = st.sidebar.number_input("Tariff (AED per kWh)", min_value=0.0, value=0.44, step=0.01, format="%.2f")
forecast_days = st.sidebar.number_input("Forecast days", min_value=1, max_value=30, value=7, step=1)

# bad csv files raise ValueError, this also covers files pandas cant read
try:
    raw, file_name = load_raw_data(uploaded)
except (FileNotFoundError, ValueError) as error:
    st.error(f"Could not load the file: {error}")
    st.stop()

validator = Validator()
df = validator.validate(raw)
show_validation(raw, df, validator.errors, file_name)

if len(df) == 0:
    st.error("No valid rows left after checking the data, so there is nothing to analyze.")
    st.stop()

analyzer = Analyzer(df, tariff)
metrics = analyzer.get_metrics()
show_metric_tiles(metrics)
show_charts(df, analyzer.daily_usage(), forecast_days)
