"""Experiment planner = active learning / design of experiments.
Bleaching: acquisition = w * (ensemble uncertainty) + (1-w) * (distance from existing data), chosen greedily so picks are diverse.
Wastewater: no model exists at first -> transparent design: anchor run, replicates (to measure noise), then maximin space-filling."""
import numpy as np
import pandas as pd
from .config import assumption, settings
from .envelope import bleach_envelope
from .prediction import predict_bleach_grid
from .training import BLEACH_FEATURES, normalise


def plan_bleach(bl: dict, b: dict, k: int = 3, w_unc: float = 0.5) -> pd.DataFrame:
    pHs = np.round(np.arange(b["pH_min"], b["pH_max"] + 1e-9, 0.5), 2); Ts = np.arange(20, 41, 5.0); Ts = Ts[(Ts >= b["T_min"]) & (Ts <= b["T_max"])]
    O3s = np.round(np.arange(0.1, b["o3_max"] + 1e-9, 0.1), 2)
    g = pd.MultiIndex.from_product([pHs, Ts, O3s], names=BLEACH_FEATURES).to_frame(index=False)
    g["envelope"] = [bleach_envelope(bl, *r)["status"] for r in g[BLEACH_FEATURES].values]; g = g[g.envelope != "RED"].reset_index(drop=True)
    if g.empty: return g
    g = predict_bleach_grid(bl, g)
    Z = normalise(g[BLEACH_FEATURES].values, bl["ranges"]); chosen = normalise(bl["X_all"].values, bl["ranges"])
    unc = (g.L_star_std / (g.L_star_std.max() or 1) + g.DP_std / (g.DP_std.max() or 1)) / 2
    picks = []
    for _ in range(min(k, len(g))):
        d = np.min(np.linalg.norm(Z[:, None] - chosen[None], axis=2), axis=1); dn = d / (d.max() or 1)
        score = w_unc * unc.values + (1 - w_unc) * dn; score[[p[0] for p in picks]] = -1
        i = int(np.argmax(score)); picks.append((i, unc.values[i], d[i], score[i])); chosen = np.vstack([chosen, Z[i]])
    out = g.iloc[[p[0] for p in picks]].copy()
    out["uncertainty_norm"] = [p[1] for p in picks]; out["distance_to_data"] = [p[2] for p in picks]; out["acquisition"] = [p[3] for p in picks]
    out["why"] = [f"Explores a poorly covered region (distance {d:.2f} from the nearest measured condition) where the model ensemble disagrees most (uncertainty {u:.2f} of max). A result here should shrink the model's error most." for _, u, d, _ in picks]
    return out.reset_index(drop=True)


def plan_wastewater(own: pd.DataFrame, V: float, k: int = 4, seed: int = 0) -> pd.DataFrame:
    """Next wastewater experiments. By default ONLY treatment duration is varied: the team states that pH and temperature are natural sample conditions.
    pH/temperature are explored only if config assumptions_editable.control_pH_and_temperature_in_design is true."""
    A = settings()["assumptions_editable"]; ds = A["design_space_wastewater"]; ref = A["poster_reference_run"]
    ctrl = bool(A["control_pH_and_temperature_in_design"]["value"])
    base_min = ref["hours"] * 60 * V / ref["volume_L"]
    ww = own[own["Module"] == "WASTEWATER"] if len(own) else pd.DataFrame()
    dims = [0, 1, 2] if ctrl else [0]
    pts = []
    if len(ww):
        t = pd.to_numeric(ww.Treatment_Time_min, errors="coerce") / base_min; ph = pd.to_numeric(ww.Initial_pH, errors="coerce"); tt = pd.to_numeric(ww.Temperature_C, errors="coerce")
        pts = [list(x) for x in zip(t, ph, tt) if not any(pd.isna(x[d]) for d in dims)]
    lo = np.array([ds["duration_multiplier"][0], ds["pH"][0], ds["temperature_C"][0]]); hi = np.array([ds["duration_multiplier"][1], ds["pH"][1], ds["temperature_C"][1]])
    rows = []
    n_anchor = sum(1 for p_ in pts if abs(p_[0] - 1) < 0.05)
    while n_anchor < 3 and len(rows) < k:   # anchor + 2 replicates -> measurement noise
        rows.append({"Run_type": "Anchor / replicate" if n_anchor else "Anchor (reference dose)", "Duration_multiplier": 1.0, "Duration_min": base_min, "pH": None, "Temperature_C": None,
                     "why": "Baseline at the team's reference dose with the sample's NATURAL pH and temperature. Repeating it 3x gives the run-to-run noise; without it no later difference can be trusted."})
        n_anchor += 1
    rng = np.random.default_rng(seed); cand = lo + rng.random((800, 3)) * (hi - lo)
    have = ((np.array(pts) - lo) / (hi - lo))[:, dims] if pts else np.empty((0, len(dims)))
    while len(rows) < k:
        Zc = ((cand - lo) / (hi - lo))[:, dims]
        d = np.min(np.linalg.norm(Zc[:, None] - have[None], axis=2), axis=1) if len(have) else np.ones(len(Zc))
        i_ = int(np.argmax(d)); c = cand[i_]
        rows.append({"Run_type": "Space-filling", "Duration_multiplier": round(float(c[0]), 2), "Duration_min": float(c[0] * base_min),
                     "pH": round(float(c[1]), 1) if ctrl else None, "Temperature_C": round(float(c[2]), 0) if ctrl else None,
                     "why": f"Farthest point from all your existing runs in the explored factor(s) ({'duration, pH, temperature' if ctrl else 'treatment duration only; pH and temperature stay natural'}) (distance {d[i_]:.2f}); bounds are human-defined, NOT validated optima."})
        have = np.vstack([have, ((c - lo) / (hi - lo))[dims][None]])
    return pd.DataFrame(rows)
