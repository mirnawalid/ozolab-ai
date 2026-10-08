"""Functional tests of the decision engine. Run: python tests/test_engine.py"""
import sys, warnings
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); warnings.filterwarnings("ignore")
import pandas as pd
from src.training import load_or_train, train_bleach
from src.recommendation_engine import bleach_recipe, wastewater_recipe
from src.experiment_planner import plan_bleach, plan_wastewater
from src.envelope import bleach_envelope
from src.prediction import predict_bleach
from src.data_loader import OWN_COLUMNS

acs, bl = load_or_train()
safe = dict(module="PULP", volume_L=2.0, consistency_pct=2.0, pH=7.0, temp=25.0, TDS=None, TSS=None, COD=None, abs0=0.5, wavelength=450, initial_L=None, turbid=False,
            contaminants=[], sample_type="x", ozone_output_mg_h=400.0, air_flow_L_h=100.0, transfer_eff_pct=50.0, ventilation=True, offgas=True, estop=True, ppe=True, flammable_solvents=False)
goals = dict(target_dL=3.0, max_dp_loss=0.25, o3_max=1.0, pH_min=2.0, pH_max=9.6, T_min=20, T_max=40)
r = bleach_recipe(bl, safe, goals); print("PULP:", r["headline"]); assert r["status"] in ("GREEN", "YELLOW") and r["stages"]
unsafe = {**safe, "offgas": False}; r2 = bleach_recipe(bl, unsafe, goals); assert r2["status"] == "RED" and not r2["stages"]; print("gate blocks:", r2["headline"][:60])
over = {**safe, "consistency_pct": 10.0}; assert bleach_recipe(bl, over, goals)["status"] == "RED"
imp = bleach_recipe(bl, safe, {**goals, "target_dL": 6.0, "max_dp_loss": 0.05}); print("impossible goal ->", imp["headline"][:90]); assert not imp["stages"]
w = wastewater_recipe({**safe, "module": "WASTEWATER"}); print("WW:", w["headline"]); assert w["stages"] and w["scenarios"] is not None
assert wastewater_recipe({**safe, "module": "WASTEWATER", "ventilation": False})["status"] == "RED"
assert bleach_envelope(bl, 7.0, 90.0, 0.5)["status"] == "RED" and bleach_envelope(bl, 20, 30, 0.5)["status"] == "RED"
pl = plan_bleach(bl, dict(pH_min=2, pH_max=9.6, T_min=20, T_max=40, o3_max=1.0), 3); print(pl[["pH", "Temp_C", "O3_Consumed_pct_odp"]].to_string()); assert len(pl) == 3
pw = plan_wastewater(pd.DataFrame(columns=OWN_COLUMNS), 5.0, 5); print(pw[["Run_type", "Duration_multiplier", "pH", "Temperature_C"]].to_string()); assert len(pw) == 5
# learning loop: one own pulp record changes the training set and is labelled by origin
own = pd.DataFrame([{c: None for c in OWN_COLUMNS}]); own.loc[0, ["Experiment_ID", "Module", "Treatment_pH", "Temperature_C", "O3_Consumed_pct_odp", "Final_L_star", "Final_DP"]] = ["T1", "PULP", 3.0, 30.0, 0.5, 84.0, 900]
b2 = train_bleach(own, save=False); assert b2["n_own"] == 1 and b2["n_external"] == bl["n_external"]; print("retrain ok: own", b2["n_own"], "external", b2["n_external"])
print(predict_bleach(bl, 3, 30, 0.5)["L_star"]["value"])
# --- corrections-round tests
from src.envelope import safety_gates, overall
assert overall(safety_gates({**safe, "ozone_output_mg_h": 450.0})) == "RED"          # above <= 400 mg/h spec
assert overall(safety_gates({**safe, "air_flow_L_h": 60.0})) == "RED"                # outside 90-120 L/h
assert overall(safety_gates({**safe, "air_flow_L_h": 120.0, "ozone_output_mg_h": 400.0})) == "GREEN"
assert wastewater_recipe({**safe, "module": "WASTEWATER", "ozone_output_mg_h": 450.0})["stages"] == []
wr = wastewater_recipe({**safe, "module": "WASTEWATER"}); txt = " ".join(a for s_ in wr["stages"] for a in s_["actions"])
assert "90-120 L/h" in txt and "400" in txt and "6.3" in txt and "FAIL-SAFE" in txt
pw2 = plan_wastewater(pd.DataFrame(columns=OWN_COLUMNS), 5.0, 6); assert pw2["pH"].isna().all() and pw2["Temperature_C"].isna().all()   # pH/temperature stay natural
import json, re
cfgj = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
assert cfgj["team_specification"]["sample_pH"]["value"] == 6.3 and cfgj["team_specification"]["water_temperature_C"]["value"] == 25
for f in list(ROOT.rglob("*.py")) + [ROOT / "README.md"]:
    if "tests" in f.parts or ".venv" in f.parts: continue
    assert "override" not in f.read_text(encoding="utf-8").lower(), f
print("ALL ENGINE TESTS PASSED")
