import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (%) - FIXED TIME STABLE")

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
# SIDEBAR REGION
# =========================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =========================
# MAP (optional visual only)
# =========================
st.subheader("🗺️ Selected Region")

m = folium.Map(location=[8.5, 40], zoom_start=5)

folium.Rectangle(
    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    color="blue",
    fill=True,
    fill_opacity=0.2
).add_to(m)

st_folium(m, width=700, height=400)

# =========================
# LOAD DATA (FIXED TIME SAFE)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    # decode_times=True lets xarray handle CMIP6 time properly
    ds = xr.open_dataset(file_path, decode_times=True)

    da = ds["mrso"]

    # subset Ethiopia
    da = da.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    # convert to dataframe
    df = da.to_dataframe().reset_index()

    # SAFE TIME FIX (critical)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("Processing CMIP6 soil moisture...")

    df = load_data()

    # clean bad time rows
    df = df.dropna(subset=["time"])

    # =========================
    # PHYSICAL CONVERSION
    # =========================
    mrso = df["mrso"]

    # convert to pseudo %
    df["soil_moisture_pct"] = (mrso / 1000.0) * 100
    df["soil_moisture_pct"] = df["soil_moisture_pct"].clip(0, 100)

    # =========================
    # ANOMALY + INDEX
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
    # TIME SERIES (FIXED X = TIME)
    # =========================
    st.subheader("🌱 Soil Moisture Time Series (%)")
    st.line_chart(df.set_index("time")["soil_moisture_pct"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    # =========================
    # TABLE
    # =========================
    st.subheader("📋 Data")
    st.dataframe(df)
