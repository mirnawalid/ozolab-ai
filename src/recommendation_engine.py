"""AI Treatment Recipe Engine.

Two independent pathways (never mixed):
 A) PULP module  : literature-trained surrogate (pH, T, ozone consumed -> L*, DP)  [origin A + C]
 B) WASTEWATER   : NO validated dose-response data exists yet -> a safe, staged, data-collecting recipe;
                   predictions appear only after the team's own experiments pass the minimum-records threshold.
Every line carries an origin tag: [A] external data, [B] own data, [C] model prediction, [D] engineering assumption, [E] user input.
"""
import numpy as np
import pandas as pd
from .config import P1_BASELINE, assumption, settings
from .envelope import overall, safety_gates
from .prediction import predict_bleach, predict_bleach_grid, to_user_L
from .training import BLEACH_FEATURES

DEFAULT_WEIGHTS = {"ozone": 1.0, "dp_loss": 1.0, "uncertainty": 1.0, "envelope": 1.0}


# --------------------------------------------------------------------------- helpers
def energy_kwh(hours: float) -> tuple:
    s = settings()["device_specs_from_poster"]
    return ((s["ozone_generator_W"] + s["o2_or_air_pump_W_min"]) * hours / 1000, (s["ozone_generator_W"] + s["o2_or_air_pump_W_max"]) * hours / 1000)


def ozone_mass_plan(volume_L: float, consistency_pct: float, dose_pct_odp: float, output_mg_h, eff_pct) -> dict:
    od_g = volume_L * 1000 * consistency_pct / 100          # [D] suspension density taken as 1 kg/L
    o3_mg = dose_pct_odp / 100 * od_g * 1000
    r = {"od_pulp_g": od_g, "o3_mg_needed_consumed": o3_mg, "time_h_lower_bound": None, "time_h": None}
    if output_mg_h:
        r["time_h_lower_bound"] = o3_mg / output_mg_h                     # 100 % transfer: absolute minimum
        if eff_pct: r["time_h"] = o3_mg / (output_mg_h * eff_pct / 100)
    return r


# --------------------------------------------------------------------------- PULP pathway
def recommend_bleach(bl: dict, s: dict, goals: dict, weights: dict | None = None) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    r = bl["ranges"]
    pHs = np.round(np.arange(max(r["pH"][0], goals["pH_min"]), min(r["pH"][1], goals["pH_max"]) + 1e-9, 0.25), 2)
    Ts = np.array([t for t in np.arange(20, 41, 5.0) if goals["T_min"] <= t <= goals["T_max"]])
    O3s = np.round(np.arange(0.05, min(r["O3_Consumed_pct_odp"][1], goals["o3_max"]) + 1e-9, 0.05), 2)
    if len(pHs) == 0 or len(Ts) == 0 or len(O3s) == 0:
        return {"feasible": False, "message": "The allowed pH/temperature/ozone window does not overlap the literature data range.", "candidates": pd.DataFrame()}
    g = pd.MultiIndex.from_product([pHs, Ts, O3s], names=BLEACH_FEATURES).to_frame(index=False)
    g = predict_bleach_grid(bl, g)
    g["dL_pred"] = g.L_star_pred - P1_BASELINE["L_star"]
    g["dp_loss_frac"] = (P1_BASELINE["DP"] - g.DP_pred) / P1_BASELINE["DP"]
    from .envelope import bleach_envelope
    g["envelope"] = [bleach_envelope(bl, a, b, c)["status"] for a, b, c in g[BLEACH_FEATURES].values]
    g = g[g.envelope != "RED"]
    ok = g[(g.dL_pred >= goals["target_dL"]) & (g.dp_loss_frac <= goals["max_dp_loss"])].copy()
    best_possible = float(g.dL_pred.max()) if len(g) else float("nan")
    if ok.empty:
        near = g.sort_values("dL_pred", ascending=False).head(3)
        return {"feasible": False, "best_possible_dL": best_possible, "candidates": near.reset_index(drop=True),
                "message": f"No condition inside the data-supported window is predicted to reach dL* >= {goals['target_dL']:.1f} with DP loss <= {goals['max_dp_loss']:.0%}. Highest predicted dL* in the window is {best_possible:.2f}."}
    n = lambda c: (c - c.min()) / (c.max() - c.min() or 1)
    ok["s_ozone"] = ok.O3_Consumed_pct_odp / max(O3s.max(), 1e-9)
    ok["s_dp"] = ok.dp_loss_frac / max(goals["max_dp_loss"], 1e-9)
    ok["s_unc"] = n(ok.L_star_std + ok.DP_std / 50)   # DP std scaled by ~its data spread; only used for ranking
    ok["s_env"] = (ok.envelope == "YELLOW").astype(float)
    ok["score"] = w["ozone"] * ok.s_ozone + w["dp_loss"] * ok.s_dp + w["uncertainty"] * ok.s_unc + w["envelope"] * ok.s_env
    A = ok.sort_values(["O3_Consumed_pct_odp", "score"]).iloc[0]                      # least ozone
    B = ok.sort_values("score").iloc[0]                                               # best weighted score
    C = ok.sort_values(["dp_loss_frac", "score"]).iloc[0]                             # gentlest on cellulose
    cands = pd.DataFrame([A, B, C]); cands.insert(0, "Scenario", ["A least ozone", "B best weighted score", "C gentlest on cellulose (DP)"])
    key = cands[BLEACH_FEATURES].round(4).astype(str).agg("|".join, axis=1)
    merged = cands.assign(_k=key).groupby("_k", sort=False).agg({**{c: "first" for c in cands.columns if c not in ("Scenario", "_k")}, "Scenario": " + ".join}).reset_index(drop=True)
    return {"feasible": True, "candidates": merged, "n_feasible": len(ok), "weights": w,
            "best_possible_dL": best_possible, "message": ""}


def bleach_recipe(bl: dict, s: dict, goals: dict, weights: dict | None = None) -> dict:
    gates = safety_gates(s); status = overall(gates)
    rec = {"module": "PULP", "gates": gates, "status": status, "stages": [], "warnings": [], "unknown": [], "explain": [], "scenarios": None}
    cap = assumption("max_consistency_pct_for_this_hardware")
    if s["consistency_pct"] > cap:
        gates.append(("RED", f"Consistency {s['consistency_pct']}% exceeds the hardware cap of {cap}% (assumption in config/settings.json: small diaphragm pump/PVC tube not validated for fibre suspensions).")); rec["status"] = status = "RED"
    if status == "RED":
        rec["headline"] = "NOT RECOMMENDED - a safety / hardware gate is RED. No operating numbers are given."; return rec
    res = recommend_bleach(bl, s, goals, weights)
    rec["search"] = res
    if not res["feasible"]:
        rec["headline"] = "NO SUPPORTED RECIPE FOUND - " + res["message"]; rec["scenarios"] = res["candidates"]; return rec
    c = res["candidates"]; rec["scenarios"] = c; top = c[c.Scenario.str.contains("B ")].iloc[0] if c.Scenario.str.contains("B ").any() else c.iloc[0]
    pH, T, O3 = float(top.pH), float(top.Temp_C), float(top.O3_Consumed_pct_odp)
    p = predict_bleach(bl, pH, T, O3); plan = ozone_mass_plan(s["volume_L"], s["consistency_pct"], O3, s.get("ozone_output_mg_h"), s.get("transfer_eff_pct"))
    L0 = s.get("initial_L")
    rec["headline"] = f"Ozonate at pH {pH:g}, {T:g} C until about {O3:.2f} % ozone (on o.d. pulp) has been consumed."
    rec["params"] = {"pH": pH, "T": T, "O3": O3}; rec["pred"] = p; rec["plan"] = plan
    rec["stages"] = [
        {"name": "Stage 0 - Safety", "actions": ["Confirm ventilation, off-gas handling, power cut-off, PPE (all confirmed in the form)."], "reason": "Fixed safety rules set by humans. The AI works inside them; if any is not satisfied the recipe is blocked.", "tag": "E"},
        {"name": "Stage 1 - Pre-treatment", "actions": [
            f"Prepare {s['volume_L']:g} L pulp suspension at {s['consistency_pct']:g} % consistency = {plan['od_pulp_g']:.1f} g o.d. pulp [D: density 1 kg/L].",
            f"Adjust pH to {pH:g} with dilute acid/base and measure it in the slurry. (The screenshot papers do not show P1's reagent; P5 used 4 N sulfuric acid to reach pH 2.5.)",
            f"Bring/hold temperature at {T:g} C (literature tested only 20 C and 40 C).",
            "Measure BEFORE treatment: L*a*b* or ISO brightness, kappa/viscosity if you can, pH, temperature."],
         "reason": "Lower pH gave higher L* at comparable ozone consumption in the P1 series (model-learned association).", "tag": "A+C"},
        {"name": "Stage 2 - Ozone treatment", "actions": [
            f"Target ozone CONSUMED: {O3:.2f} % on o.d. pulp = {plan['o3_mg_needed_consumed']:.0f} mg O3 [derived from your inputs].",
            (f"Time at 100 % transfer (absolute minimum): {plan['time_h_lower_bound']*60:.0f} min at your calibrated {s['ozone_output_mg_h']:g} mg/h."
             if plan["time_h_lower_bound"] else "Time: UNKNOWN - the ozone generator's output (mg/h) is not stated anywhere. Calibrate it (e.g. iodometric trapping - confirm the method with your supervisor) and enter it on the Sample page."),
            (f"With your estimated transfer efficiency {s['transfer_eff_pct']:g} %: about {plan['time_h']*60:.0f} min." if plan["time_h"] else "Transfer efficiency of the PVC column is UNKNOWN - measure off-gas ozone or use sampling (below) to decide when enough has been consumed."),
            "Air/oxygen flow: UNKNOWN for this prototype - no supported value; record what you use.",
            "Sample at 25 %, 50 %, 75 %, 100 % of the planned ozone and keep the intermediate L*/pH readings."],
         "reason": "Ozone consumed (not time) is the variable the model uses; reaction time in the papers depends on their reactor.", "tag": "A+D"},
        {"name": "Stage 3 - Post-treatment", "actions": ["Purge the column with air (off-gas handled), wash the pulp with water, then measure.",
                                                       "NOTE: the radiata-pine paper reached higher brightness with a following peroxide (P) stage - hydrogen peroxide stage is NOT CURRENTLY AVAILABLE in the prototype."],
         "reason": "Removes residual ozone/reaction products before measuring.", "tag": "A"},
        {"name": "Stage 4 - Verification", "actions": [
            f"Measure L*a*b* (or brightness), DP/viscosity if possible, final pH.",
            f"PASS if measured dL* >= {goals['target_dL']:.1f} and DP loss <= {goals['max_dp_loss']:.0%}. Otherwise FAIL -> record it: failures are the most informative data for the model.",
            "Enter the result in Experiment History (digital record)."], "reason": "Closes the learning loop.", "tag": "E"},
    ]
    dL = p["L_star"]["value"] - P1_BASELINE["L_star"]
    rec["expected"] = {
        "L* (literature pulp)": (p["L_star"]["value"], p["L_star"]["low"], p["L_star"]["high"], "C"),
        "Change in L*": (dL, p["L_star"]["low"] - P1_BASELINE["L_star"], p["L_star"]["high"] - P1_BASELINE["L_star"], "C"),
        "DP": (p["DP"]["value"], p["DP"]["low"], p["DP"]["high"], "C"),
        "Ozone consumed (% o.d. pulp)": (O3, None, None, "C"),
        "Ozone mass (mg)": (plan["o3_mg_needed_consumed"], None, None, "D"),
    }
    if L0 is not None: rec["expected"]["L* for YOUR pulp (assumes same change)"] = (to_user_L(p["L_star"]["value"], L0), None, None, "D")
    en = p["envelope"]; rec["envelope"] = en
    rec["warnings"] = [f"Envelope {en['status']}: " + " ".join(en["reasons"])]
    if pH < 2.0: rec["warnings"].append(f"pH {pH:g} means a strong-acid slurry: corrosive; not assessed for this rig (exposed wiring, small pump, PVC fittings). You lowered the default pH window knowingly - wear acid PPE and keep electronics away from the liquid.")
    for t in ("L_star", "DP"):
        if p[t]["reliability"] != "usable with caution": rec["warnings"].append(f"{p[t]['label']} model: {p[t]['reliability']} (leave-one-condition-out R2={p[t]['loco_r2']:.2f}).")
    rec["warnings"] += ["The training pulp (oxygen-delignified hardwood kraft, L*=83.04) is NOT your pulp; the literature data have 2 temperatures and 5 pH levels only.",
                        "The model predicts CIELAB L*, not ISO brightness - ISO brightness was not reported per experiment in these tables."]
    rec["unknown"] = ["Ozone generator output (mg/h)", "Transfer efficiency of the PVC contact column", "Air/O2 flow rate", "Column internal volume", "Whether the pump tolerates fibres", "Your pulp's response (needs experiments)"]
    return rec


def _spec_lines(cfg: dict) -> list:
    sp = cfg["team_specification"]; fl = sp["o2_flow_L_per_h"]; oz = sp["ozone_generation_max"]
    return [
        f"Team-stated device specification [TEAM-STATED, to be verified]: O2/air flow {fl['min']}-{fl['max']} L/h (controlled setting); ozone generation <= {oz['value']} {oz['unit']} (controlled setting; the unit NEEDS VERIFICATION on the ozonizer label).",
        f"Natural / background sample conditions stated by the team (measured, NOT adjusted): pH {sp['sample_pH']['value']}, water temperature {sp['water_temperature_C']['value']} C. Record the real values of YOUR sample; if they differ, this run is outside the team's reference conditions.",
        "Write down the ozonizer dial position and measure its real output (mg/h) so future recommendations can be quantitative.",
    ]


# --------------------------------------------------------------------------- WASTEWATER pathway
def wastewater_recipe(s: dict, own_model: dict | None = None) -> dict:
    cfg = settings(); out = cfg["limits"]["outlet_criteria"]; raw = cfg["limits"]["raw_water_criteria"]; ref = cfg["assumptions_editable"]["poster_reference_run"]
    gates = safety_gates(s); status = overall(gates)
    rec = {"module": "WASTEWATER", "gates": gates, "status": status, "stages": [], "warnings": [], "unknown": [], "scenarios": None}
    if status == "RED":
        rec["headline"] = "NOT RECOMMENDED - a safety gate is RED. No operating numbers are given."; return rec
    V = s["volume_L"]; base_h = ref["hours"] * V / ref["volume_L"]                     # [D] same ozone dose per litre as the team's stated reference run
    rows = []
    for mult in (0.5, 1.0, 2.0):
        h = base_h * mult; lo, hi = energy_kwh(h)
        row = {"Scenario": {0.5: "A - short (x0.5)", 1.0: "B - reference (x1)", 2.0: "C - long (x2)"}[mult], "Duration_h": h, "Energy_kWh_low": lo, "Energy_kWh_high": hi,
               "Ozone_mass_mg": (s["ozone_output_mg_h"] * h * (s.get("transfer_eff_pct") or 100) / 100) if s.get("ozone_output_mg_h") else None,
               "Ozone_mg_per_L": (s["ozone_output_mg_h"] * h / V) if s.get("ozone_output_mg_h") else None, "Predicted_absorbance_removal_pct": None}
        if own_model and own_model.get("trained") and s.get("abs0"):
            X = pd.DataFrame([{"Treatment_Time_min": h * 60, "Initial_pH": s["pH"], "Temperature_C": s["temp"], "Volume_L": V, "Initial_Abs": s["abs0"]}])
            row["Predicted_absorbance_removal_pct"] = float(own_model["model"].predict(X)[0])
        rows.append(row)
    rec["scenarios"] = pd.DataFrame(rows); T = base_h
    pre = []
    if s.get("turbid") or (s.get("TSS") or 0) > assumption("tss_prefilter_trigger_mg_L"):
        pre.append(f"Settle/filter the sample first (turbid or TSS above the configured trigger of {assumption('tss_prefilter_trigger_mg_L')} mg/L [D]) - suspended solids consume ozone. Filter type: UNKNOWN / not shown in photos.")
    if "Heavy metals" in s.get("contaminants", []):
        pre.append("Heavy metals: ozone does NOT remove them. A precipitation/adsorption step is NOT CURRENTLY AVAILABLE in the prototype - route this fraction to licensed disposal.")
    if s["pH"] is not None and not (raw["pH_min"] <= s["pH"] <= raw["pH_max"]): pre.append(f"Measured pH {s['pH']} is outside the raw-water criteria {raw['pH_min']}-{raw['pH_max']} (poster). Note it; do not adjust for the first baseline run.")
    if s["temp"] is not None and s["temp"] > raw["temp_max_C"]: pre.append(f"Sample temperature {s['temp']} C exceeds the {raw['temp_max_C']} C raw-water criterion (poster): cool first.")
    pre += ["Mix and take the BEFORE sample: pH, TDS, temperature, and a spectrophotometer scan (record the wavelength of the main absorbance peak). COD/TSS only if you have the method (availability UNKNOWN).",
            "Keep the initial pH unchanged for the first baseline run (no supported pH target exists for this device)."]
    rec["headline"] = f"Run a staged baseline ozonation of {V:g} L, planned around {T:.2f} h (reference dose x1), sampling at 0 / 10 / 25 / 50 / 75 / 100 % of the time."
    rec["stages"] = [
        {"name": "Stage 0 - Safety", "actions": ["All gates confirmed (form).", "FAIL-SAFE: if ANY gate stops being true during the run (ventilation lost, ozone smell/leak, wiring or water problem, flow or ozone setting outside the specification), STOP at once: switch the ozone generator off, cut power with the emergency stop, ventilate, and do not resume until the cause is fixed. This dashboard is not connected to the hardware, so it cannot stop the machine - the operator and the physical power cut-off do."], "reason": "Fixed safety rules set by humans. The AI works inside them; if any is not satisfied the recipe is blocked.", "tag": "E"},
        {"name": "Stage 1 - Pre-treatment", "actions": pre, "reason": "Rules of good practice; thresholds are configurable assumptions, not validated values.", "tag": "D"},
        {"name": "Stage 2 - Ozone treatment", "actions": [
            f"Circulate through the PVC contact column with the liquid pump and run the ozone generator + air pump for about {T:.2f} h ({T*60:.0f} min) [D: same ozone dose per litre as the team's stated reference run: {ref['volume_L']} L / {ref['hours']} h - team-stated, not measured here].",
            *_spec_lines(cfg),
            "At each sampling time take a small sample and record: spectrophotometer absorbance at the peak wavelength, pH, TDS, temperature.",
            "Duration scenarios A/B/C are below (x0.5, x1, x2): they are experiment design points, NOT predicted optima."],
         "reason": "No dose-response data exist for this device or for laboratory wastewater in the project's datasets, so a measured kinetic curve is the only safe basis for a recommendation.", "tag": "D"},
        {"name": "Stage 3 - Post-treatment", "actions": ["Stop generator, keep the air pump running to purge the column (off-gas handled), then let the water rest.",
                                                       f"Check the discharge criteria: pH {out['pH_min']}-{out['pH_max']}, temperature <= {out['temp_max_C']} C, TDS <= {out['TDS_max_mg_L']} (poster criteria - verify the legal source)."], "reason": "Ozone residuals must be gone before any reuse/discharge decision.", "tag": "A/D"},
        {"name": "Stage 4 - Verification", "actions": ["Measure the AFTER set (same instruments and same wavelength as BEFORE).",
                                                       f"STOP EARLY when absorbance changes by < {assumption('plateau_stop_pct')} % between two consecutive samples [D], or if pH leaves {out['pH_min']}-{out['pH_max']}, TDS > {out['TDS_max_mg_L']}, temperature > {out['temp_max_C']} C, or ANY safety condition is no longer satisfied - in that case switch the generator off and cut power; do not continue the run.",
                                                       "PASS (regulatory screen) only if pH, TDS and temperature meet the criteria. Colour/absorbance removal has no validated pass value yet - report the measured %.",
                                                       "Enter the run in Experiment History."], "reason": "Turns every run into training data.", "tag": "E"},
    ]
    rec["expected"] = {"Absorbance removal (%)": ("UNKNOWN" if not (own_model and own_model.get("trained")) else "see scenarios table", None, None, "C" if own_model and own_model.get("trained") else "-"),
                       "Final pH / TDS / temperature": ("must be measured - no supported prediction", None, None, "-"),
                       "Energy for the reference run (kWh)": (f"{energy_kwh(T)[0]:.2f} - {energy_kwh(T)[1]:.2f}", None, None, "D (poster power ratings x time)")}
    rec["warnings"] = ["Poster 'Proof of Concept' shows 2 unlabeled samples (pH 7.13/7.07, TDS 765/784) - TDS did not decrease; this is NOT evidence of removal.",
                       "The ACS pulp-mill Biochemical Oxygen Demand (BOD) dataset is not an ozone dataset and its file shows signs of being algorithmically generated; it cannot support any ozone dose here.",
                       "Ozone may raise TDS/conductivity via oxidised ionic by-products - watch TDS."]
    rec["unknown"] = ["Ozone output (mg/h)", "Measured O2/air flow (team-stated spec: 90-120 L/h)", "Unit of the ozone specification (team-stated <= 400 mg/h; verify on the device label)", "Which sample the team-stated pH 6.3 belongs to (poster samples show 7.13 / 7.07)", "Liquid pump flow (L/min)", "Column volume", "Composition of your laboratory wastewater", "COD/TSS method availability", "Legal source of the poster's criteria"]
    return rec
