import pandas as pd
import plotly.express as px
import streamlit as st
from src import ui
from src.data_loader import ACS_FEATURES, load_acs
from src.prediction import predict_bod

ui.setup("Water Quality Analysis", "💧")
ui.hero("5 - Water Quality Analysis", "ACS pulp-mill dataset [A]: historical records of ANOTHER plant, used as a water-treatment modelling benchmark. It is NOT an ozone dataset, not our data, and never produces an ozone setting.")
acs, _ = ui.base_models(); df = load_acs(); s = ui.get_sample()
st.warning(f"Integrity note: in this file effluent Biochemical Oxygen Demand (BOD) is an exact linear function of the inputs (linear R2 = {acs['integrity']['linear_R2_full']:.6f}). Real plant data does not behave like this, so treat the file as a pipeline demonstration, not as evidence about real mills or about ozone.")
with st.expander("What is BOD? (Biochemical Oxygen Demand) - read this first", expanded=True):
    st.markdown("""
**BOD = Biochemical Oxygen Demand.** It is the amount of dissolved oxygen that microorganisms consume while biologically breaking down the *biodegradable organic matter* in a water sample, measured over a standard test period (the usual test is BOD5: 5 days at 20 C - general laboratory standard, not a project result).
- A **higher BOD** means the water contains **more biodegradable organic pollution**.
- BOD is **not** a measure of how much oxygen is *supplied* to a system. Oxygen supplied (for example plant aeration, or the oxygen flow of our device) and BOD are different quantities; more oxygen does **not** mean more BOD. In a biological treatment plant, aeration supplies oxygen to the microorganisms so that they can *lower* the BOD of the water.
- Treatment conditions (including ozone) can change the BOD that is measured afterwards, but that must be **measured** - this app does not predict it for ozone.
- **ΔBOD (change in BOD)** is used here as **BOD at the inlet minus BOD at the outlet** (influent BOD - effluent BOD, same units, mg/L). Positive ΔBOD = BOD was removed. Removal % = ΔBOD / inlet BOD x 100. For our own lab runs, ΔBOD would need a BOD measurement before and after treatment; the availability of a BOD method is UNKNOWN in the project material.
""")
t1, t2, t3 = st.tabs(["Explore", "Biochemical Oxygen Demand (BOD) predictor (benchmark)", "Your sample vs this dataset"])
with t1:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.line(df, x="Date", y=["BOD_In", "BOD_Out"], title="Influent vs effluent Biochemical Oxygen Demand (mg/L) - historical plant data [A]"), width="stretch")
    d_ = df.assign(dBOD=df["BOD_In"] - df["BOD_Out"])
    m1, m2 = st.columns(2)
    m1.metric("Median ΔBOD = BOD_In - BOD_Out (mg/L)", f"{d_.dBOD.median():.0f}"); m2.metric("Median BOD removal (ΔBOD / BOD_In)", f"{(d_.dBOD / d_.BOD_In * 100).median():.0f} %")
    st.caption("Computed from the historical ACS records (another plant, daily values). Not a result of our ozone system.")
    var = c2.selectbox("Distribution of", ACS_FEATURES + ["BOD_Out"]); c2.plotly_chart(px.histogram(df, x=var, nbins=40, title=var), width="stretch")
    corr = df[ACS_FEATURES + ["BOD_Out"]].corr().round(2); st.plotly_chart(px.imshow(corr, text_auto=True, title="Correlation matrix (association only)", color_continuous_scale="RdBu", zmin=-1, zmax=1), width="stretch")
    st.dataframe(df.describe().T.round(2), width="stretch")
    st.caption(f"{len(df)} daily records, {df.Date.min():%Y-%m-%d} to {df.Date.max():%Y-%m-%d}; missing values: {int(df.isna().sum().sum())}.")
with t2:
    cols = st.columns(4); x = {}
    for i, f in enumerate(ACS_FEATURES):
        x[f] = cols[i % 4].number_input(f, float(acs["min"][f]) * 0.5, float(acs["max"][f]) * 1.5, float(df[f].median()), key=f"acs_{f}", help=("Oxygen SUPPLIED to the plant's biological treatment (kg/h) - an operating input, not the same thing as BOD." if f == "Aeration_Rate" else ("BOD of the incoming water (mg/L)" if f == "BOD_In" else None)))
    mn = st.selectbox("Model", list(acs["models"]), index=list(acs["models"]).index(acs["best"]))
    p = predict_bod(acs, x, mn)
    st.metric("Predicted effluent Biochemical Oxygen Demand, BOD (mg/L) [C]", f"{p['value']:.1f}", f"95% band {p['low']:.1f} to {p['high']:.1f}")
    st.markdown(f"Envelope: {ui.pill(p['envelope']['status'])} " + " ".join(p["envelope"]["reasons"]), unsafe_allow_html=True)
with t3:
    st.caption("Only TSS and temperature are comparable between your sample and a pulp-mill activated-sludge plant. This is context, not a prediction.")
    for lab, key, col in [("TSS (mg/L)", "TSS", "TSS"), ("Temperature (C)", "temp", "Temperature")]:
        v = s.get(key)
        if v is None: st.write(f"{lab}: not entered."); continue
        pct = float((df[col] < v).mean() * 100)
        st.write(f"{lab}: your value **{v:g}** [E] lies at the {pct:.0f}th percentile of the ACS dataset (range {df[col].min():.0f}-{df[col].max():.0f}).")
