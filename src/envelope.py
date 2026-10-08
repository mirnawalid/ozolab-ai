"""Safe / Validated Operating Envelope.  GREEN = supported by data, YELLOW = needs validation, RED = unsupported or unsafe.
Recommendations are produced only INSIDE the safety rules: a violated rule (RED) takes priority and blocks the recipe; the AI cannot change or bypass it. No safety limit is invented: hard gates come from config/settings.json or the user's own confirmations."""
import numpy as np
from .config import assumption, settings
from .training import BLEACH_FEATURES, normalise

ORDER = {"GREEN": 0, "YELLOW": 1, "RED": 2}


def worst(*s):
    return max(s, key=lambda x: ORDER[x])


def bleach_envelope(bl: dict, pH: float, T: float, O3: float) -> dict:
    r, tol = bl["ranges"], assumption("range_tolerance_fraction")
    x = dict(zip(BLEACH_FEATURES, [pH, T, O3])); status, why = "GREEN", []
    if not (0 <= pH <= 14) or O3 < 0 or T <= 0 or T >= 100:
        return {"status": "RED", "reasons": ["Physically invalid input (pH outside 0-14, negative ozone, or temperature outside 0-100 C)."], "nn_distance": None}
    for c in BLEACH_FEATURES:
        lo, hi = r[c]; span = hi - lo or 1.0
        over = max(x[c] - hi, lo - x[c], 0) / span
        if over > tol:
            status = "RED"; why.append(f"{c} = {x[c]:.2f} is outside the literature range {lo:g}-{hi:g} by more than {tol:.0%} of the range - unsupported.")
        elif over > 0:
            status = worst(status, "YELLOW"); why.append(f"{c} = {x[c]:.2f} is slightly outside the literature range {lo:g}-{hi:g} - requires validation.")
    Z = normalise(bl["X_all"].values, r); z = normalise([pH, T, O3], r)
    d = float(np.min(np.linalg.norm(Z - z, axis=1)))
    if d > bl["nn_p95"] and status != "RED":
        status = worst(status, "YELLOW"); why.append(f"Nearest measured condition is far away (normalised distance {d:.2f} > {bl['nn_p95']:.2f}, the 95th percentile of the training data's own spacing) - interpolating between sparse conditions.")
    if status == "GREEN": why.append("Inside the range and close to measured literature/own conditions (only 2 temperatures, 5 pH levels exist in the data).")
    return {"status": status, "reasons": why, "nn_distance": d}


def acs_envelope(acs: dict, x: dict) -> dict:
    status, why = "GREEN", []
    for c in acs["features"]:
        v = x[c]
        if v < acs["min"][c] or v > acs["max"][c]:
            status = "RED"; why.append(f"{c}={v:g} is outside the dataset range {acs['min'][c]:.4g}-{acs['max'][c]:.4g}.")
        elif v < acs["lo"][c] or v > acs["hi"][c]:
            status = worst(status, "YELLOW"); why.append(f"{c}={v:g} is in the extreme 1% tail of the training data.")
    return {"status": status, "reasons": why or ["All inputs inside the central 98% of the dataset."]}


def safety_gates(s: dict) -> list:
    """Human-confirmed gates. Returns list of (status, message). Any RED blocks the recipe."""
    g = []
    def gate(ok, msg_ok, msg_bad):
        g.append(("GREEN", msg_ok) if ok else ("RED", msg_bad))
    gate(s.get("ventilation"), "Fume hood / ventilation confirmed.", "Ventilation / fume hood NOT confirmed - ozone gas is toxic; do not run.")
    gate(s.get("offgas"), "Ozone off-gas handling confirmed.", "Off-gas destruction/venting NOT confirmed. None is visible in the prototype photos - do not run until installed.")
    gate(s.get("estop"), "Power cut-off / emergency stop confirmed.", "Emergency stop / quick power cut-off NOT confirmed (none visible in photos; breadboard wiring is exposed next to water) - do not run.")
    gate(s.get("ppe"), "PPE and supervisor present confirmed.", "PPE / supervisor presence NOT confirmed.")
    spec = settings()["team_specification"]; o3max = spec["ozone_generation_max"]["value"]; fl = spec["o2_flow_L_per_h"]
    if s.get("ozone_output_mg_h"):
        gate(s["ozone_output_mg_h"] <= o3max, f"Entered ozone output {s['ozone_output_mg_h']:g} mg/h is within the team specification (<= {o3max} mg/h; unit to be verified on the device label).",
             f"Entered ozone output {s['ozone_output_mg_h']:g} mg/h EXCEEDS the team specification (<= {o3max} mg/h). Reduce the generator setting and re-check before any run.")
    if s.get("air_flow_L_h"):
        gate(fl["min"] <= s["air_flow_L_h"] <= fl["max"], f"O2/air flow {s['air_flow_L_h']:g} L/h is inside the team specification ({fl['min']}-{fl['max']} L/h).",
             f"O2/air flow {s['air_flow_L_h']:g} L/h is OUTSIDE the team specification ({fl['min']}-{fl['max']} L/h). Adjust the flow and re-check before any run.")
    if s.get("flammable_solvents"):
        g.append(("RED", "Flammable solvents above trace level + ozone/oxygen = fire/explosion and vapour-stripping risk. Not recommended by this tool; consult the lab safety officer."))
    else:
        g.append(("GREEN", "No flammable solvents above trace level declared."))
    return g


def overall(gates: list) -> str:
    return worst(*[x[0] for x in gates]) if gates else "GREEN"
