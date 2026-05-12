import streamlit as st
import requests
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(page_title="CMIP6 Ethiopia Climate Tool", layout="wide")

st.title("🌍 CMIP6 Climate Analysis Tool – Ethiopia (STABLE VERSION)")

# =====================================================
# 1. INPUTS (ONLY ONE VARIABLE)
# =====================================================
st.sidebar.header("🧠 Configuration")

variable = st.sidebar.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# =====================================================
# 2. TIME SELECTION (BEFORE RUN)
# =====================================================
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.number_input("Start Year", value=1990)
end_year = st.sidebar.number_input("End Year", value=2000)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 3. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Region (Ethiopia)")

min_lon = st.sidebar.number_input("Min Lon", value=33.0)
max_lon = st.sidebar.number_input("Max Lon", value=48.0)
min_lat = st.sidebar.number_input("Min Lat", value=3.0)
max_lat = st.sidebar.number_input("Max Lat", value=15.0)

# =====================================================
# 4. SAFE CMIP6 LINK (FIXED DEMO SOURCE)
# =====================================================
def get_cmip_url(model, variable, experiment):

    base = "http://esgf-data.dkrz.de/thredds/dodsC/CMIP6/CMIP"

    return (
        f"{base}/MPI-M/MPI-ESM1-2-LR/{experiment}/r1i1p1f1/day/"
        f"{variable}/gn/v20190710/"
        f"{variable}_day_MPI-ESM1-2-LR_{experiment}_r1i1p1f1_gn_18500101-18691231.nc"
    )

# =====================================================
# 5. SAFE DATA LOADER (NO CRASH)
# =====================================================
@st.cache_data
def load_data(url, var):
    try:
        # SAFE OPEN (prevents crash)
        ds = xr.open_dataset(url, engine="netcdf4")

        data = ds[var]

        # spatial subset
        data = data.sel(
            lon=slice(min_lon, max_lon),
            lat=slice(min_lat, max_lat)
        )

        data = data.mean(dim=["lat", "lon"])

        df = data.to_dataframe().reset_index()
        return df

    except Exception as e:
        st.error("❌ Failed to load CMIP6 dataset")
        st.code(str(e))
        return None

# =====================================================
# 6. RUN BUTTON
# =====================================================
if st.button("🚀 Run CMIP6 Analysis"):

    st.info("🔍 Loading CMIP6 dataset...")

    url = get_cmip_url("MPI-ESM1-2-LR", variable, experiment)

    st.success("📦 Dataset URL selected")
    st.code(url)

    df = load_data(url, variable)

    # STOP IF FAILED
    if df is None:
        st.stop()

    # =================================================
    # TIME COLUMN
    # =================================================
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # =================================================
    # TIME FILTER (YOUR SELECTED RANGE)
    # =================================================
    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    # =================================================
    # PHYSICS
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400  # kg/m²/s → mm/day
    else:
        df["value"] = df[variable] - 273.15  # Kelvin → Celsius

    # =================================================
    # SPI INDEX
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # VISUALIZATION
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
st.markdown("🌍 CMIP6 Ethiopia Climate Tool | Stable Version (No Crash)")
