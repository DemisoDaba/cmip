import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) - FIXED TIME")

# =========================
# DATA URL
# =========================
URL = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

LOCAL_FILE = "mrso.nc"

# =========================
# DOWNLOAD
# =========================
def download_file():
    if not os.path.exists(LOCAL_FILE):
        st.info("⬇️ Downloading CMIP6 file...")
        r = requests.get(URL, stream=True)
        with open(LOCAL_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return LOCAL_FILE

# =========================
# SIDEBAR
# =========================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =========================
# LOAD DATA (CORRECT FIX)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    # 🔥 IMPORTANT FIX: decode_times=True (NO manual time hack)
    ds = xr.open_dataset(file_path, decode_times=True)

    da = ds["mrso"]

    # subset first
    da = da.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    # convert to dataframe
    df = da.to_dataframe().reset_index()

    # ensure proper datetime
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    df = df.dropna(subset=["time"])

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # sort time (VERY IMPORTANT)
    df = df.sort_values("time")

    # =========================
    # REAL VALUES
    # =========================
    df["soil_moisture"] = df["mrso"]

    # anomaly (correct)
    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    # standardized index
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =========================
    # OPTIONAL: NORMALIZED %
    # =========================
    df["soil_moisture_pct"] = (
        (df["mrso"] - df["mrso"].min()) /
        (df["mrso"].max() - df["mrso"].min())
    ) * 100

    # =========================
    # METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean (kg/m²)", f"{df['soil_moisture'].mean():.2f}")
    col2.metric("Min", f"{df['soil_moisture'].min():.2f}")
    col3.metric("Max", f"{df['soil_moisture'].max():.2f}")

    # =========================
    # TIME SERIES (CORRECT)
    # =========================
    st.subheader("🌱 Soil Moisture (Raw)")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📊 Soil Moisture (%) Normalized")
    st.line_chart(df.set_index("time")["soil_moisture_pct"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    # =========================
    # DATA TABLE
    # =========================
    st.subheader("📋 Data")
    st.dataframe(df)
