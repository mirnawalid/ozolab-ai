import streamlit as st
import pandas as pd
from src import ui
from src.config import P1_BASELINE, assumption, settings
from src.recommendation_engine import DEFAULT_WEIGHTS, bleach_recipe, wastewater_recipe

ui.setup("Recommendation", "🧭")
ui.hero("2 - AI Treatment Recommendation", "An operational recipe for the existing prototype - or a clear statement that none is supported.")
s = ui.get_sample(); bl = ui.bleach_bundle()
st.caption(f"Use-case: **{s['module']}** - change it on the Sample Analysis page.")
if s["module"] == "PULP":
    st.warning("LITERATURE BACKGROUND module: it uses 61 experiments PUBLISHED by other researchers on other pulps and reactors. We have not performed pulp-bleaching experiments, and pulp bleaching is not part of the project's final use-case (laboratory wastewater).")
goals = None
if s["module"] == "PULP":
    lo_pH = float(assumption("operating_pH_window_default")[0]); hi_pH = float(assumption("operating_pH_window_default")[1])
    st.subheader("Goals and limits (human-defined)")
    g1, g2, g3 = st.columns(3)
    target = g1.number_input("Target change in L* (dL*)", 0.5, 6.0, 3.0, 0.5, help="In the literature data the largest observed gain is 5.6.")
    dpl = g2.slider("Max acceptable DP loss (cellulose damage), %", 5, 40, 25) / 100
    o3max = g3.number_input("Max ozone consumed (% on o.d. pulp)", 0.1, 1.45, 1.0, 0.05)
    h1, h2, h3 = st.columns(3)
    pHr = h1.slider("Allowed pH window", 0.26, 9.6, (lo_pH, hi_pH), help="Default lower bound 2.0 is a HUMAN-DEFINED safety choice, see config/settings.json.")
    Tr = h2.slider("Allowed temperature (C)", 20, 40, (20, 40))
    with h3:
        st.caption("Scoring weights (transparent, editable)")
    w = {k: st.sidebar.slider(f"weight: {k}", 0.0, 3.0, v, 0.1) for k, v in DEFAULT_WEIGHTS.items()}
    goals = dict(target_dL=target, max_dp_loss=dpl, o3_max=o3max, pH_min=pHr[0], pH_max=pHr[1], T_min=Tr[0], T_max=Tr[1])

if st.button("Generate recommendation", type="primary"):
    rec = bleach_recipe(bl, s, goals, w) if s["module"] == "PULP" else wastewater_recipe(s, ui.own_ww_model())
    st.session_state["recipe"] = rec
rec = st.session_state.get("recipe")
if not rec or rec["module"] != s["module"]:
    st.info("Press **Generate recommendation**."); st.stop()

st.markdown("#### Safety gates")
for stt, msg in rec["gates"]:
    st.markdown(f"{ui.pill(stt)} {msg}", unsafe_allow_html=True)
st.markdown(f"### RECOMMENDED TREATMENT")
st.markdown(f'<div class="rec">{rec["headline"]}</div>', unsafe_allow_html=True)
if rec["status"] == "RED" or not rec["stages"]:
    if rec.get("scenarios") is not None and len(rec["scenarios"]):
        st.caption("Closest data-supported conditions (none meets your goals):")
        st.dataframe(rec["scenarios"][[c for c in ["pH", "Temp_C", "O3_Consumed_pct_odp", "L_star_pred", "DP_pred", "envelope"] if c in rec["scenarios"].columns]].round(2), hide_index=True)
    st.stop()

t1, t2, t3, t4, t5 = st.tabs(["Recipe (stages)", "Expected outcomes", "Why this recommendation?", "Scenarios / alternatives", "Confidence, warnings, unknowns"])
with t1:
    for st_ in rec["stages"]:
        with st.container(border=True):
            st.markdown(f"**{st_['name']}** {ui.tag('origin ' + st_['tag'])}", unsafe_allow_html=True)
            for a in st_["actions"]: st.markdown(f"- {a}")
            st.caption("Reason: " + st_["reason"])
with t2:
    rows = []
    for k, (v, lo, hi, o) in rec["expected"].items():
        val = f"{v:.2f}" if isinstance(v, (int, float)) else str(v)
        rng = f"{lo:.2f} to {hi:.2f}" if lo is not None else "-"
        rows.append((k, val, rng, o))
    st.dataframe(pd.DataFrame(rows, columns=["Quantity", "Expected", "Approx. 95 % band (leave-one-condition-out RMSE)", "Origin"]), hide_index=True, width="stretch")
    if "envelope" in rec: st.markdown(f"Operating envelope: {ui.pill(rec['envelope']['status'])}", unsafe_allow_html=True)
    st.caption("Bands are rough: +/-1.96 x cross-validated RMSE. They are not guaranteed intervals.")
with t3:
    if rec["module"] == "PULP":
        from src.explainability import local_sensitivity, sentence
        p = rec["params"]; base = {"pH": p["pH"], "Temp_C": p["T"], "O3_Consumed_pct_odp": p["O3"]}
        m = bl["targets"]["L_star"]["model"]; sens = local_sensitivity(lambda d: m.predict(d[list(base)]), base, bl["ranges"])
        for _, r in sens.iterrows():
            up = r.pred_change_if_up if abs(r.pred_change_if_up) >= abs(r.pred_change_if_down) else -r.pred_change_if_down
            st.markdown("- " + sentence(r.feature, up, "L*"))
        st.markdown("- The candidate was chosen because it is the cheapest in the **transparent score** below among conditions that (i) are not RED, (ii) reach your dL* target and (iii) respect your DP-loss limit.")
        st.latex(r"score = w_{O_3}\frac{O_3}{O_{3,max}} + w_{DP}\frac{DP\ loss}{limit} + w_{unc}\,u_{norm} + w_{env}\,[YELLOW]")
        st.caption("Weights are in the sidebar (default 1.0 each = neutral). Lower score = better. No hidden factors.")
    else:
        st.markdown("- There is **no** validated dose-response dataset for laboratory wastewater in this project, so the tool does not invent a dose.\n- It therefore gives a **staged, data-collecting baseline** scaled from the team's own stated reference run (poster), plus stop rules and pass/fail checks from the poster's criteria.\n- After enough of your own runs (threshold in config) an own-data model is trained and predictions appear here.")
with t4:
    df = rec["scenarios"]
    if df is not None and len(df):
        st.dataframe(df.round(3), hide_index=True, width="stretch")
    st.caption("Use the What-if Simulator page to change these and see graphs.")
with t5:
    st.markdown("**Warnings / limitations**"); [st.warning(w_) for w_ in rec["warnings"]]
    st.markdown("**UNKNOWN - needs measurement or experimental validation**"); [st.markdown(f"- {u}") for u in rec["unknown"]]

txt = f"OzoLab AI recipe\n{rec['headline']}\n\n" + "\n".join(f"{x['name']}\n" + "\n".join(f"  - {a}" for a in x["actions"]) for x in rec["stages"]) + "\n\nUNKNOWN: " + "; ".join(rec["unknown"])
st.download_button("Download recipe (.txt)", txt, "ozolab_recipe.txt")
