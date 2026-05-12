import streamlit as st
import requests

st.title("🌍 Auto CMIP6 Model Discovery")

variable = st.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# -----------------------------
# ESGF SEARCH FUNCTION
# -----------------------------
def get_models(var, exp):
    try:
        # ESGF search API (public endpoint)
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&limit=1000&format=json"
        )

        r = requests.get(url)
        data = r.json()

        models = set()

        for d in data["response"]["docs"]:
            if "source_id" in d:
                models.add(d["source_id"])

        return sorted(list(models))

    except Exception as e:
        return [f"Error: {e}"]

# -----------------------------
# RUN
# -----------------------------
if st.button("🔍 Find Available Models"):
    models = get_models(variable, experiment)

    st.subheader("📦 Auto-Detected CMIP6 Models")
    st.write(models)

    model = st.selectbox("Select Model", models)
