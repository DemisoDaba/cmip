import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np

st.set_page_config(page_title="CMIP6 Ethiopia Tool", layout="wide")

st.title("🌍 CMIP6 Ethiopia Climate Analysis Tool (Stable)")

# =====================================================
# 1. INPUTS
# =====================================================
st.sidebar.header("🧠 Configuration")

variable = st.sidebar.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.sidebar.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# =====================================================
# 2. TIME INPUT (EASIER VERSION)
# =====================================================
st.sidebar.header("📅 Time Range")

start_year = st.sidebar.slider("Start Year", 1850, 2100, 1990)
end_year = st.sidebar.slider("End Year", 1850, 2100, 2000)

# =====================================================
# 3. ETHIOPIA BOUNDING BOX
# =====================================================
st.sidebar.header("📍 Ethiopia Region")

min_lon = st.sidebar.number_input("Min Lon", value=33.0)
max_lon = st.sidebar.number_input("Max Lon", value=48.0)
min_lat = st.sidebar.number_input("Min Lat", value=3.0)
max_lat = st.sidebar.number_input("Max Lat", value=15.0)

# =====================================================
# 4. CMIP6 URL BUILDER (SAFE TEMPLATE)
# =====================================================
def build_url(variable, experiment):

    model = "MPI-ESM1-2-LR"

    return (
        f"http://esgf-data.dkrz.de/thredds/dodsC/CMIP6/CMIP/MPI-M/"
        f"{model}/{experiment}/r1i1p1f1/day/"
        f"{variable}/gn/v20190710/"
        f"{variable}_day_{model}_{experiment}_r1i1p1f1_gn_18500101-18691231.nc"
    )

# =====================================================
# 5. SAFE LOADER
# =====================================================
@st.cache_data
def load_data(url, var):

    try:
        ds = xr.open_dataset(url, engine="netcdf4", decode_times=True)

        data = ds[var]

        # Ethiopia subset
        data = data.sel(
            lon=slice(min_lon, max_lon),
            lat=slice(min_lat, max_lat)
        )

        # spatial mean → time series
        data = data.mean(dim=["lat", "lon"])

        df = data.to_dataframe().reset_index()

        return df

    except Exception as e:
        st.error("❌ Failed to load CMIP6 dataset")
        st.code(str(e))
        return None

# =====================================================
# 6. RUN
# =====================================================
if st.button("🚀 Run CMIP6 Analysis"):

    st.info("🔍 Loading CMIP6 dataset...")

    url = build_url(variable, experiment)

    st.success("📦 Dataset URL generated")
    st.code(url)

    df = load_data(url, variable)

    if df is None:
        st.stop()

    # =================================================
    # TIME COLUMN FIX
    # =================================================
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # =================================================
    # FILTER TIME (YEAR BASED - SAFE)
    # =================================================
    df = df[
        (df[time_col].dt.year >= start_year) &
        (df[time_col].dt.year <= end_year)
    ]

    # =================================================
    # PHYSICS CONVERSION
    # =================================================
    if variable == "pr":
        df["value"] = df[variable] * 86400  # kg/m²/s → mm/day
        y_label = "Precipitation (mm/day)"
    else:
        df["value"] = df[variable] - 273.15  # Kelvin → Celsius
        y_label = "Temperature (°C)"

    # =================================================
    # SPI (SIMPLE VERSION)
    # =================================================
    df["SPI"] = (df[variable] - df[variable].mean()) / df[variable].std()

    # =================================================
    # PLOT
    # =================================================
    st.subheader("📈 Time Series")

    st.line_chart(df.set_index(time_col)["value"])

    st.subheader("📉 SPI Index")

    st.line_chart(df.set_index(time_col)["SPI"])

    st.subheader("📊 Data Table")

    st.dataframe(df)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown("🌍 CMIP6 Ethiopia Tool | Stable One-Variable Version")
