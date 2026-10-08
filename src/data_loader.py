"""Dataset loading with explicit origin labels. Nothing is generated or imputed here."""
import pandas as pd
import streamlit as st
from .config import ACS_XLSX, LIT_CLEAN, LIT_FULL, OWN_CSV, POSTER_CSV

ACS_RENAME = {"Flow_Rate (m3/h)": "Flow_Rate", "TSS (mg/L)": "TSS", "BOD_In (mg/L)": "BOD_In", "Temperature (°C)": "Temperature",
              "Aeration_Rate (kg/h)": "Aeration_Rate", "Retention_Time (h)": "Retention_Time",
              "Chemical_Consumption (kg)": "Chemical_Consumption", "BOD_Out (mg/L)": "BOD_Out"}
ACS_FEATURES = ["Flow_Rate", "TSS", "BOD_In", "Temperature", "Aeration_Rate", "Retention_Time", "Chemical_Consumption"]
ACS_TARGET = "BOD_Out"

OWN_COLUMNS = ["Experiment_ID", "Date", "Module", "Sample_Type", "Volume_L", "Pulp_Consistency_pct", "Initial_pH", "Initial_TDS_mg_L",
               "Initial_TSS_mg_L", "Initial_COD_mg_L", "Initial_Abs", "Wavelength_nm", "Temperature_C", "Initial_L_star", "Initial_DP",
               "Ozone_Output_mg_h", "Treatment_pH", "Treatment_Time_min", "O3_Consumed_pct_odp", "O3_Dose_mg_per_L", "Air_Flow_L_min",
               "Recommended_Treatment", "Actual_Treatment", "Final_pH", "Final_TDS_mg_L", "Final_TSS_mg_L", "Final_COD_mg_L", "Final_Abs",
               "Final_L_star", "Final_DP", "Final_Brightness_ISO", "Pulp_Strength_Note", "Prediction_Target", "Model_Prediction",
               "Actual_Result", "Prediction_Error", "Absorbance_Removal_pct", "Origin", "Notes"]


@st.cache_data(show_spinner=False)
def load_acs() -> pd.DataFrame:
    df = pd.read_excel(ACS_XLSX, sheet_name="Input_Data").rename(columns=ACS_RENAME)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_literature_clean() -> pd.DataFrame:
    return pd.read_csv(LIT_CLEAN)


@st.cache_data(show_spinner=False)
def load_literature_full() -> pd.DataFrame:
    return pd.read_csv(LIT_FULL)


def load_poster_poc() -> pd.DataFrame:
    return pd.read_csv(POSTER_CSV) if POSTER_CSV.exists() else pd.DataFrame()


def load_own_from_disk() -> pd.DataFrame:
    if OWN_CSV.exists() and OWN_CSV.stat().st_size > 0:
        try:
            df = pd.read_csv(OWN_CSV)
            for c in OWN_COLUMNS:
                if c not in df.columns:
                    df[c] = None
            return df[OWN_COLUMNS]
        except Exception:
            pass
    return pd.DataFrame(columns=OWN_COLUMNS)


def data_counts(own: pd.DataFrame) -> dict:
    lit = load_literature_clean()
    lit_model = lit[(lit.Task_Group == "KINETICS_OPTICAL_DP") & (~lit.Is_Baseline.astype(bool))]
    return {"acs_rows": len(load_acs()), "lit_rows_all": len(lit), "lit_rows_kinetics": len(lit_model),
            "own_records": len(own), "own_pulp": int((own["Module"] == "PULP").sum()) if len(own) else 0,
            "own_wastewater": int((own["Module"] == "WASTEWATER").sum()) if len(own) else 0}
