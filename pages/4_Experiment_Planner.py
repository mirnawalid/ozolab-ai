import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src import ui
from src.experiment_planner import plan_bleach, plan_wastewater
from src.prediction import predict_bleach
from src.records import get_own

ui.setup("Experiment Planner", "🎯")
ui.hero("4 - Experiment Planner", "Active learning: which experiment should the team run NEXT to learn the most? Transparent rule, not a black box.")
s = ui.get_sample(); bl = ui.bleach_bundle(); own = get_own()
tab_w, tab_p = st.tabs(["Laboratory wastewater (the poster's use-case)", "Pulp bleaching"])

with tab_w:
    k = st.slider("How many experiments to propose", 3, 10, 5)
    plan = plan_wastewater(own, s["volume_L"], k)
    n_ww = int((own["Module"] == "WASTEWATER").sum()) if len(own) else 0
    st.markdown(f"Your own wastewater records so far: **{n_ww}** (software setting: the app fits a model on our own runs only after {ui.own_ww_model()['needed']} runs - a developer-chosen minimum, NOT from a paper and NOT experiments we performed).")
    st.dataframe(plan.round(2), hide_index=True, width="stretch")
    st.markdown("**Logic:** (1) run the reference dose 3 times at the sample's natural pH and temperature to measure run-to-run noise; (2) then vary the treatment DURATION, choosing points farthest from all existing runs inside the human-defined bounds (maximin space-filling). pH and temperature are not varied unless enabled in config/settings.json. Bounds are in `config/settings.json` and are **not validated optima**.")
    st.markdown("**Measure for every run (BEFORE and AFTER, same instruments):** spectrophotometer scan + absorbance at the peak wavelength, pH, TDS, temperature; COD/TSS only if you have a method; plus 4-5 intermediate samples for the kinetic curve. Record the ozonizer dial position and, if possible, its output in mg/h. Then log it in **Experiment History**.")
    st.caption("Expected outcome: UNKNOWN until a model exists - this is exactly why these runs are proposed. Model uncertainty is currently total for this module.")
    if len(plan):
        fig = px.scatter(plan.dropna(subset=["pH"]), x="Duration_multiplier", y="pH", color="Run_type", size_max=14, title="Proposed design points (anchor runs use native pH)")
        st.plotly_chart(fig, width="stretch")

with tab_p:
    r = bl["ranges"]
    c1, c2, c3, c4 = st.columns(4)
    pHr = c1.slider("pH window", float(r["pH"][0]), float(r["pH"][1]), (2.0, 9.6)); Tr = c2.slider("Temperature window (C)", 20, 40, (20, 40))
    o3max = c3.number_input("Max ozone consumed (% o.d. pulp)", 0.1, float(r["O3_Consumed_pct_odp"][1]), 1.0, 0.1)
    w_unc = c4.slider("Weight on model uncertainty (rest = distance from data)", 0.0, 1.0, 0.5, 0.1)
    b = dict(pH_min=pHr[0], pH_max=pHr[1], T_min=Tr[0], T_max=Tr[1], o3_max=o3max)
    pl = plan_bleach(bl, b, 3, w_unc)
    if pl.empty: st.warning("No non-RED candidate inside the chosen window."); st.stop()
    for i, row in pl.iterrows():
        p = predict_bleach(bl, row.pH, row.Temp_C, row.O3_Consumed_pct_odp)
        with st.container(border=True):
            st.markdown(f"**Proposed experiment {i + 1}:** pH **{row.pH:g}**, **{row.Temp_C:g} C**, ozone consumed **{row.O3_Consumed_pct_odp:.2f} % o.d. pulp** {ui.pill(row.envelope)}", unsafe_allow_html=True)
            st.write(f"Expected (model, [C]): L* {p['L_star']['value']:.1f} ({p['L_star']['low']:.1f} to {p['L_star']['high']:.1f}), DP {p['DP']['value']:.0f} ({p['DP']['low']:.0f} to {p['DP']['high']:.0f}). Model ensemble spread: L* {row.L_star_std:.2f}, DP {row.DP_std:.0f}.")
            st.caption("Why: " + row.why)
            st.caption("Measure afterwards: L*a*b* (or ISO brightness), DP/viscosity, final pH, ozone actually consumed. Log it in Experiment History.")
    X = bl["X_all"].copy(); X["kind"] = bl["origin"].values
    pts = pl[["pH", "Temp_C", "O3_Consumed_pct_odp"]].assign(kind="PROPOSED")
    fig = px.scatter(pd.concat([X, pts]), x="O3_Consumed_pct_odp", y="pH", color="kind", symbol="Temp_C", title="Existing data vs proposed experiments", labels={"O3_Consumed_pct_odp": "Ozone consumed (% o.d. pulp)"})
    st.plotly_chart(fig, width="stretch")
