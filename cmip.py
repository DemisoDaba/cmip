import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (%) - PHYSICAL VERSION")

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
# REGION
# =========================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =========================
# LOAD DATA (FIXED TIME)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    ds = xr.open_dataset(file_path, decode_times=True)

    da = ds["mrso"]

    # subset Ethiopia
    da = da.sel(lon=slice(min_lon, max_lon),
                lat=slice(min_lat, max_lat))

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    df = da.to_dataframe().reset_index()

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("Processing CMIP6 soil moisture...")

    df = load_data()

    # =========================
    # FIX TIME
    # =========================
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna(subset=["time"])

    # =========================
    # 🔥 PHYSICAL CONVERSION TO %
    # =========================
    mrso = df["mrso"]

    df["soil_moisture_pct"] = (mrso / 1000.0) * 100   # kg/m² → %

    # clamp (0–100)
    df["soil_moisture_pct"] = df["soil_moisture_pct"].clip(0, 100)

    # =========================
    # ANOMALY & INDEX
    # =========================
    df["anomaly"] = df["soil_moisture_pct"] - df["soil_moisture_pct"].mean()

    df["index"] = (
        df["soil_moisture_pct"] - df["soil_moisture_pct"].mean()
    ) / df["soil_moisture_pct"].std()

    # =========================
    # METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean Soil Moisture %", f"{df['soil_moisture_pct'].mean():.2f}%")
    col2.metric("Min %", f"{df['soil_moisture_pct'].min():.2f}%")
    col3.metric("Max %", f"{df['soil_moisture_pct'].max():.2f}%")

    # =========================
    # TIME SERIES (CORRECT)
    # =========================
    st.subheader("🌱 Soil Moisture (%) Over Time")
    st.line_chart(df.set_index("time")["soil_moisture_pct"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📋 Data")
    st.dataframe(df)
