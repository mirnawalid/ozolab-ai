"""Prediction wrappers. Every number returned is tagged as MODEL PREDICTION (origin C) with an uncertainty band."""
import numpy as np
import pandas as pd
from .config import P1_BASELINE
from .envelope import acs_envelope, bleach_envelope
from .training import BLEACH_FEATURES, BLEACH_TARGETS


def reliability(r2: float) -> str:
    return "usable with caution" if r2 >= 0.6 else ("weak" if r2 >= 0.3 else "NOT predictive - do not rely on it")


def predict_bod(acs: dict, x: dict, model_name: str | None = None) -> dict:
    m = acs["models"][model_name or acs["best"]]
    X = pd.DataFrame([{c: x[c] for c in acs["features"]}])
    y = float(m.predict(X)[0]); half = 1.96 * acs["test_rmse"]
    return {"value": y, "low": y - half, "high": y + half, "model": model_name or acs["best"], "envelope": acs_envelope(acs, x)}


def predict_bleach(bl: dict, pH: float, T: float, O3: float) -> dict:
    X = pd.DataFrame([[pH, T, O3]], columns=BLEACH_FEATURES); out = {}
    for t, v in bl["targets"].items():
        y = float(v["model"].predict(X)[0]); half = 1.96 * v["cv_rmse"]
        spread = float(np.std([e.predict(X)[0] for e in v["forest"].estimators_]))
        r2 = float(v["table"].loc[v["table"].Model == v["best"], "LOCO_R2"].iloc[0])
        out[t] = {"value": y, "low": y - half, "high": y + half, "tree_std": spread, "model": v["best"], "loco_r2": r2, "reliability": reliability(r2), "label": BLEACH_TARGETS[t]}
    out["envelope"] = bleach_envelope(bl, pH, T, O3)
    return out


def predict_bleach_grid(bl: dict, grid: pd.DataFrame) -> pd.DataFrame:
    """Vectorised: returns grid + predicted columns + tree-spread of L*."""
    g = grid.copy()
    for t, v in bl["targets"].items():
        g[t + "_pred"] = v["model"].predict(g[BLEACH_FEATURES])
    lf = bl["targets"]["L_star"]["forest"]
    g["L_star_std"] = np.std(np.stack([e.predict(g[BLEACH_FEATURES].values) for e in lf.estimators_]), axis=0)
    g["DP_std"] = np.std(np.stack([e.predict(g[BLEACH_FEATURES].values) for e in bl["targets"]["DP"]["forest"].estimators_]), axis=0)
    return g


def to_user_L(pred_L: float, user_L0: float | None) -> float:
    """Literature pulp started at L*=83.04. For a different pulp we can only ADD the predicted change (assumption D)."""
    return pred_L if user_L0 is None else user_L0 + (pred_L - P1_BASELINE["L_star"])
