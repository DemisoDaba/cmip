import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import cftime

st.set_page_config(page_title="CMIP6 Soil Moisture Ethiopia", layout="wide")

st.title("🌍 CMIP6 Ethiopia Soil Moisture (mrso)")

# =====================================================
# 1. FIXED DATA SOURCE
# =====================================================
url = "http://noresg.nird.sigma2.no/thredds/fileServer/esg_dataroot/cmor/CMIP6/ScenarioMIP/NCC/NorESM2-MM/ssp245/r2i1p1f1/day/mrso/gn/v20200702/mrso_day_NorESM2-MM_ssp245_r2i1p1f1_gn_20141231-20201231.nc"

# =====================================================
# 2. REGION
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", 33.0)
max_lon = st.sidebar.number_input("Max Lon", 48.0)
min_lat = st.sidebar.number_input("Min Lat", 3.0)
max_lat = st.sidebar.number_input("Max Lat", 15.0)

# =====================================================
# 3. SAFE LOADER
# =====================================================
@st.cache_data
def load_data():

    # IMPORTANT: decode_times=False avoids crash
    ds = xr.open_dataset(url, engine="netcdf4", decode_times=False)

    da = ds["mrso"]

    # subset
    da = da.sel(lon=slice(min_lon, max_lon),
                lat=slice(min_lat, max_lat))

    # spatial mean → time series
    da = da.mean(dim=["lat", "lon"])

    df = da.to_dataframe().reset_index()

    return df, ds

# =====================================================
# 4. RUN
# =====================================================
if st.button("🚀 Load Soil Moisture"):

    st.info("🔍 Loading CMIP6 soil moisture (mrso)...")

    df, ds = load_data()

    # =================================================
    # FIX TIME (IMPORTANT PART)
    # =================================================
    time_vals = ds["time"].values

    # convert cftime → pandas safe format
    try:
        df["time"] = pd.to_datetime(time_vals)
    except:
        # fallback: keep numeric index
        df["time"] = np.arange(len(df))

    # rename variable
    df["soil_moisture"] = df["mrso"]

    # anomaly
    df["anomaly"] = df["mrso"] - df["mrso"].mean()

    # standardized index (SPI-like)
    df["index"] = (df["mrso"] - df["mrso"].mean()) / df["mrso"].std()

    # =================================================
    # VISUALS
    # =================================================
    st.subheader("🌱 Soil Moisture Time Series (mrso)")
    st.line_chart(df.set_index("time")["soil_moisture"])

    st.subheader("📉 Soil Moisture Anomaly")
    st.line_chart(df.set_index("time")["anomaly"])

    st.subheader("📊 Standardized Index")
    st.line_chart(df.set_index("time")["index"])

    st.subheader("📋 Data Table")
    st.dataframe(df)
