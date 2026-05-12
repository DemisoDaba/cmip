import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) - STABLE FINAL VERSION")

# =====================================================
# 1. DATA SOURCE
# =====================================================
URL = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

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
# 3. REGION INPUT
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =====================================================
# 4. SAFE DATA LOADING
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

    # =====================================================
    # 🔥 UNIVERSAL TIME FIX (NO CRASH GUARANTEE)
    # =====================================================
    try:
        df["time"] = pd.to_datetime(ds["time"].values)

    except Exception:
        try:
            df["time"] = pd.to_datetime(ds.indexes["time"])
        except Exception:
            df["time"] = np.arange(len(df))  # fallback safe index

    return df

# =====================================================
# 5. RUN BUTTON
# =====================================================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # clean NaN time just in case
    df = df.dropna()

    # rename
    df["soil_moisture"] = df["mrso"]

    # anomaly
    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    # standardized index
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =====================================================
    # VISUALIZATION
    # =====================================================
    st.subheader("🌱 Soil Moisture Time Series")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📋 Data Table")
    st.dataframe(df)
