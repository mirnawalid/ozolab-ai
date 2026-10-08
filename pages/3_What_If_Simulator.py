import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src import ui
from src.config import P1_BASELINE, settings
from src.prediction import predict_bleach, predict_bleach_grid
from src.recommendation_engine import DEFAULT_WEIGHTS, energy_kwh, ozone_mass_plan
from src.training import BLEACH_FEATURES

ui.setup("What-if Simulator", "🔀")
ui.hero("3 - What-if Simulator", "Compare treatment scenarios side by side. Every predicted number is a MODEL PREDICTION [C]; the suitability score is transparent and editable.")
s = ui.get_sample(); bl = ui.bleach_bundle(); r = bl["ranges"]
tab_p, tab_w = st.tabs(["Pulp bleaching (literature model)", "Laboratory wastewater (duration scenarios)"])

with tab_p:
    st.caption(f"Model range: pH {r['pH'][0]:g}-{r['pH'][1]:g}, T {r['Temp_C'][0]:g}-{r['Temp_C'][1]:g} C, ozone consumed {r['O3_Consumed_pct_odp'][0]:g}-{r['O3_Consumed_pct_odp'][1]:g} % o.d. pulp. Reaction time is NOT an input: the papers' times depend on their reactors.")
    g1, g2 = st.columns(2)
    target = g1.number_input("Goal: change in L* (dL*)", 0.5, 6.0, 3.0, 0.5, key="wi_t")
    dpl = g2.slider("Limit: max DP loss (%)", 5, 40, 25, key="wi_d") / 100
    with st.expander("Suitability score weights (lower score = better; 1.0 = neutral)"):
        w = {k: st.slider(k, 0.0, 3.0, v, 0.1, key=f"wi_w_{k}") for k, v in DEFAULT_WEIGHTS.items()}
    defaults = [("A - low ozone", 3.0, 30.0, 0.30), ("B - medium ozone", 3.0, 30.0, 0.60), ("C - higher ozone", 3.0, 30.0, 1.00)]
    cols = st.columns(3); sc = []
    for col, (nm, pH0, T0, O0) in zip(cols, defaults):
        with col:
            st.markdown(f"**Scenario {nm}**")
            pH = st.number_input("pH", 0.0, 14.0, pH0, 0.25, key=f"p_{nm}")
            T = st.number_input("Temperature (C)", 1.0, 99.0, T0, 5.0, key=f"t_{nm}")
            O3 = st.number_input("Ozone consumed (% o.d. pulp)", 0.0, 3.0, O0, 0.05, key=f"o_{nm}")
            sc.append((nm, pH, T, O3))
    rows = []
    for nm, pH, T, O3 in sc:
        p = predict_bleach(bl, pH, T, O3); plan = ozone_mass_plan(s["volume_L"], s["consistency_pct"], O3, s.get("ozone_output_mg_h"), s.get("transfer_eff_pct"))
        g = predict_bleach_grid(bl, pd.DataFrame([[pH, T, O3]], columns=BLEACH_FEATURES))
        dL = p["L_star"]["value"] - P1_BASELINE["L_star"]; dpl_ = (P1_BASELINE["DP"] - p["DP"]["value"]) / P1_BASELINE["DP"]
        st_ = p["envelope"]["status"]
        rows.append({"Scenario": nm, "Predicted L*": p["L_star"]["value"], "dL*": dL, "L* 95% band": f"{p['L_star']['low']:.1f} to {p['L_star']['high']:.1f}",
                     "Predicted a*": p["a_star"]["value"], "Predicted b*": p["b_star"]["value"], "Predicted DP": p["DP"]["value"], "DP loss %": 100 * dpl_,
                     "Ozone consumed %": O3, "Ozone mass mg (derived)": plan["o3_mg_needed_consumed"],
                     "Min. time min (100% transfer)": plan["time_h_lower_bound"] * 60 if plan["time_h_lower_bound"] else None,
                     "Model spread (L*)": float(g.L_star_std.iloc[0]), "Envelope": st_, "Meets goal?": bool(dL >= target and dpl_ <= dpl),
                     "Score": w["ozone"] * O3 / max(r["O3_Consumed_pct_odp"][1], 1e-9) + w["dp_loss"] * dpl_ / max(dpl, 1e-9) + w["uncertainty"] * float(g.L_star_std.iloc[0]) + w["envelope"] * (st_ == "YELLOW") + 100 * (st_ == "RED")})
    df = pd.DataFrame(rows)
    st.dataframe(df.round(2), hide_index=True, width="stretch")
    ok = df[(df["Meets goal?"]) & (df.Envelope != "RED")]
    if len(ok): st.success(f"Best suitability among scenarios that meet your goals and are not RED: **{ok.sort_values('Score').iloc[0].Scenario}** (score {ok.Score.min():.2f}).")
    else: st.warning("No scenario meets the goal inside the data-supported envelope. Raw predictions are shown anyway; RED rows add +100 to the score and are never recommended.")
    st.latex(r"score = w_{O_3}\frac{O_3}{O_{3,max}} + w_{DP}\frac{DP\ loss}{limit} + w_{unc}\,\sigma_{L^*} + w_{env}[YELLOW] + 100\,[RED]")
    for _, x in df.iterrows(): st.markdown(f"{x.Scenario}: {ui.pill(x.Envelope)}", unsafe_allow_html=True)
    st.subheader("Response curves (all other inputs as in scenario B)")
    _, pH, T, _ = sc[1]; O3s = np.round(np.arange(0.05, r["O3_Consumed_pct_odp"][1] + 1e-9, 0.05), 2)
    figs = []
    curves = []
    for ph in sorted({round(pH, 2), 2.5, 5.0, 7.0}):
        gg = predict_bleach_grid(bl, pd.DataFrame({"pH": ph, "Temp_C": T, "O3_Consumed_pct_odp": O3s})); gg["pH_curve"] = f"pH {ph:g}"; curves.append(gg)
    cv = pd.concat(curves)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.line(cv, x="O3_Consumed_pct_odp", y="L_star_pred", color="pH_curve", title=f"Predicted L* vs ozone consumed ({T:g} C)", labels={"O3_Consumed_pct_odp": "Ozone consumed (% o.d. pulp)", "L_star_pred": "L* [C]"}), width="stretch")
    c2.plotly_chart(px.line(cv, x="O3_Consumed_pct_odp", y="DP_pred", color="pH_curve", title=f"Predicted DP vs ozone consumed ({T:g} C)", labels={"O3_Consumed_pct_odp": "Ozone consumed (% o.d. pulp)", "DP_pred": "DP [C]"}), width="stretch")
    st.caption("Curves outside the measured conditions are interpolation/extrapolation: check the envelope colour of each scenario above. Only 2 temperatures and 5 pH levels exist in the data.")

with tab_w:
    own_m = ui.own_ww_model(); V = s["volume_L"]; ref = settings()["assumptions_editable"]["poster_reference_run"]
    base_h = ref["hours"] * V / ref["volume_L"]
    st.markdown(f"Reference duration scaled from the team's stated run ({ref['volume_L']} L / {ref['hours']} h, poster - team-stated, not measured here): **{base_h:.2f} h for {V:g} L** [D].")
    mults = st.multiselect("Duration multipliers to compare", [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0], default=[0.5, 1.0, 2.0])
    rows = []
    for m in mults:
        h = base_h * m; lo, hi = energy_kwh(h)
        row = {"Duration x": m, "Duration h": h, "Energy kWh (low)": lo, "Energy kWh (high)": hi,
               "Ozone mg/L (needs output)": (s["ozone_output_mg_h"] * h / V) if s.get("ozone_output_mg_h") else None, "Predicted absorbance removal %": None}
        if own_m.get("trained") and s.get("abs0"):
            row["Predicted absorbance removal %"] = float(own_m["model"].predict(pd.DataFrame([{"Treatment_Time_min": h * 60, "Initial_pH": s["pH"] or 7.0, "Temperature_C": s["temp"] or 25.0, "Volume_L": V, "Initial_Abs": s["abs0"]}]))[0])
        rows.append(row)
    if rows:
        d = pd.DataFrame(rows); st.dataframe(d.round(3), hide_index=True, width="stretch")
        st.plotly_chart(px.bar(d, x="Duration h", y=["Energy kWh (low)", "Energy kWh (high)"], barmode="group", title="Energy = poster power ratings x time [D]"), width="stretch")
    if own_m.get("trained"): st.success(f"Own-data model trained on {own_m['n']} wastewater records (CV R2 = {own_m['cv']['R2']:.2f}).")
    else: st.info(f"Predicted COD/TDS/pH/TSS/absorbance removal for laboratory wastewater are **UNKNOWN**: you have logged {own_m['n']} wastewater runs; the app is set to fit a model only after {own_m['needed']} (a developer-chosen software setting, not a literature value). Use the Experiment Planner to collect them.")
