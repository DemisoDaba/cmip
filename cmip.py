import streamlit as st
import requests
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(page_title="CMIP6 Ethiopia Climate Tool", layout="wide")

st.title("🌍 CMIP6 Climate Analysis Tool – Ethiopia")

# =====================================================
# 1. MODEL + VARIABLE SELECTION
# =====================================================
st.sidebar.header("🧠 CMIP6 Configuration")

variable = st.sidebar.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# fallback models
fallback_models = [
    "MPI-ESM1-2-LR",
    "EC-Earth3",
    "NorESM2-LM",
    "MIROC6",
    "GFDL-ESM4",
    "CNRM-CM6-1",
    "UKESM1-0-LL"
]

# =====================================================
# 2. ESGF MODEL FETCH (SAFE)
# =====================================================
def get_models(var, exp):
    try:
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&format=json&limit=50"
        )

        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return fallback_models

        data = r.json()

        if "response" not in data:
            return fallback_models

        docs = data["response"].get("docs", [])

        models = set()
        for d in docs:
            if "source_id" in d:
                models.add(d["source_id"])

        if len(models) == 0:
            return fallback_models

        return sorted(list(models))

    except:
        return fallback_models

# =====================================================
# 3. MODEL SELECTION
# =====================================================
models = get_models(variable, experiment)

model = st.sidebar.selectbox("CMIP6 Model", models)

st.sidebar.success(f"Selected: {model}")

# =====================================================
# 4. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Longitude", value=33.0)
max_lon = st.sidebar.number_input("Max Longitude", value=48.0)
min_lat = st.sidebar.number_input("Min Latitude", value=3.0)
max_lat = st.sidebar.number_input("Max Latitude", value=15.0)

# =====================================================
# 5. DATA INPUT (ESGF URL)
# =====================================================
url = st.text_input("🌐 Enter CMIP6 NetCDF ESGF URL")

# =====================================================
# 6. LOAD DATA ENGINE
# =====================================================
@st.cache_data
def load_data(url, var):
    ds = xr.open_dataset(url)

    data = ds[var]

    # clip Ethiopia region
    data = data.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean
    data = data.mean(dim=["lat", "lon"])

    df = data.to_dataframe().reset_index()
    return df

# =====================================================
# 7. RUN PIPELINE
# =====================================================
if url:

    st.subheader("📥 Loading CMIP6 Data...")

    df = load_data(url, variable)

    # ensure time column
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # =================================================
    # 8. TIME SELECTION
    # =================================================
    st.subheader("⏱️ Time Selection")

    min_time = df[time_col].min()
    max_time = df[time_col].max()

    start_time, end_time = st.slider(
        "Select Time Range",
        min_value=min_time.to_pydatetime(),
        max_value=max_time.to_pydatetime(),
        value=(min_time.to_pydatetime(), max_time.to_pydatetime())
    )

    df = df[(df[time_col] >= start_time) & (df[time_col] <= end_time)]

    # =================================================
    # 9. PHYSICS LAYER
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400  # mm/day
    elif variable == "tasmax":
        df["value"] = df[variable] - 273.15
    elif variable == "tasmin":
        df["value"] = df[variable] - 273.15

    # =================================================
    # 10. SPI INDEX
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # 11. VISUALIZATION
    # =================================================
    st.subheader("📈 Climate Time Series")

    st.line_chart(df.set_index(time_col)["value"])

    st.subheader("📉 SPI Drought Index")

    st.line_chart(df.set_index(time_col)["SPI"])

    st.subheader("📊 Data Table")

    st.dataframe(df)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Climate Analysis Tool | Streamlit Prototype")
