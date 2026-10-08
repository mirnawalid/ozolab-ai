import pandas as pd
import streamlit as st
from src import ui
from src.config import settings
from src.data_loader import data_counts
from src.records import get_own

ui.setup("Home", "🧪")
ui.hero("OzoLab AI - Treatment Decision Support", "Decision-support prototype for the team's EXISTING ozone treatment setup (laboratory wastewater). "
        "Separate from the hardware: you tell it what you have, it recommends what to do, then learns from the results you log.")
own = get_own(); c = data_counts(own); acs, bl = ui.base_models(); sp = settings()["team_specification"]

a, b, c2, d = st.columns(4)
a.metric("Our own experiments performed", c["own_records"]); a.caption("Runs WE did and logged. 0 = none yet - this is a count, not a result.")
b.metric("Published pulp-bleaching experiments", bl["n_external"]); b.caption("From papers/patents - NOT performed by us. They are the 61 kinetic rows inside 127 harmonised literature rows (189 transcribed).")
c2.metric("ACS historical records", f"{c['acs_rows']:,}"); c2.caption("Daily records (2020-01-01 to 2022-10-29) of a European paper-mill wastewater plant. Not ours, not ozone.")
d.metric("Recipes safety-checked", "every one"); d.caption("A recipe is shown only if all safety rules are satisfied.")

st.subheader("What is ours, what is literature, what was set aside")
st.markdown("""
| | Category | Content |
|---|---|---|
| **A** | **What WE did** | Built this decision-support software; transcribed the literature tables; built the physical prototype; a 2-sample 'Proof of Concept' (spectrophotometer scan, pH, TDS - shown on the poster, unlabeled, unverified). **Own logged experiment runs: see the counter above.** |
| **B** | **Found in literature / external data** | 61 pulp-bleaching kinetic experiments (published papers, not ours); the ACS paper-mill file with 1,033 daily records (historical data of another plant); published safety limits. |
| **C** | **Considered earlier, NOT used in the final system** | (1) Detecting dripping water by whether a paper strip bleaches - an old idea, tried on one type of water (**which type: team to state - NEEDS INPUT**); after discussion with the instructor the final approach uses an **indicator** to show whether the paper changed (**indicator details: team to state - NEEDS INPUT**). (2) Pulp bleaching as a use-case of our own - set aside; the final use-case is **laboratory wastewater**. The pulp module remains only as literature background. |
""")

st.subheader("Reference conditions stated by the team (handwritten notes)")
st.dataframe(pd.DataFrame([
    ["Oxygen flow rate", f"{sp['o2_flow_L_per_h']['min']}-{sp['o2_flow_L_per_h']['max']} L/hour", "CONTROLLED device setting", "Team-stated"],
    ["Ozone generation", f"<= {sp['ozone_generation_max']['value']} mg/hour", "CONTROLLED device setting (upper limit)", "Team-stated - UNIT NEEDS VERIFICATION on the ozonizer label"],
    ["Water temperature", f"{sp['water_temperature_C']['value']} C", "NATURAL sample condition (measured, not adjusted)", "Team-stated"],
    ["pH", f"{sp['sample_pH']['value']}", "NATURAL sample condition (measured, not adjusted)", "Team-stated; the handwritten 7 was corrected to 6.3 - NEEDS CLARIFICATION which sample (poster samples: 7.13 / 7.07)"],
], columns=["Quantity", "Value", "Type of condition", "Status"]), hide_index=True, width="stretch")

st.subheader("The learning loop")
st.graphviz_chart("""digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#e3eef3", fontname="Helvetica"];
 Characterize -> Predict -> Optimize -> Recommend -> Experiment -> Measure -> Learn -> Improve -> Characterize; }""")
st.markdown("""
**How to use it (4 steps):**
1. **Sample Analysis** - say what you have (sample, volume, measurements you *actually* have, safety confirmations). Optional fields can stay empty.
2. **AI Treatment Recommendation** - a staged recipe for the *existing* prototype (pre-treatment -> ozone -> post-treatment -> verification), with warnings and everything unknown marked UNKNOWN.
3. **Experiment Planner** - which experiment should we run next?
4. **Experiment History** - log the real result. The record exports to CSV and the models can retrain on it.

**Who it is for:** a prototype built for laboratory staff and researchers, as defined in the project poster. It is a first, basic system developed for the current experimental setup. With further development and testing it could be adapted for wider users and applications - this has **not** been demonstrated yet.

**What this system does NOT claim:** it does not know your device's real ozone output, it has no validated dose-response data for laboratory wastewater, and its pulp-bleaching model comes from *published* experiments on other pulps and reactors.
""")

st.error("**Safety logic.** The AI works inside fixed safety rules set by humans (ventilation, ozone off-gas handling, emergency power cut-off, PPE, and the device specification above). "
         "If any rule is not satisfied, the recommendation is **BLOCKED** - no operating numbers are shown and the run must not start. The AI cannot change or bypass these rules. "
         "The dashboard is not connected to the hardware: if something becomes unsafe during a run, the operator must stop the ozone generator and cut power with the emergency stop.")
with st.expander("Data-integrity notice about the ACS dataset (read before presenting)", expanded=False):
    i = acs["integrity"]
    st.warning(f"In the downloaded ACS file, effluent Biochemical Oxygen Demand (BOD) is an **exact linear function** of the 7 inputs (linear-regression R² = {i['linear_R2_full']:.6f}, max residual {i['max_abs_residual']:.1e}). "
               "Real plant data never behaves this way, and the file's summary statistics differ from the paper's own Table S2. It is consistent with algorithmically generated data. "
               "It is therefore used **only** as a pipeline/benchmark demonstration and is never used to derive an ozone setting.")
