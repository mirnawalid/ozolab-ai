import streamlit as st
from src import ui
from src.config import settings

ui.setup("Sample Analysis", "🔬")
ui.hero("1 - Sample Analysis", "What do you have? Everything you type here is user-entered information [E]. Optional fields can stay empty - nothing is guessed for you.")
s = ui.get_sample(); cfg = settings()

mod = st.radio("Which use-case?", ["WASTEWATER", "PULP"], horizontal=True, index=0 if s["module"] == "WASTEWATER" else 1,
               format_func=lambda x: "Laboratory wastewater (the project's use-case)" if x == "WASTEWATER" else "Pulp bleaching (LITERATURE BACKGROUND module - not part of our experiments)")
s["module"] = mod

def opt_number(label, key, default, step, help_=None, fmt="%.2f"):
    on = st.checkbox(f"I have: {label}", value=s.get(key) is not None, key=f"chk_{key}")
    return st.number_input(label, value=float(s.get(key) if s.get(key) is not None else default), step=step, format=fmt, help=help_, key=f"num_{key}") if on else None

c1, c2 = st.columns(2)
with c1:
    st.subheader("Sample")
    s["sample_type"] = st.text_input("Sample type / description", s["sample_type"])
    s["volume_L"] = st.number_input("Sample volume (L) - required", 0.05, 500.0, float(s["volume_L"]), 0.5)
    if mod == "PULP":
        s["consistency_pct"] = st.number_input("Pulp consistency (% solids) - required", 0.1, 40.0, float(s["consistency_pct"]), 0.5,
                                               help="The prototype's hardware cap is set in config/settings.json (assumption).")
        s["initial_L"] = opt_number("Initial L* (CIELAB lightness)", "initial_L", 83.04, 0.1)
    s["pH"] = opt_number("pH (team-stated natural value: 6.3 - enter what you actually measure)", "pH", 6.3, 0.1)
    s["temp"] = opt_number("Temperature (C) (team-stated natural value: 25 - enter what you actually measure)", "temp", 25.0, 0.5)
with c2:
    st.subheader("Measurements you have")
    s["TDS"] = opt_number("TDS (mg/L)", "TDS", 700.0, 10.0, fmt="%.0f")
    s["TSS"] = opt_number("TSS (mg/L)", "TSS", 20.0, 5.0, "Availability of a TSS method is UNKNOWN in the project material.", "%.0f")
    s["COD"] = opt_number("COD (mg/L)", "COD", 500.0, 10.0, "Availability of a COD method is UNKNOWN in the project material.", "%.0f")
    if mod == "WASTEWATER":
        s["abs0"] = opt_number("Absorbance at main peak (spectrophotometer)", "abs0", 0.5, 0.01, fmt="%.3f")
        s["wavelength"] = opt_number("Wavelength of that peak (nm)", "wavelength", 450.0, 5.0, fmt="%.0f")
        s["turbid"] = st.checkbox("Sample is visibly turbid / has suspended solids", s["turbid"])
        s["contaminants"] = st.multiselect("Known contaminant classes (optional)", ["Dye / coloured organics", "Organic solvents", "Heavy metals", "Surfactants", "Unknown"], default=s["contaminants"])
        s["contaminants"] = [x.replace("Dye / coloured organics", "Dye") for x in s["contaminants"]]

st.subheader("Your equipment (optional but makes the recipe quantitative)")
e1, e2 = st.columns(2)
with e1:
    s["ozone_output_mg_h"] = opt_number("Measured ozone generator output (mg O3/h)", "ozone_output_mg_h", 400.0, 10.0,
                                        "Team specification: <= 400 mg/h (unit to be verified on the device label). Above it the recipe is BLOCKED. The poster gives only 15 W.", "%.0f")
    s["air_flow_L_h"] = opt_number("Measured O2/air flow (L/hour)", "air_flow_L_h", 100.0, 5.0, "Team specification: 90-120 L/hour. Outside it the recipe is BLOCKED.", "%.0f")
with e2:
    s["transfer_eff_pct"] = opt_number("Estimated ozone transfer efficiency of the column (%)", "transfer_eff_pct", 50.0, 5.0, "UNKNOWN. Leave unchecked if not measured.", "%.0f")
with st.expander("Hardware inventory read from your photos / poster (edit in config/settings.json)"):
    import pandas as pd
    st.dataframe(pd.DataFrame(cfg["hardware"]), width="stretch", hide_index=True)

st.subheader("Safety confirmations (fixed rules set by humans - the AI works inside them)")
st.caption("If any confirmation is missing, or a value is outside the device specification, the recommendation is BLOCKED and the run must not start. If something becomes unsafe DURING a run: ozone generator off, emergency power cut-off, ventilate, do not resume. This dashboard is not connected to the hardware and cannot do that for you.")
g1, g2 = st.columns(2)
with g1:
    s["ventilation"] = st.checkbox("Work happens in a fume hood / well-ventilated room", s["ventilation"])
    s["offgas"] = st.checkbox("Ozone off-gas is destroyed or safely vented (none visible in the photos)", s["offgas"])
with g2:
    s["estop"] = st.checkbox("There is an emergency stop / quick power cut-off (none visible in the photos)", s["estop"])
    s["ppe"] = st.checkbox("PPE worn and a supervisor is present", s["ppe"])
s["flammable_solvents"] = st.checkbox("Sample contains flammable solvents above trace level", s["flammable_solvents"])
st.session_state["sample"] = s

out, raw = cfg["limits"]["outlet_criteria"], cfg["limits"]["raw_water_criteria"]
st.subheader("Quick check against the poster's criteria")
rows = []
if s["pH"] is not None: rows.append(("pH", s["pH"], f"{raw['pH_min']}-{raw['pH_max']}", raw["pH_min"] <= s["pH"] <= raw["pH_max"]))
if s["temp"] is not None: rows.append(("Temperature (C)", s["temp"], f"<= {raw['temp_max_C']}", s["temp"] <= raw["temp_max_C"]))
if s["TDS"] is not None: rows.append(("TDS (mg/L)", s["TDS"], f"<= {raw['TDS_max_mg_L']}", s["TDS"] <= raw["TDS_max_mg_L"]))
if rows:
    import pandas as pd
    st.dataframe(pd.DataFrame(rows, columns=["Parameter", "Your value [E]", "Raw-water criterion [poster]", "Within?"]), hide_index=True, width="stretch")
st.caption("Poster criteria source not cited on the poster - verify the legal document before relying on them.")
st.success("Saved for this session. Go to **AI Treatment Recommendation**.")
