import streamlit as st
import requests
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(page_title="CMIP6 Ethiopia Soil Moisture Tool", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture Analysis (mrso)")

# =====================================================
# 1. INPUTS
# =====================================================
st.sidebar.header("🧠 Configuration")

# ONLY SOIL MOISTURE NOW
variable = "mrso"
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# =====================================================
# 2. TIME RANGE
# =====================================================
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.number_input("Start Year", value=1990)
end_year = st.sidebar.number_input("End Year", value=2000)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 3. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Region (Ethiopia)")

min_lon = st.sidebar.number_input("Min Lon", value=33.0)
max_lon = st.sidebar.number_input("Max Lon", value=48.0)
min_lat = st.sidebar.number_input("Min Lat", value=3.0)
max_lat = st.sidebar.number_input("Max Lat", value=15.0)

# =====================================================
# 4. SAFE SOIL MOISTURE URL
# =====================================================
def get_cmip_url(experiment):

    base = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6"

    return (
        f"{base}/ScenarioMIP/NCC/NorESM2-MM/{experiment}/r2i1p1f1/day/"
        f"mrso/gn/v20200702/"
        f"mrso_day_NorESM2-MM_{experiment}_r2i1p1f1_gn_20141231-20201231.nc"
    )

# =====================================================
# 5. SAFE LOADER
# =====================================================
@st.cache_data
def load_data(url):

    try:
        ds = xr.open_dataset(url)

        data = ds["mrso"]

        # subset Ethiopia
        data = data.sel(
            lon=slice(min_lon, max_lon),
            lat=slice(min_lat, max_lat)
        )

        # spatial average → time series
        data = data.mean(dim=["lat", "lon"])

        df = data.to_dataframe().reset_index()

        return df

    except Exception as e:
        st.error("❌ Failed to load soil moisture dataset")
        st.code(str(e))
        return None

# =====================================================
# 6. RUN
# =====================================================
if st.button("🚀 Run Soil Moisture Analysis"):

    st.info("🔍 Loading CMIP6 soil moisture (mrso)...")

    url = get_cmip_url(experiment)

    st.code(url)

    df = load_data(url)

    if df is None:
        st.stop()

    # =================================================
    # TIME HANDLING
    # =================================================
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    # =================================================
    # UNIT (optional normalization)
    # =================================================
    df["soil_moisture"] = df["mrso"]

    # =================================================
    # ANOMALY (IMPORTANT FOR DROUGHT)
    # =================================================
    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    df["SPI_like"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =================================================
    # VISUALIZATION
    # =================================================
    st.subheader("🌱 Soil Moisture Time Series (mrso)")
    st.line_chart(df.set_index(time_col)["soil_moisture"])

    st.subheader("📉 Soil Moisture Anomaly")
    st.line_chart(df.set_index(time_col)["anomaly"])

    st.subheader("📊 Standardized Index (SPI-like)")
    st.line_chart(df.set_index(time_col)["SPI_like"])

    st.subheader("📋 Data Table")
    st.dataframe(df)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Soil Moisture Tool | mrso-based drought monitoring")
