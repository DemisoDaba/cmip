import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso)")

# =====================================================
# 1. FIXED CMIP6 URL (DO NOT CHANGE)
# =====================================================
url = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

local_file = "mrso.nc"

# =====================================================
# 2. ETHIOPIA REGION
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =====================================================
# 3. TIME RANGE
# =====================================================
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.number_input("Start Year", 2014)
end_year = st.sidebar.number_input("End Year", 2020)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 4. DOWNLOAD + LOAD (FIX)
# =====================================================
@st.cache_data
def load_data():

    # -----------------------------
    # 1. DOWNLOAD IF NOT EXISTS
    # -----------------------------
    if not os.path.exists(local_file):
        st.info("⬇️ Downloading CMIP6 NetCDF file...")
        os.system(f"wget -O {local_file} '{url}'")

    # -----------------------------
    # 2. OPEN LOCAL FILE (SAFE)
    # -----------------------------
    ds = xr.open_dataset(local_file, decode_times=True)

    data = ds["mrso"]

    # -----------------------------
    # 3. SPATIAL SUBSET
    # -----------------------------
    data = data.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean → time series
    data = data.mean(dim=["lat", "lon"])

    df = data.to_dataframe().reset_index()

    return df

# =====================================================
# 5. RUN
# =====================================================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # -----------------------------
    # TIME FILTER
    # -----------------------------
    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    # -----------------------------
    # ANALYSIS
    # -----------------------------
    df["soil_moisture"] = df["mrso"]

    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # -----------------------------
    # PLOTS
    # -----------------------------
    st.subheader("🌱 Soil Moisture Time Series (mrso)")
    st.line_chart(df.set_index(time_col)["soil_moisture"])

    st.subheader("📉 Soil Moisture Anomaly")
    st.line_chart(df.set_index(time_col)["anomaly"])

    st.subheader("📊 Standardized Index (Drought Signal)")
    st.line_chart(df.set_index(time_col)["index"])

    st.subheader("📋 Data Table")
    st.dataframe(df)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Soil Moisture Tool | Local NetCDF Mode (Stable)")
