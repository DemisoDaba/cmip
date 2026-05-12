import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) Dashboard")

# =====================================================
# 1. DATA SOURCE
# =====================================================
URL = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

LOCAL_FILE = "mrso.nc"

# =====================================================
# 2. DOWNLOAD (SAFE)
# =====================================================
def download_file():
    if not os.path.exists(LOCAL_FILE):
        st.info("⬇️ Downloading CMIP6 soil moisture file...")
        r = requests.get(URL, stream=True)
        with open(LOCAL_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return LOCAL_FILE

# =====================================================
# 3. SIDEBAR CONTROLS (RESTORED)
# =====================================================
st.sidebar.header("📍 Ethiopia Region (Lat/Lon)")

min_lon = st.sidebar.number_input("Min Longitude", 33.0)
max_lon = st.sidebar.number_input("Max Longitude", 48.0)
min_lat = st.sidebar.number_input("Min Latitude", 3.0)
max_lat = st.sidebar.number_input("Max Latitude", 15.0)

st.sidebar.header("📅 Time Range")
start_year = st.sidebar.number_input("Start Year", 2014)
end_year = st.sidebar.number_input("End Year", 2020)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 4. LOAD DATA (FIXED CMIP6 TIME)
# =====================================================
@st.cache_data
def load_data():
    file_path = download_file()

    # IMPORTANT: disable auto time decoding
    ds = xr.open_dataset(file_path, decode_times=False)

    da = ds["mrso"]

    # spatial subset
    da = da.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean → time series
    da = da.mean(dim=["lat", "lon"])

    # fix time manually
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

# =====================================================
# 5. RUN
# =====================================================
if st.button("🚀 Load Soil Moisture Analysis"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # clean time
    df = df.dropna(subset=["time"])
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    # time filter
    df = df[(df["time"] >= start_date) & (df["time"] <= end_date)]

    # physics
    df["soil_moisture"] = df["mrso"]
    df["anomaly"] = df["mrso"] - df["mrso"].mean()
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =================================================
    # DASHBOARD LAYOUT
    # =================================================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean Soil Moisture", f"{df['soil_moisture'].mean():.3f}")
    col2.metric("Min", f"{df['soil_moisture'].min():.3f}")
    col3.metric("Max", f"{df['soil_moisture'].max():.3f}")

    st.markdown("---")

    # =================================================
    # TIME SERIES
    # =================================================
    st.subheader("🌱 Soil Moisture Time Series")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index (Drought Signal)")
    st.line_chart(df.set_index("time")["index"])

    # =================================================
    # DATA TABLE
    # =================================================
    st.subheader("📋 Data Table")
    st.dataframe(df)
