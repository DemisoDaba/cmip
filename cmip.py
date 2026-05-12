import streamlit as st
import requests
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(page_title="CMIP6 Ethiopia Climate Tool", layout="wide")

st.title("🌍 CMIP6 Climate Analysis Tool – Ethiopia (AUTO MODE)")

# =====================================================
# 1. INPUTS
# =====================================================
st.sidebar.header("🧠 Configuration")

variable = st.sidebar.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

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
# 2. GET MODELS (SAFE ESGF)
# =====================================================
def get_models(var, exp):
    try:
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&format=json&limit=30"
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

        return sorted(list(models)) if models else fallback_models

    except:
        return fallback_models

models = get_models(variable, experiment)
model = st.sidebar.selectbox("CMIP6 Model", models)

st.sidebar.success(f"Selected: {model}")

# =====================================================
# 3. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Longitude", value=33.0)
max_lon = st.sidebar.number_input("Max Longitude", value=48.0)
min_lat = st.sidebar.number_input("Min Latitude", value=3.0)
max_lat = st.sidebar.number_input("Max Latitude", value=15.0)

# =====================================================
# 4. AUTO CMIP6 DATA FINDER (IMPORTANT FIX)
# =====================================================
def find_dataset_url(model, variable, experiment):
    try:
        search_url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=File&source_id={model}&variable={variable}"
            f"&experiment_id={experiment}&format=json&limit=1"
        )

        r = requests.get(search_url, timeout=15)
        data = r.json()

        docs = data.get("response", {}).get("docs", [])

        if len(docs) == 0:
            return None

        return docs[0].get("url", None)

    except:
        return None

# =====================================================
# 5. LOAD DATA
# =====================================================
@st.cache_data
def load_data(url, var):
    ds = xr.open_dataset(url)

    data = ds[var]

    # Ethiopia subset
    data = data.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    data = data.mean(dim=["lat", "lon"])

    df = data.to_dataframe().reset_index()
    return df

# =====================================================
# 6. RUN PIPELINE (NO USER URL)
# =====================================================
if st.button("🚀 Run CMIP6 Analysis Automatically"):

    st.info("🔍 Searching CMIP6 dataset...")

    url = find_dataset_url(model, variable, experiment)

    if url is None:
        st.error("❌ No dataset found for selected configuration")
        st.stop()

    st.success("✅ Dataset found!")
    st.code(url)

    df = load_data(url, variable)

    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # =================================================
    # 7. TIME SELECTION
    # =================================================
    st.subheader("⏱️ Time Selection")

    start_time, end_time = st.slider(
        "Select Time Range",
        min_value=df[time_col].min().to_pydatetime(),
        max_value=df[time_col].max().to_pydatetime(),
        value=(df[time_col].min().to_pydatetime(),
               df[time_col].max().to_pydatetime())
    )

    df = df[(df[time_col] >= start_time) & (df[time_col] <= end_time)]

    # =================================================
    # 8. PHYSICS
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400
    else:
        df["value"] = df[variable] - 273.15

    # =================================================
    # 9. SPI INDEX
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # 10. VISUALIZATION
    # =================================================
    st.subheader("📈 Time Series")
    st.line_chart(df.set_index(time_col)["value"])

    st.subheader("📉 SPI Index")
    st.line_chart(df.set_index(time_col)["SPI"])

    st.subheader("📊 Data Table")
    st.dataframe(df)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Climate Tool | Fully Automatic Version")
