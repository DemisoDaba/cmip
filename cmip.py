import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import requests

st.set_page_config(page_title="CMIP6 Ethiopia Tool", layout="wide")
st.title("🌍 CMIP6 Ethiopia Climate Analysis Tool (Stable + Fixed)")

# =====================================================
# 1. INPUTS (ONE VARIABLE ONLY)
# =====================================================
variable = st.sidebar.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# =====================================================
# 2. TIME RANGE
# =====================================================
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.number_input("Start Year", 1990)
end_year = st.sidebar.number_input("End Year", 2000)

start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

# =====================================================
# 3. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =====================================================
# 4. FIXED CMIP6 URL
# =====================================================
def get_url(variable, experiment):
    base = "http://esgf-data.dkrz.de/thredds/dodsC/CMIP6/CMIP/MPI-M/MPI-ESM1-2-LR"

    return (
        f"{base}/{experiment}/r1i1p1f1/day/"
        f"{variable}/gn/v20190710/"
        f"{variable}_day_MPI-ESM1-2-LR_{experiment}_r1i1p1f1_gn_18500101-18691231.nc"
    )

# =====================================================
# 5. SAFE DATA LOADER (IMPORTANT FIX)
# =====================================================
@st.cache_data
def load_data(url, var):

    engines = ["netcdf4", "h5netcdf", None]

    for eng in engines:
        try:
            ds = xr.open_dataset(url, engine=eng)

            data = ds[var]

            # subset Ethiopia
            data = data.sel(
                lon=slice(min_lon, max_lon),
                lat=slice(min_lat, max_lat)
            )

            data = data.mean(dim=["lat", "lon"])

            df = data.to_dataframe().reset_index()

            return df

        except Exception:
            continue

    st.error("❌ Failed to open dataset with all engines (netcdf4/h5netcdf)")
    return None

# =====================================================
# 6. RUN
# =====================================================
if st.button("🚀 Run CMIP6 Analysis"):

    st.info("🔍 Loading CMIP6 dataset...")

    url = get_url(variable, experiment)

    st.code(url)

    df = load_data(url, variable)

    if df is None:
        st.stop()

    # =================================================
    # TIME HANDLING
    # =================================================
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]

    # =================================================
    # PHYSICS
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400
    else:
        df["value"] = df[variable] - 273.15

    # =================================================
    # SPI
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # PLOTS
    # =================================================
    st.subheader("📈 Time Series")
    st.line_chart(df.set_index(time_col)["value"])

    st.subheader("📉 SPI Index")
    st.line_chart(df.set_index(time_col)["SPI"])

    st.subheader("📊 Data Table")
    st.dataframe(df)

st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Tool | Stable OpenDAP Engine Fallback Version")
