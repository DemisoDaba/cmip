import streamlit as st
import requests

st.set_page_config(page_title="CMIP6 Auto Model Tool", layout="wide")

st.title("🌍 CMIP6 Auto Model Discovery (Stable Version)")

# -----------------------------
# USER INPUT
# -----------------------------
variable = st.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# -----------------------------
# FALLBACK MODEL LIST (IMPORTANT)
# -----------------------------
fallback_models = [
    "MPI-ESM1-2-LR",
    "EC-Earth3",
    "NorESM2-LM",
    "MIROC6",
    "GFDL-ESM4",
    "CNRM-CM6-1",
    "UKESM1-0-LL"
]

# -----------------------------
# ESGF FUNCTION (SAFE)
# -----------------------------
def get_models(var, exp):
    try:
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&format=json&limit=50"
        )

        r = requests.get(url, timeout=10)

        # if server fails
        if r.status_code != 200:
            return fallback_models

        try:
            data = r.json()
        except:
            return fallback_models

        if "response" not in data:
            return fallback_models

        docs = data["response"].get("docs", [])

        models = set()

        for d in docs:
            model = d.get("source_id", None)
            if model:
                models.add(model)

        if len(models) == 0:
            return fallback_models

        return sorted(list(models))

    except:
        return fallback_models

# -----------------------------
# RUN APP
# -----------------------------
if st.button("🔍 Find CMIP6 Models"):
    models = get_models(variable, experiment)

    st.subheader("📦 Available Models")

    st.write(models)

    model = st.selectbox("Select Model", models)

    st.success(f"Selected Model: {model}")

# -----------------------------
# INFO SECTION
# -----------------------------
st.markdown("---")
st.markdown("""
### 🌍 How this works
- First tries live ESGF database  
- If ESGF fails → uses safe fallback models  
- Ensures app never crashes  
""")
