import os
import tempfile
import streamlit as st
from smartenergy.data_loader import DataLoader
from smartenergy.validator import Validator
from smartenergy.analyzer import Analyzer

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), "data", "sample_usage.csv")


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


st.set_page_config(page_title="SmartEnergy AI", layout="wide")
st.title("SmartEnergy AI")

uploaded = st.sidebar.file_uploader("Upload a usage CSV", type=["csv"])
if uploaded is None:
    st.sidebar.caption("Using the sample data")
tariff = st.sidebar.number_input("Tariff (AED per kWh)", min_value=0.0, value=0.44, step=0.01, format="%.2f")

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
