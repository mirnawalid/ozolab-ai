import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src import ui
from src.training import BLEACH_TARGETS

ui.setup("ML Model Performance", "📊")
ui.hero("9 - ML Model Performance", "Honest validation: time-ordered split for the ACS series, leave-one-condition-out for the bleaching series (random K-fold shown only to expose leakage).")
acs, _ = ui.base_models(); bl = ui.bleach_bundle()
t1, t2 = st.tabs(["Pulp bleaching surrogate", "ACS Biochemical Oxygen Demand (BOD) benchmark"])
with t1:
    st.caption(f"{bl['n_external']} PUBLISHED (literature) experiments + {bl['n_own']} of our own experiments (0 = none logged yet). A 'condition' = temperature x pH kinetic series; whole series are held out together, otherwise neighbouring points leak.")
    for t, v in bl["targets"].items():
        st.markdown(f"#### {BLEACH_TARGETS[t]} - selected: **{v['best']}** (n={v['n']})")
        tab = v["table"].round(3); st.dataframe(tab, hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.bar(tab.melt("Model", ["LOCO_RMSE", "KFold_RMSE"]), x="Model", y="value", color="variable", barmode="group", title="RMSE: LOCO (honest) vs random K-fold (optimistic)"), width="stretch")
        fig = px.scatter(x=v["y"], y=v["oof_best"], labels={"x": "Observed", "y": "Predicted (leave-one-condition-out)"}, title="Parity plot")
        lo, hi = float(min(v["y"])), float(max(v["y"])); fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="ideal")); c2.plotly_chart(fig, width="stretch")
        r2 = float(tab.loc[tab.Model == v["best"], "LOCO_R2"].iloc[0])
        (st.success if r2 >= 0.6 else st.warning)(f"Honest reliability: R2 = {r2:.2f} -> {'usable with caution' if r2 >= 0.6 else 'weak / not predictive - the app labels it so'}.")
    st.info("Neural networks were deliberately NOT used here: with ~60 rows they would overfit and cannot be justified.")
with t2:
    sp = acs["split"]["dates"]
    st.markdown(f"Chronological split: train {sp[0]} -> {sp[1]}, validation then test up to {sp[3]}; model chosen on **validation**, test untouched; no shuffling (time series).")
    st.dataframe(acs["table"].round(4), hide_index=True, width="stretch")
    st.plotly_chart(px.bar(acs["table"].melt("Model", ["Val_RMSE", "Test_RMSE"]), x="Model", y="value", color="variable", barmode="group", title="RMSE (mg/L Biochemical Oxygen Demand)"), width="stretch")
    m = acs["models"][acs["best"]]; p = m.predict(acs["X_test"])
    fig = px.scatter(x=acs["y_test"], y=p, labels={"x": "Observed BOD_Out", "y": "Predicted"}, title=f"{acs['best']} - held-out test set"); st.plotly_chart(fig, width="stretch")
    st.error("R2 ~ 1.000 for linear models is NOT a success story: the target is an exact linear function of the inputs in this file (data-integrity finding). Do not present it as proof of a good model.")
