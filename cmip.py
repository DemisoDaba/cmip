import streamlit as st
import requests

st.title("🌍 Auto CMIP6 Model Discovery")

variable = st.selectbox("Variable", ["pr", "tasmax", "tasmin"])
experiment = st.selectbox("Experiment", ["historical", "ssp245", "ssp585"])

# -----------------------------
# SAFE ESGF SEARCH FUNCTION
# -----------------------------
def get_models(var, exp):
    try:
        url = (
            "https://esgf-node.llnl.gov/esg-search/search/"
            f"?type=Dataset&variable={var}&experiment_id={exp}&format=json&limit=100"
        )

        r = requests.get(url, timeout=10)

        # check if request is valid JSON
        try:
            data = r.json()
        except:
            return ["ESGF returned non-JSON response"]

        # SAFE STRUCTURE CHECK
        if "response" not in data:
            return ["No response from ESGF"]

        if "docs" not in data["response"]:
            return ["No datasets found"]

        models = set()

        for d in data["response"]["docs"]:
            model = d.get("source_id", None)
            if model:
                models.add(model)

        if len(models) == 0:
            return ["No models available"]

        return sorted(list(models))

    except Exception as e:
        return [f"Error: {str(e)}"]

# -----------------------------
# RUN
# -----------------------------
if st.button("🔍 Find Available Models"):
    models = get_models(variable, experiment)

    st.subheader("📦 Auto-Detected CMIP6 Models")
    st.write(models)

    if models and "Error" not in models[0]:
        model = st.selectbox("Select Model", models)
