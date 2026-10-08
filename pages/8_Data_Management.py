import pandas as pd
import streamlit as st
from src import ui
from src.config import ARCHIVE_XLSX, ACS_XLSX
from src.data_loader import data_counts, load_acs, load_literature_clean, load_literature_full, load_poster_poc
from src.records import get_own

ui.setup("Data Management", "🗄️")
ui.hero("8 - Dataset & Data Management", "Every dataset keeps its origin label. They are never silently mixed.")
own = get_own(); c = data_counts(own)
a, b, d, e = st.columns(4); a.metric("A - ACS daily records (not ozone)", c["acs_rows"]); b.metric("A - Literature rows (harmonised)", c["lit_rows_all"]); d.metric("A - Literature rows used by the model (published, not ours)", c["lit_rows_kinetics"]); e.metric("B - Our own experiments", c["own_records"])
st.markdown("""
| Dataset | Origin | Used for | NOT used for |
|---|---|---|---|
| ACS Eng. Au 2026 Table S1 (1,033 DAILY records, 2020-01-01 to 2022-10-29, one per day, from a European paper-mill wastewater plant; DOI 10.1021/acsengineeringau.5c00088) | A - external, historical data of another plant | Water-treatment pipeline, model benchmarking, explainability demo | Any ozone dose or bleaching claim |
| Literature ozone-bleaching tables (189 transcribed rows -> 127 harmonised rows after merging the two linked tables of one study -> 61 kinetic rows train the model). Published experiments, NOT performed by us. | A - external | Pulp L*/a*/b*/DP surrogate model | Laboratory-wastewater prediction |
| Poster 'Proof of Concept' (2 samples) | Team poster, UNVERIFIED | Context only | Training |
| `data/own/experiments.csv` | B - our experiments | Retraining; takes priority over A as it grows | - |
| Brightness-defect MATLAB paper (ScienceDirect S2666016424003281) | Reference study | Domain/process knowledge only - its dataset is not available and was NOT recreated | Training |
""")
t = st.tabs(["Literature (full)", "Combined clean (ML)", "Source index", "Derived/calculated", "ACS", "Poster PoC", "Own"])
with t[0]: st.dataframe(load_literature_full(), width="stretch", hide_index=True)
with t[1]: st.dataframe(load_literature_clean(), width="stretch", hide_index=True)
with t[2]: st.dataframe(pd.read_csv(ARCHIVE_XLSX.parent.parent / "data" / "literature" / "source_index.csv"), width="stretch", hide_index=True)
with t[3]: st.dataframe(pd.read_csv(ARCHIVE_XLSX.parent.parent / "data" / "literature" / "derived_calculated_not_observations.csv"), width="stretch", hide_index=True); st.caption("Calculated values - NOT measured observations.")
with t[4]: st.dataframe(load_acs(), width="stretch", hide_index=True)
with t[5]: st.dataframe(load_poster_poc(), width="stretch", hide_index=True)
with t[6]: st.dataframe(own, width="stretch", hide_index=True)
st.subheader("Downloads")
if ARCHIVE_XLSX.exists(): st.download_button("Project Archive Excel (Existing_Dataset, Literature, Combined_Clean, Source_Index, Derived, Reference_Physical)", ARCHIVE_XLSX.read_bytes(), ARCHIVE_XLSX.name)
st.markdown(f"ACS source: <https://pubs.acs.org/doi/10.1021/acsengineeringau.5c00088> - file expected at `data/raw/{ACS_XLSX.name}` (sheet `Input_Data`).")
st.caption("Data quality rules: no invented values, no graph digitising, original units preserved next to converted values, different papers are not assumed comparable.")
