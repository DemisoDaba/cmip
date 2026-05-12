import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) - FIXED + DASHBOARD")

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
# SIDEBAR CONTROLS
# =========================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =========================
# MAP VIEW (NEW)
# =========================
st.subheader("🗺️ Selected Region Map")

m = folium.Map(location=[8.5, 40], zoom_start=5)

folium.Rectangle(
    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    color="blue",
    fill=True,
    fill_opacity=0.2
).add_to(m)

st_folium(m, width=700, height=400)

# =========================
# LOAD DATA (FIXED TIME)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    ds = xr.open_dataset(file_path, decode_times=False)

    da = ds["mrso"]

    # subset
    da = da.sel(lon=slice(min_lon, max_lon),
                lat=slice(min_lat, max_lat))

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    time_var = ds["time"]

    import cftime
    units = time_var.attrs.get("units", "days since 1850-01-01")
    calendar = time_var.attrs.get("calendar", "noleap")

    try:
        times = cftime.num2date(time_var.values, units=units, calendar=calendar)
        da = da.assign_coords(time=times)
    except:
        da = da.assign_coords(time=pd.to_datetime(time_var.values, errors="coerce"))

    df = da.to_dataframe().reset_index()

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # clean
    df = df.dropna(subset=["time"])

    df["soil_moisture"] = df["mrso"]
    df["anomaly"] = df["mrso"] - df["mrso"].mean()
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =========================
    # DASHBOARD METRICS (NEW)
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean Soil Moisture", f"{df['soil_moisture'].mean():.3f}")
    col2.metric("Min", f"{df['soil_moisture'].min():.3f}")
    col3.metric("Max", f"{df['soil_moisture'].max():.3f}")

    # =========================
    # SMOOTHED DROUGHT SIGNAL (NEW)
    # =========================
    df["rolling_index"] = df["index"].rolling(7).mean()

    # =========================
    # PLOTS
    # =========================
    st.subheader("🌱 Soil Moisture Time Series")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📉 Smoothed Drought Signal (7-day)")
    st.line_chart(df.set_index("time")["rolling_index"])

    # =========================
    # DOWNLOAD (NEW)
    # =========================
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="mrso_ethiopia.csv",
        mime="text/csv"
    )

    # =========================
    # TABLE
    # =========================
    st.subheader("📋 Data")
    st.dataframe(df)
