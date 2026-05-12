import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import os
import requests
import cftime

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso) - CORRECT INTERPRETATION")

# =========================
# DATA SOURCE
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
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    return LOCAL_FILE

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():

    file_path = download_file()

    ds = xr.open_dataset(file_path, decode_times=False)

    da = ds["mrso"]

    # Ethiopia subset
    da = da.sel(lon=slice(33, 48),
                lat=slice(3, 15))

    # spatial mean
    da = da.mean(dim=["lat", "lon"])

    # =========================
    # FIX TIME PROPERLY (CMIP6 SAFE)
    # =========================
    time_var = ds["time"]

    units = time_var.attrs.get("units", "days since 1850-01-01")
    calendar = time_var.attrs.get("calendar", "noleap")

    times = cftime.num2date(
        time_var.values,
        units=units,
        calendar=calendar
    )

    da = da.assign_coords(time=times)

    df = da.to_dataframe().reset_index()

    # force clean datetime
    df["time"] = pd.to_datetime(df["time"])

    return df

# =========================
# RUN
# =========================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Processing CMIP6 soil moisture (mrso)...")

    df = load_data()

    # clean
    df = df.dropna(subset=["time"])

    # =========================
    # CORRECT PHYSICAL INTERPRETATION
    # =========================

    # raw CMIP6 unit: kg/m² = mm water equivalent
    df["soil_moisture_mm"] = df["mrso"]

    # convert to meters (clear interpretation)
    df["soil_moisture_m"] = df["mrso"] / 1000

    # =========================
    # CLIMATOLOGY ANOMALY (REAL SCIENCE)
    # =========================
    clim = df.groupby(df["time"].dt.month)["mrso"].mean()
    df["climatology"] = df["time"].dt.month.map(clim)

    df["anomaly"] = df["mrso"] - df["climatology"]

    # =========================
    # STANDARDIZED SOIL MOISTURE INDEX (SSI)
    # =========================
    mean = df["mrso"].mean()
    std = df["mrso"].std()

    df["ssi"] = (df["mrso"] - mean) / std

    # =========================
    # DROUGHT CLASSIFICATION
    # =========================
    def classify(x):
        if x <= -2:
            return "Extreme Drought"
        elif x <= -1:
            return "Moderate Drought"
        elif x < 1:
            return "Normal"
        elif x < 2:
            return "Wet"
        else:
            return "Very Wet"

    df["condition"] = df["ssi"].apply(classify)

    # =========================
    # SMOOTHED STRESS
    # =========================
    df["stress_index"] = df["ssi"].rolling(7).mean()

    # =========================
    # DASHBOARD
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Mean (mm)", f"{df['soil_moisture_mm'].mean():.1f}")
    col2.metric("Min", f"{df['soil_moisture_mm'].min():.1f}")
    col3.metric("Max", f"{df['soil_moisture_mm'].max():.1f}")

    # =========================
    # TIME DEBUG (IMPORTANT)
    # =========================
    st.write("🕒 Time check (first 10 rows)")
    st.dataframe(df[["time", "mrso"]].head(10))

    # =========================
    # PLOTS
    # =========================
    st.subheader("🌱 Soil Moisture (mm water equivalent)")
    st.line_chart(df.set_index("time")["soil_moisture_mm"])

    st.subheader("📉 Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Soil Moisture Index (SSI)")
    st.line_chart(df.set_index("time")["ssi"])

    st.subheader("🌾 Agricultural Stress (smoothed)")
    st.line_chart(df.set_index("time")["stress_index"])

    # =========================
    # DROUGHT TABLE
    # =========================
    st.subheader("📊 Drought Classification")
    st.dataframe(df[["time", "mrso", "ssi", "condition"]])

    # =========================
    # DOWNLOAD
    # =========================
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="cmip6_mrso_ethiopia.csv",
        mime="text/csv"
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Soil Moisture Tool | Correct CMIP6 Interpretation")
