#Import libraries
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (%) - NORMALIZED")

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
# MAP
# =========================
st.subheader("🗺️ Region")

m = folium.Map(location=[8.5, 40], zoom_start=5)

folium.Rectangle(
    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    color="blue",
    fill=True,
    fill_opacity=0.2
).add_to(m)

st_folium(m, width=700, height=400)

# =========================
# LOAD DATA (FIXED)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    # FIX TIME DECODING
    ds = xr.open_dataset(file_path, decode_times=True, use_cftime=True)

    da = ds["mrso"]

    # =========================
    # FIX LONGITUDE (0–360 → -180–180)
    # =========================
    if da.lon.max() > 180:
        da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180))
        da = da.sortby("lon")

    # =========================
    # FIX LAT ORDER
    # =========================
    if da.lat[0] > da.lat[-1]:
        da = da.sortby("lat")

    # =========================
    # SUBSET REGION
    # =========================
    da = da.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    df = da.to_dataframe().reset_index()

    # clean time
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture %"):

    st.info("Processing CMIP6 soil moisture...")

    df = load_data()

    # =========================
    # SORT TIME (IMPORTANT)
    # =========================
    df = df.sort_values("time")

    # =========================
    # NORMALIZATION
    # =========================
    vmin = df["mrso"].min()
    vmax = df["mrso"].max()

    df["soil_moisture_pct"] = (df["mrso"] - vmin) / (vmax - vmin) * 100

    df["anomaly"] = df["soil_moisture_pct"] - df["soil_moisture_pct"].mean()

    df["index"] = (
        df["soil_moisture_pct"] - df["soil_moisture_pct"].mean()
    ) / df["soil_moisture_pct"].std()

    # =========================
    # TIME AS INDEX (KEY FIX)
    # =========================
    df = df.set_index("time")

    # =========================
    # METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean Soil Moisture %", f"{df['soil_moisture_pct'].mean():.2f}%")
    col2.metric("Min %", f"{df['soil_moisture_pct'].min():.2f}%")
    col3.metric("Max %", f"{df['soil_moisture_pct'].max():.2f}%")

    # =========================
    # TIME SERIES PLOTS (FIXED X-AXIS)
    # =========================
    st.subheader("🌱 Soil Moisture (%)")
    st.line_chart(df["soil_moisture_pct"])

    st.subheader("📉 Anomaly (%)")
    st.line_chart(df["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df["index"])

    # =========================
    # DATA VIEW
    # =========================
    st.subheader("📋 Data")
    st.dataframe(df.reset_index())
