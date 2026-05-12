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
# LOAD DATA (FIXED TIME)
# =========================
@st.cache_data
def load_data():
    file_path = download_file()

    # 🚨 IMPORTANT FIX: decode_times=False first
    ds = xr.open_dataset(file_path, decode_times=False)

    da = ds["mrso"]

    # convert time manually
    time_var = ds["time"]

    # CMIP6 fix (robust conversion)
    try:
        import cftime
        units = time_var.attrs.get("units", "days since 1850-01-01")
        calendar = time_var.attrs.get("calendar", "noleap")

        times = cftime.num2date(time_var.values, units=units, calendar=calendar)

        da = da.assign_coords(time=times)

    except Exception:
        # fallback (still works)
        da = da.assign_coords(time=pd.to_datetime(time_var.values, errors="coerce"))

    # subset Ethiopia
    da = da.sel(lon=slice(33, 48), lat=slice(3, 15))

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    df = da.to_dataframe().reset_index()

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # 🔥 FORCE FIX: ensure time is valid
    df = df.dropna(subset=["time"])

    df["soil_moisture"] = df["mrso"]
    df["anomaly"] = df["mrso"] - df["mrso"].mean()
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =========================
    # PLOTS
    # =========================
    st.subheader("🌱 Soil Moisture Time Series")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📋 Data")
    st.dataframe(df)
