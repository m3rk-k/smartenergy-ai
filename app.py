import os
import tempfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator
from smartenergy.analyzer import Analyzer
from smartenergy.predictor import Predictor
from smartenergy.recommender import Recommender
from smartenergy.report import ReportGenerator

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "data", "sample_usage.csv")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CO2_FACTOR = 0.4041

THEMES = {
    "Meter": {
        "bg": "#0E100D",
        "panel": "#171A15",
        "border": "#2A2F26",
        "number": "#FFB000",
        "text": "#E6E9E1",
        "label": "#8A9183",
        "good": "#7CFF6B",
        "bad": "#FF5A4E",
        "accent": "#FFB000",
        "on_accent": "#0E100D",
        "predicted": "#E6E9E1",
        "heat": ["#23271F", "#8A6200", "#FFB000"],
    },
    "Light": {
        "bg": "#F6F4EE",
        "panel": "#FFFFFF",
        "border": "#E2DED3",
        "number": "#1F3B2D",
        "text": "#1F3B2D",
        "label": "#6B7166",
        "good": "#2F7D4F",
        "bad": "#C77700",
        "accent": "#2F7D4F",
        "on_accent": "#FFFFFF",
        "predicted": "#C77700",
        "heat": ["#E7F2EA", "#2F7D4F", "#1F3B2D"],
    },
}

# the layout is the same for both themes, only the --color values change
PAGE_CSS = """
.stApp, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: var(--bg); }
[data-testid="stToolbar"] button, [data-testid="stToolbar"] span { color: var(--label) !important; }
[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--border); }
.stApp h1 { color: var(--text); font-family: monospace; font-size: 1.6rem; }
.stApp h3 {
    color: var(--label); font-size: 0.78rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; padding: 0 0 6px 0;
}
.stApp p, .stApp label { color: var(--text); }
[data-testid="stCaptionContainer"] p, [data-testid="stWidgetLabel"] p {
    color: var(--label); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em;
}

[class*="st-key-panel"] {
    background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 6px;
}
[data-testid="stMetric"] {
    background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 14px 16px;
}
[data-testid="stMetricLabel"] p {
    color: var(--label); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
    color: var(--number); font-family: monospace; font-size: clamp(1.05rem, 1.9vw, 2rem);
    overflow: visible; text-overflow: clip;
}

[data-testid="stAlertContainer"] { background: var(--panel) !important; border: 1px solid var(--border); }
[data-testid="stAlertContentSuccess"] p { color: var(--good); }
[data-testid="stAlertContentWarning"] p { color: var(--bad); }
[data-testid="stAlertContentError"] p { color: var(--bad); }
[data-testid="stAlertContentInfo"] p { color: var(--text); }
[data-testid="stExpander"] details { background: var(--panel); border: 1px solid var(--border); }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary:hover { color: var(--text); }
[data-testid="stExpander"] svg { fill: var(--text); color: var(--text); }

[data-testid="stNumberInputContainer"], [data-testid="stNumberInputContainer"] > div,
[data-testid="stNumberInputContainer"] input {
    background: var(--bg) !important; color: var(--text) !important; border-color: var(--border) !important;
}
[data-testid="stNumberInputContainer"] button { background: var(--bg) !important; color: var(--text) !important; }
[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploader"] section {
    background: var(--bg) !important; border: 1px dashed var(--border);
}
[data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] div { color: var(--label); }
[data-testid="stFileUploader"] button {
    background: var(--panel) !important; color: var(--text) !important; border: 1px solid var(--border) !important;
}
[data-testid="stRadioOption"] > div > div:first-child {
    background: var(--bg) !important; border: 1px solid var(--label);
}
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child { background: var(--accent) !important; }
[data-testid="stRadioOption"] > div > div:first-child > div { background: var(--bg) !important; }
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child > div {
    background: var(--on_accent) !important;
}
[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important; color: var(--on_accent) !important; border: none !important;
}
[data-testid="stBaseButton-primary"] p { color: var(--on_accent) !important; font-weight: 600; }

.tip-card {
    background: var(--bg); border: 1px solid var(--border); border-left: 3px solid var(--bad);
    border-radius: 4px; padding: 12px 14px; font-family: sans-serif;
}
.tip-card.general { border-left-color: var(--good); }
.tip-title { color: var(--text); font-weight: 600; margin-bottom: 4px; }
.tip-reason { color: var(--label); font-size: 0.85rem; line-height: 1.45; margin-bottom: 8px; }
.tip-label { color: var(--label); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; }
.tip-saving { color: var(--good); font-family: monospace; font-size: 1.1rem; }

.receipt {
    background: var(--bg); border: 1px solid var(--border); border-radius: 2px; padding: 18px;
    color: var(--text); font-family: "Courier New", Courier, monospace; font-size: 0.82rem; overflow-x: auto;
}
.receipt-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.receipt-name { font-weight: 700; font-size: 1rem; }
.receipt-sub { color: var(--label); font-size: 0.72rem; margin-top: 2px; }
.receipt-stamp {
    color: var(--bad); border: 2px solid var(--bad); padding: 2px 8px;
    font-weight: 700; letter-spacing: 0.12em; transform: rotate(-3deg);
}
.receipt table { width: 100%; border-collapse: collapse; margin: 14px 0; }
.receipt th, .receipt td {
    border-bottom: 1px dashed var(--label); padding: 7px 4px; text-align: right; white-space: nowrap;
}
.receipt th { color: var(--label); font-size: 0.7rem; font-weight: 400; }
.receipt th:first-child, .receipt td:first-child { text-align: left; }
.receipt td:last-child { color: var(--good); }
.receipt-total { display: flex; justify-content: space-between; align-items: baseline; font-weight: 700; }
.receipt-total span:last-child { color: var(--good); font-size: 1.25rem; }
.receipt-print {
    color: var(--label); font-size: 0.66rem; line-height: 1.5;
    border-top: 1px dashed var(--label); margin-top: 12px; padding-top: 8px;
}
/* smaller receipt on a phone so all 4 columns fit */
@media (max-width: 640px) {
    .receipt { padding: 12px; font-size: 0.72rem; }
    .receipt th, .receipt td { padding: 6px 2px; }
}
"""


def apply_theme(colors):
    """puts the theme colors and the page css into the app"""
    variables = ""
    for name in colors:
        # heat is a list for the charts, not a css color
        if name != "heat":
            variables = variables + f"--{name}: {colors[name]}; "
    st.html(f"<style>:root {{ {variables} }} {PAGE_CSS}</style>")


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


def style_chart(fig, colors, height):
    """same chart colors and spacing for every chart"""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": colors["label"]},
        hoverlabel={"bgcolor": colors["panel"], "bordercolor": colors["border"], "font": {"color": colors["text"]}},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
    )
    # automargin makes room for the axis labels so they dont get cut off
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=colors["border"], automargin=True)
    fig.update_yaxes(gridcolor=colors["border"], zeroline=False, linecolor=colors["border"], automargin=True)


def make_calendar_chart(daily, colors):
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
        colorscale=colors["heat"],
        xgap=2,
        ygap=2,
        hoverongaps=False,
        colorbar={"title": "kWh"},
        hovertemplate="Week of %{x|%d %b %Y}<br>%{y}: %{z:,.1f} kWh<extra></extra>",
    ))
    style_chart(fig, colors, 320)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickformat="%d %b")
    return fig


def make_hour_chart(df, colors):
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
        colorscale=colors["heat"],
        xgap=1,
        ygap=2,
        hoverongaps=False,
        colorbar={"title": "kWh"},
        hovertemplate="%{y} %{x}<br>Average: %{z:,.1f} kWh<extra></extra>",
    ))
    style_chart(fig, colors, 320)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    # only every third hour so the labels dont overlap
    fig.update_xaxes(type="category", tickmode="array", tickvals=hours[::3])
    return fig


def make_forecast_chart(daily, forecast, colors):
    """actual daily kwh as a solid line, forecast dashed inside a PREDICTED area"""
    actual_dates = pd.to_datetime(daily["date"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=actual_dates,
        y=daily["kwh"],
        mode="lines",
        name="Actual",
        line={"color": colors["accent"], "width": 2},
        hovertemplate="Actual: %{y:,.1f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["date"],
        y=forecast["predicted_kwh"],
        mode="lines",
        name="Predicted",
        line={"color": colors["predicted"], "width": 2, "dash": "dash"},
        hovertemplate="Predicted: %{y:,.1f} kWh<extra></extra>",
    ))

    # half a day each side so the shading covers the whole predicted days
    half_day = pd.Timedelta(hours=12)
    fig.add_vrect(
        x0=actual_dates.max() + half_day,
        x1=forecast["date"].max() + half_day,
        fillcolor=colors["predicted"],
        opacity=0.12,
        line_width=0,
        annotation_text="PREDICTED",
        annotation_position="top left",
        annotation_font_color=colors["predicted"],
    )
    style_chart(fig, colors, 400)
    fig.update_yaxes(title="kWh per day")
    fig.update_layout(hovermode="x unified", legend={"orientation": "h", "y": 1.08})
    return fig


def make_forecast(daily, days):
    """returns the forecast and an error message, the message is empty if it worked"""
    try:
        return Predictor(daily, window=7).forecast(days), ""
    except ValueError as error:
        # the report can handle an empty forecast
        return pd.DataFrame(columns=["date", "predicted_kwh"]), str(error)


def show_charts(df, daily, forecast, forecast_error, colors):
    """shows the two heatmaps side by side and the forecast under them"""
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True, key="panel_calendar"):
            st.subheader("Daily usage calendar")
            st.plotly_chart(make_calendar_chart(daily, colors), width="stretch", theme=None)
    with col2:
        with st.container(border=True, key="panel_hours"):
            st.subheader("Average usage by hour and weekday")
            st.plotly_chart(make_hour_chart(df, colors), width="stretch", theme=None)

    with st.container(border=True, key="panel_forecast"):
        st.subheader("Forecast (predicted)")
        if forecast_error != "":
            st.info(f"No forecast for this file: {forecast_error}")
        else:
            st.plotly_chart(make_forecast_chart(daily, forecast, colors), width="stretch", theme=None)


def show_recommendations(tips):
    """shows each recommendation as a card"""
    for tip in tips:
        card_class = "tip-card"
        saving_text = f"{tip.saving_kwh:,.1f} kWh per month"
        if tip.saving_kwh == 0:
            card_class = "tip-card general"
            saving_text = "None estimated"

        st.html(
            f'<div class="{card_class}">'
            f'<div class="tip-title">{tip.title}</div>'
            f'<div class="tip-reason">{tip.reason}</div>'
            f'<div class="tip-label">Estimated saving</div>'
            f'<div class="tip-saving">{saving_text}</div>'
            f"</div>"
        )


def receipt_row(name, row):
    return (
        f"<tr><td>{name}</td><td>{row['baseline']:,.2f}</td>"
        f"<td>{row['proposed']:,.2f}</td><td>{row['saving']:,.2f}</td></tr>"
    )


def show_receipt(scenario, tariff, cut_percent):
    """shows baseline vs proposed like a printed electricity bill"""
    kwh = scenario.iloc[0]
    cost = scenario.iloc[1]
    co2 = scenario.iloc[2]

    st.html(
        '<div class="receipt">'
        '<div class="receipt-top"><div>'
        '<div class="receipt-name">SMARTENERGY AI</div>'
        f'<div class="receipt-sub">30 DAY MONTH, {cut_percent}% OF WASTE REMOVED</div>'
        '</div><div class="receipt-stamp">ESTIMATE</div></div>'
        "<table><tr><th>ITEM</th><th>BASELINE</th><th>PROPOSED</th><th>SAVING</th></tr>"
        + receipt_row("kWh", kwh)
        + receipt_row("AED", cost)
        + receipt_row("CO2 kg", co2)
        + "</table>"
        '<div class="receipt-total"><span>ESTIMATED SAVING</span>'
        f"<span>AED {cost['saving']:,.2f}</span></div>"
        '<div class="receipt-print">'
        "ASSUMPTIONS: waste is weekend use from 9am to 5pm and weekday use from 6pm to 10pm "
        "above the night base load (midnight to 6am). The peak hour tip is not counted here. "
        f"Flat tariff of {tariff:.2f} AED per kWh, a real bill has slabs and fees. "
        f"CO2 factor of {CO2_FACTOR} kg per kWh from DEWA, not measured for this building. "
        "This is not a real bill."
        "</div></div>"
    )


def show_savings(tips, scenario, tariff, cut_percent):
    """recommendations on the left, the receipt on the right"""
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True, key="panel_tips"):
            st.subheader("Recommendations")
            show_recommendations(tips)
    with col2:
        with st.container(border=True, key="panel_receipt"):
            st.subheader("Baseline vs proposed")
            show_receipt(scenario, tariff, cut_percent)


def show_export(report):
    """saves the txt and csv reports when the button is clicked"""
    if st.button("Export report", type="primary"):
        try:
            txt_path = report.export_txt()
            csv_path = report.export_csv()
        except OSError as error:
            st.error(f"Could not save the report: {error}")
            return
        st.success("Report saved")
        st.code(f"{txt_path}\n{csv_path}", language=None)


st.set_page_config(page_title="SmartEnergy AI", layout="wide")

uploaded = st.sidebar.file_uploader("Upload a usage CSV", type=["csv"])
if uploaded is None:
    st.sidebar.caption("Using the sample data")
tariff = st.sidebar.number_input("Tariff (AED per kWh)", min_value=0.0, value=0.44, step=0.01, format="%.2f")
forecast_days = st.sidebar.number_input("Forecast days", min_value=1, max_value=30, value=7, step=1)
cut_percent = st.sidebar.number_input("Cut percent of waste", min_value=0, max_value=100, value=100, step=5)
theme = st.sidebar.radio("Theme", ["Meter", "Light"], horizontal=True)
colors = THEMES[theme]
apply_theme(colors)

st.title("SmartEnergy AI")

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

daily = analyzer.daily_usage()
forecast, forecast_error = make_forecast(daily, forecast_days)
show_charts(df, daily, forecast, forecast_error, colors)

recommender = Recommender(analyzer)
tips = recommender.get_recommendations()
scenario = recommender.baseline_vs_proposed(cut_percent, CO2_FACTOR)
show_savings(tips, scenario, tariff, cut_percent)

report = ReportGenerator(
    metrics, forecast, tips, scenario,
    df["timestamp"].min(), df["timestamp"].max(), output_dir=REPORTS_DIR,
)
show_export(report)
