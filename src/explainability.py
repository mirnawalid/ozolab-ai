"""Model-agnostic explanations (permutation importance, 1-D response curves, local sensitivity). SHAP is used only if installed.
Wording rule: these describe what the MODEL learned (association in the data), not proven causation."""
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from .training import BLEACH_FEATURES

NICE = {"pH": "pH", "Temp_C": "Temperature (C)", "O3_Consumed_pct_odp": "Ozone consumed (% on o.d. pulp)"}


def perm_importance(model, X: pd.DataFrame, y, n_repeats: int = 20, seed: int = 0) -> pd.DataFrame:
    r = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=seed, scoring="neg_root_mean_squared_error")
    return pd.DataFrame({"feature": X.columns, "importance_rmse_increase": r.importances_mean, "std": r.importances_std}).sort_values("importance_rmse_increase", ascending=False)


def response_curve(predict_fn, base: dict, feature: str, lo: float, hi: float, n: int = 40) -> pd.DataFrame:
    xs = np.linspace(lo, hi, n)
    rows = [{**base, feature: v} for v in xs]
    return pd.DataFrame({feature: xs, "prediction": predict_fn(pd.DataFrame(rows))})


def local_sensitivity(predict_fn, base: dict, ranges: dict, frac: float = 0.10) -> pd.DataFrame:
    """One-at-a-time: change each input by +/-frac of its data range; report the model's predicted change."""
    b = float(predict_fn(pd.DataFrame([base]))[0]); out = []
    for f, (lo, hi) in ranges.items():
        d = (hi - lo) * frac
        up = float(predict_fn(pd.DataFrame([{**base, f: min(base[f] + d, hi)}]))[0]); dn = float(predict_fn(pd.DataFrame([{**base, f: max(base[f] - d, lo)}]))[0])
        out.append({"feature": f, "delta_input": d, "pred_change_if_up": up - b, "pred_change_if_down": dn - b})
    return pd.DataFrame(out).assign(strength=lambda x: x[["pred_change_if_up", "pred_change_if_down"]].abs().max(axis=1)).sort_values("strength", ascending=False)


def sentence(feature: str, up: float, target: str, unit: str = "") -> str:
    direction = "higher" if up > 0 else "lower"
    return f"Raising **{NICE.get(feature, feature)}** is associated with a {direction} predicted {target} ({up:+.2f}{unit}) - this is what the model learned, not proof of cause."


def shap_or_none(forest, X: pd.DataFrame):
    try:
        import shap  # optional dependency, deliberately NOT in requirements.txt
        return shap.TreeExplainer(forest).shap_values(X)
    except Exception:
        return None
