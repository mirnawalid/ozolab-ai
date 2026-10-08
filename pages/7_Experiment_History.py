import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from src import ui
from src.data_loader import OWN_COLUMNS
from src.prediction import predict_bleach
from src.records import add_record, get_own, import_csv, next_id

ui.setup("Experiment History", "📒")
ui.hero("7 - Experiment History (Digital Treatment Record)", "One row per REAL physical experiment [B]. Streamlit Cloud storage is temporary: DOWNLOAD the CSV after every session and commit it to GitHub.")
s = ui.get_sample(); rec = st.session_state.get("recipe")
num = lambda t: (float(t) if str(t).strip() not in ("", "None") else None)

def f(label, key, ph=""):
    return num(st.text_input(label, key=key, placeholder=ph or "leave empty if not measured"))

mod = st.radio("Record type", ["WASTEWATER", "PULP"], horizontal=True, index=0 if s["module"] == "WASTEWATER" else 1)
with st.form("rec_form", clear_on_submit=False):
    st.markdown(f"**New record** - ID will be `{next_id(mod)}`. Empty fields stay empty; nothing is imputed.")
    a, b, c = st.columns(3)
    sample_type = a.text_input("Sample type", s["sample_type"]); vol = a.number_input("Volume (L)", 0.05, 500.0, float(s["volume_L"]))
    t_min = b.number_input("Actual treatment time (min)", 0.0, 5000.0, 60.0, 5.0); temp = f("Temperature during treatment (C)", "r_T")
    pH0 = f("Initial pH", "r_pH0"); pH1 = f("Final pH", "r_pH1")
    tds0 = f("Initial TDS (mg/L)", "r_tds0"); tds1 = f("Final TDS (mg/L)", "r_tds1")
    tss0 = f("Initial TSS (mg/L)", "r_tss0"); tss1 = f("Final TSS (mg/L)", "r_tss1")
    cod0 = f("Initial COD (mg/L)", "r_cod0"); cod1 = f("Final COD (mg/L)", "r_cod1")
    o_mg = f("Ozone output (mg/h) if calibrated", "r_omg"); air = f("Air/O2 flow (L/min) if known", "r_air")
    if mod == "WASTEWATER":
        ab0 = f("Initial absorbance (peak)", "r_ab0"); ab1 = f("Final absorbance (same wavelength)", "r_ab1"); wl = f("Wavelength (nm)", "r_wl")
        tp = {}
    else:
        cons = f("Consistency (%)", "r_cons"); tpH = f("Treatment pH", "r_tpH"); o3c = f("Ozone CONSUMED (% o.d. pulp)", "r_o3c")
        L0 = f("Initial L*", "r_L0"); L1 = f("Final L*", "r_L1"); dp0 = f("Initial DP", "r_dp0"); dp1 = f("Final DP", "r_dp1"); iso = f("Final ISO brightness", "r_iso"); note_strength = st.text_input("Pulp strength / quality note")
    recd = st.text_area("Recommended treatment (paste from the Recommendation page)", rec["headline"] if rec else "")
    actual = st.text_area("Actual treatment performed (what you REALLY did)", "")
    notes = st.text_area("Notes (deviations, colour, smell, equipment problems...)")
    ok = st.form_submit_button("Save record", type="primary")
if ok:
    r = {"Experiment_ID": next_id(mod), "Date": str(dt.date.today()), "Module": mod, "Sample_Type": sample_type, "Volume_L": vol, "Initial_pH": pH0, "Final_pH": pH1,
         "Initial_TDS_mg_L": tds0, "Final_TDS_mg_L": tds1, "Initial_TSS_mg_L": tss0, "Final_TSS_mg_L": tss1, "Initial_COD_mg_L": cod0, "Final_COD_mg_L": cod1,
         "Temperature_C": temp, "Treatment_Time_min": t_min, "Ozone_Output_mg_h": o_mg, "Air_Flow_L_min": air, "Recommended_Treatment": recd, "Actual_Treatment": actual, "Notes": notes}
    if mod == "WASTEWATER":
        r.update(Initial_Abs=ab0, Final_Abs=ab1, Wavelength_nm=wl)
    else:
        r.update(Pulp_Consistency_pct=cons, Treatment_pH=tpH, O3_Consumed_pct_odp=o3c, Initial_L_star=L0, Final_L_star=L1, Initial_DP=dp0, Final_DP=dp1, Final_Brightness_ISO=iso, Pulp_Strength_Note=note_strength)
        if None not in (tpH, temp, o3c) and L1 is not None:
            bl = ui.bleach_bundle(); p = predict_bleach(bl, tpH, temp, o3c)
            r.update(Prediction_Target="L_star", Model_Prediction=round(p["L_star"]["value"], 3), Actual_Result=L1)
    if mod == "PULP" and (r.get("Treatment_pH") is None or r.get("Temperature_C") is None): st.warning("Saved, but it will be excluded from model training until treatment pH, temperature and ozone consumed are filled in.")
    add_record(r); st.success(f"Saved {r['Experiment_ID']}. The pulp model retrains automatically on valid PULP records.")
own = get_own()
st.subheader(f"All records ({len(own)})")
if len(own):
    st.dataframe(own.dropna(axis=1, how="all"), hide_index=True, width="stretch")
    st.download_button("Download CSV (do this every session)", own.to_csv(index=False), "experiments.csv", "text/csv")
    pe = pd.to_numeric(own.Prediction_Error, errors="coerce").dropna()
    if len(pe): st.metric("Mean absolute prediction error (L*, own records)", f"{pe.abs().mean():.2f}"); st.plotly_chart(px.bar(pe.reset_index(), y=0, title="Prediction error per record (model - actual)"), width="stretch")
else:
    st.info("No own experiments yet. The dataset starts EMPTY on purpose: nothing here is invented.")
up = st.file_uploader("Import a previously downloaded experiments.csv", type="csv")
if up and st.button("Import"): st.success(f"Imported {import_csv(up)} rows (duplicates by ID replaced).")
