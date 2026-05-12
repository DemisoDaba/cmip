import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso)")

# -----------------------------
# CMIP6 FILE
# -----------------------------
URL = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

LOCAL_FILE = "mrso.nc"

# -----------------------------
# REGION
# -----------------------------
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# -----------------------------
# TIME
# -----------------------------
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.number_input("Start Year", 2014)
end_year = st.sidebar.number_input("End Year", 2020)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# -----------------------------
# SAFE DOWNLOAD FUNCTION
# -----------------------------
def download_file(url, out_path):

    if os.path.exists(out_path):
        return True

    try:
        st.info("⬇️ Downloading CMIP6 file (first run only)...")

        r = requests.get(url, stream=True, timeout=60)

        if r.status_code != 200:
            st.error(f"Download failed HTTP {r.status_code}")
            return False

        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        return os.path.exists(out_path)

    except Exception as e:
        st.error("Download error")
        st.code(str(e))
        return False

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():

    ok = download_file(URL, LOCAL_FILE)

    if not ok:
        return None

    try:
        ds = xr.open_dataset(LOCAL_FILE, decode_times=True)
        da = ds["mrso"]

        da = da.sel(
            lon=slice(min_lon, max_lon),
            lat=slice(min_lat, max_lat)
        )

        da = da.mean(dim=["lat", "lon"])

        df = da.to_dataframe().reset_index()
        return df

    except Exception as e:
        st.error("❌ NetCDF open failed")
        st.code(str(e))
        return None

# -----------------------------
# RUN
# -----------------------------
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    if df is None:
        st.stop()

    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    df["soil_moisture"] = df["mrso"]
    df["anomaly"] = df["mrso"] - df["mrso"].mean()
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    st.subheader("🌱 Soil Moisture")
    st.line_chart(df.set_index(time_col)["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index(time_col)["anomaly"])

    st.subheader("📊 Index")
    st.line_chart(df.set_index(time_col)["index"])

    st.subheader("📋 Data")
    st.dataframe(df)

st.markdown("---")
st.markdown("🌍 CMIP6 Soil Moisture Tool | Stable Download Version")
