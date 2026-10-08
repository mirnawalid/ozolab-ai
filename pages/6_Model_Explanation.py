import pandas as pd
import plotly.express as px
import streamlit as st
from src import ui
from src.explainability import local_sensitivity, perm_importance, response_curve, sentence, shap_or_none
from src.training import BLEACH_FEATURES, BLEACH_TARGETS

ui.setup("Model Explanation", "🔍")
ui.hero("6 - Model Explanation", "WHY does the model predict what it predicts? Wording rule: 'associated with', 'the model learned' - never proven causation.")
acs, _ = ui.base_models(); bl = ui.bleach_bundle()
t1, t2 = st.tabs(["Pulp bleaching model", "ACS Biochemical Oxygen Demand (BOD) benchmark model"])
with t1:
    tgt = st.selectbox("Target", list(BLEACH_TARGETS), format_func=lambda k: BLEACH_TARGETS[k]); v = bl["targets"][tgt]
    st.write(f"Selected model: **{v['best']}** (leave-one-condition-out R2 = {v['table'].loc[v['table'].Model == v['best'], 'LOCO_R2'].iloc[0]:.2f}, n = {v['n']}).")
    imp = perm_importance(v["model"], v["X"], v["y"])
    st.plotly_chart(px.bar(imp, x="importance_rmse_increase", y="feature", orientation="h", error_x="std", title="Permutation importance (RMSE increase when the input is shuffled; computed on training data)"), width="stretch")
    r = bl["ranges"]; c = st.columns(3)
    base = {"pH": c[0].slider("pH", *map(float, r["pH"]), 3.0), "Temp_C": c[1].slider("Temp (C)", *map(float, r["Temp_C"]), 30.0), "O3_Consumed_pct_odp": c[2].slider("Ozone consumed (%)", *map(float, r["O3_Consumed_pct_odp"]), 0.6)}
    fn = lambda d: v["model"].predict(d[BLEACH_FEATURES])
    sens = local_sensitivity(fn, base, r)
    st.subheader("Direction of influence at this operating point (+/-10 % of each input's range)")
    for _, x in sens.iterrows():
        up = x.pred_change_if_up if abs(x.pred_change_if_up) >= abs(x.pred_change_if_down) else -x.pred_change_if_down
        st.markdown("- " + sentence(x.feature, up, BLEACH_TARGETS[tgt]))
    f = st.selectbox("1-D response curve for", BLEACH_FEATURES)
    rc = response_curve(fn, base, f, *r[f]); st.plotly_chart(px.line(rc, x=f, y="prediction", title=f"Predicted {BLEACH_TARGETS[tgt]} vs {f} (other inputs fixed)"), width="stretch")
    sh = shap_or_none(v["forest"], v["X"])
    if sh is None: st.caption("SHAP is optional and not installed in the cloud build (keeps the app light); permutation importance and response curves above are model-agnostic equivalents.")
    else: st.write("SHAP values available:", pd.DataFrame(sh, columns=BLEACH_FEATURES).abs().mean().round(3).to_dict())
with t2:
    m = acs["models"][acs["best"]]; Xt, yt = acs["X_test"], acs["y_test"]
    imp = perm_importance(m, Xt, yt, 10)
    st.plotly_chart(px.bar(imp, x="importance_rmse_increase", y="feature", orientation="h", title=f"{acs['best']} - permutation importance on the held-out test set"), width="stretch")
    st.caption("Because this dataset is an exact linear function of its inputs, the importances simply recover that formula. This demonstrates the explainability pipeline; it says nothing about real mills or ozone.")
