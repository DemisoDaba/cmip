import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import cftime

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) - STABLE FIXED")

# =====================================================
# 1. FIXED DATA SOURCE
# =====================================================
URL = "http://noresg.nird.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

LOCAL_FILE = "mrso.nc"

# =====================================================
# 2. DOWNLOAD ONCE
# =====================================================
def download_file():
    if not os.path.exists(LOCAL_FILE):
        st.info("⬇️ Downloading CMIP6 file (first run only)...")
        r = requests.get(URL, stream=True)
        with open(LOCAL_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return LOCAL_FILE

# =====================================================
# 3. REGION
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =====================================================
# 4. LOAD DATA (FIXED TIME HANDLING)
# =====================================================
@st.cache_data
def load_data():

    file_path = download_file()

    ds = xr.open_dataset(file_path, decode_times=True)

    da = ds["mrso"]

    # spatial subset
    da = da.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean → time series
    da = da.mean(dim=["lat", "lon"])

    df = da.to_dataframe().reset_index()

    # =================================================
    # 🔥 FIX TIME PROPERLY (CRITICAL FIX)
    # =================================================
    time_var = ds["time"]

    try:
        # normal case
        df["time"] = pd.to_datetime(time_var.values)

    except:

        # CF TIME FIX (IMPORTANT FOR CMIP6)
        units = time_var.attrs.get("units", "days since 1850-01-01")
        calendar = time_var.attrs.get("calendar", "noleap")

        df["time"] = cftime.num2date(
            time_var.values,
            units=units,
            calendar=calendar
        )

        df["time"] = pd.to_datetime(df["time"])

    return df

# =====================================================
# 5. RUN
# =====================================================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # drop bad time values
    df = df.dropna(subset=["time"])

    df["soil_moisture"] = df["mrso"]

    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =================================================
    # VISUALS
    # =================================================
    st.subheader("🌱 Soil Moisture Time Series")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📋 Data Table")
    st.dataframe(df)
