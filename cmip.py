import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np

st.set_page_config(page_title="Auto CMIP6 Ethiopia Tool", layout="wide")

st.title("🌍 AUTOMATIC CMIP6 Climate Tool – Ethiopia")

# =====================================================
# 1. USER INPUTS (NO URL ANYMORE)
# =====================================================
model = st.selectbox("CMIP6 Model", [
    "MPI-ESM1-2-LR",
    "EC-Earth3",
    "NorESM2-LM",
    "MIROC6"
])

experiment = st.selectbox("Scenario", ["historical", "ssp245", "ssp585"])
variable = st.selectbox("Variable", ["pr", "tasmax", "tasmin"])

# Ethiopia bounding box
min_lon, max_lon = 33, 48
min_lat, max_lat = 3, 15

st.info("📍 Ethiopia region is fixed for this version")

# =====================================================
# 2. AUTO CMIP6 URL BUILDER (CORE MAGIC)
# =====================================================
def build_url(model, experiment, variable):
    # SIMPLE TEMPLATE (works for many CMIP6 datasets)
    base = "http://esgf-data.dkrz.de/thredds/dodsC/CMIP6/CMIP"

    url = f"{base}/{model}/{experiment}/r1i1p1f1/day/{variable}/gn/latest/latest.nc"
    return url

# =====================================================
# 3. LOAD DATA
# =====================================================
@st.cache_data
def load_data(url, var):
    ds = xr.open_dataset(url)

    data = ds[var]

    # clip Ethiopia
    data = data.sel(
        lon=slice(min_lon, max_lon),
        lat=slice(min_lat, max_lat)
    )

    # spatial mean
    data = data.mean(dim=["lat", "lon"])

    df = data.to_dataframe().reset_index()
    return df

# =====================================================
# 4. RUN PIPELINE
# =====================================================
if st.button("🚀 Run CMIP6 Analysis Automatically"):

    url = build_url(model, experiment, variable)

    st.write("🔗 Auto-generated URL:")
    st.code(url)

    try:
        df = load_data(url, variable)

        time_col = df.columns[0]
        df[time_col] = pd.to_datetime(df[time_col])

        # -----------------------------
        # TIME SERIES PLOT
        # -----------------------------
        st.subheader("📈 Time Series")

        if variable == "pr":
            df["value"] = df[variable] * 86400
        else:
            df["value"] = df[variable] - 273.15

        st.line_chart(df.set_index(time_col)["value"])

        # -----------------------------
        # SPI INDEX
        # -----------------------------
        df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

        st.subheader("📉 SPI Index")
        st.line_chart(df.set_index(time_col)["SPI"])

        st.success("✅ Analysis Complete")

    except Exception as e:
        st.error("❌ Data loading failed (CMIP6 file not found or URL invalid)")
        st.write(str(e))
