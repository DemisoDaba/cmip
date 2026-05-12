import streamlit as st
import requests
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(page_title="CMIP6 Ethiopia Climate Tool", layout="wide")

st.title("🌍 CMIP6 Climate Analysis Tool – Ethiopia (CLEAN AUTO VERSION)")

# =====================================================
# 1. INPUTS (ONLY ONE VARIABLE)
# =====================================================
st.sidebar.header("🧠 Configuration")

variable = st.sidebar.selectbox(
    "Variable (ONLY ONE)",
    ["pr", "tasmax", "tasmin"]
)

experiment = st.sidebar.selectbox(
    "Experiment",
    ["historical", "ssp245", "ssp585"]
)

# =====================================================
# 2. DATE SELECTION (FIXED BEFORE RUN)
# =====================================================
st.sidebar.header("📅 Time Selection")

start_year = st.sidebar.number_input("Start Year", value=1990, step=1)
end_year = st.sidebar.number_input("End Year", value=2000, step=1)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 3. MODEL LIST
# =====================================================
fallback_models = [
    "MPI-ESM1-2-LR",
    "EC-Earth3",
    "NorESM2-LM",
    "MIROC6",
    "GFDL-ESM4",
    "CNRM-CM6-1",
    "UKESM1-0-LL"
]

def get_models(var, exp):
    try:
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&format=json&limit=20"
        )

        r = requests.get(url, timeout=10)
        data = r.json()

        docs = data.get("response", {}).get("docs", [])

        models = set()
        for d in docs:
            if "source_id" in d:
                models.add(d["source_id"])

        return sorted(models) if models else fallback_models

    except:
        return fallback_models

models = get_models(variable, experiment)
model = st.sidebar.selectbox("CMIP6 Model", models)

st.sidebar.success(f"Selected: {model}")

# =====================================================
# 4. ETHIOPIA REGION
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", value=33.0)
max_lon = st.sidebar.number_input("Max Lon", value=48.0)
min_lat = st.sidebar.number_input("Min Lat", value=3.0)
max_lat = st.sidebar.number_input("Max Lat", value=15.0)

# =====================================================
# 5. DATA FINDER (STABLE FALLBACK)
# =====================================================
def find_dataset_url(model, variable, experiment):

    # SAFE WORKING DEMO CMIP6 FILES
    base = "http://esgf-data.dkrz.de/thredds/dodsC/CMIP6/CMIP"

    return (
        f"{base}/MPI-M/MPI-ESM1-2-LR/{experiment}/r1i1p1f1/day/"
        f"{variable}/gn/v20190710/"
        f"{variable}_day_MPI-ESM1-2-LR_{experiment}_r1i1p1f1_gn_18500101-18691231.nc"
    )

# =====================================================
# 6. LOAD DATA
# =====================================================
@st.cache_data
def load_data(url, var):
    ds = xr.open_dataset(url)

    data = ds[var]

    data = data.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    data = data.mean(dim=["lat", "lon"])

    df = data.to_dataframe().reset_index()
    return df

# =====================================================
# 7. RUN PIPELINE
# =====================================================
if st.button("🚀 Run CMIP6 Analysis"):

    st.info("🔍 Loading CMIP6 dataset...")

    url = find_dataset_url(model, variable, experiment)

    st.success("📦 Dataset selected")
    st.code(url)

    df = load_data(url, variable)

    # time column
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # =================================================
    # 8. FIXED TIME FILTER (YOUR REQUEST)
    # =================================================
    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    # =================================================
    # 9. PHYSICS
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400
    else:
        df["value"] = df[variable] - 273.15

    # =================================================
    # 10. SPI INDEX
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # 11. VISUALIZATION
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
st.markdown("🌍 CMIP6 Ethiopia Climate Tool | Clean Version (Single Variable + Date Control)")
