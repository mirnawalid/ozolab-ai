"""Digital treatment record: one row per physical experiment. Stored in session + CSV (download it!)."""
import datetime as dt
import pandas as pd
import streamlit as st
from .config import OWN_CSV
from .data_loader import OWN_COLUMNS, load_own_from_disk


def get_own() -> pd.DataFrame:
    if "own_df" not in st.session_state:
        st.session_state["own_df"] = load_own_from_disk()
    return st.session_state["own_df"]


def next_id(module: str) -> str:
    df = get_own()
    n = int((df["Module"] == module).sum()) + 1 if len(df) else 1
    return f"OZO-{'PUL' if module == 'PULP' else 'WW'}-{dt.date.today():%Y%m%d}-{n:03d}"


def _clean(rec: dict) -> dict:
    r = {c: rec.get(c) for c in OWN_COLUMNS}
    r["Origin"] = "B_OWN_EXPERIMENT"
    a0, a1 = r.get("Initial_Abs"), r.get("Final_Abs")
    if a0 not in (None, 0) and a1 is not None and pd.notna(a0) and pd.notna(a1):
        r["Absorbance_Removal_pct"] = round(100 * (float(a0) - float(a1)) / float(a0), 2)
    mp, act = r.get("Model_Prediction"), r.get("Actual_Result")
    if mp is not None and act is not None and pd.notna(mp) and pd.notna(act):
        r["Prediction_Error"] = round(float(mp) - float(act), 4)
    return r


def add_record(rec: dict, persist_local: bool = True) -> None:
    df = get_own()
    new = pd.DataFrame([_clean(rec)], columns=OWN_COLUMNS)
    df = new if df.empty else pd.concat([df, new], ignore_index=True)
    st.session_state["own_df"] = df
    if persist_local:
        try:
            OWN_CSV.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(OWN_CSV, index=False)
        except Exception:
            pass  # read-only filesystem on some hosts: user must download the CSV


def import_csv(file) -> int:
    df = pd.read_csv(file)
    for c in OWN_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[OWN_COLUMNS]
    cur = get_own()
    merged = pd.concat([cur, df], ignore_index=True) if not cur.empty else df
    st.session_state["own_df"] = merged.drop_duplicates(subset=["Experiment_ID"], keep="last").reset_index(drop=True)
    return len(df)
