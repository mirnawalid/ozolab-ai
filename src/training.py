"""Model training with leakage-aware validation.

ACS pulp-mill BOD data : chronological 70/15/15 split (daily time series -> no random shuffling).
Bleaching kinetics data: Leave-One-Condition-Out CV (a condition = temperature x pH series) because rows of one
                         kinetic series are strongly correlated; random K-fold would leak and look too good.
"""
import json
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, LeaveOneGroupOut, cross_val_predict
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from .config import MODELS, settings
from .data_loader import ACS_FEATURES, ACS_TARGET, load_acs, load_literature_clean

warnings.filterwarnings("ignore")
BLEACH_FEATURES = ["pH", "Temp_C", "O3_Consumed_pct_odp"]
BLEACH_TARGETS = {"L_star": "L* (CIELAB lightness)", "a_star": "a*", "b_star": "b* (yellowness axis)", "DP": "Degree of polymerisation (DP)"}


def metrics(y, p) -> dict:
    return {"R2": float(r2_score(y, p)), "MAE": float(mean_absolute_error(y, p)), "RMSE": float(np.sqrt(mean_squared_error(y, p)))}


def acs_model_zoo() -> dict:
    return {
        "Baseline (mean)": DummyRegressor(),
        "Linear Regression": LinearRegression(),
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Random Forest": RandomForestRegressor(300, min_samples_leaf=3, random_state=0, n_jobs=1),
        "Gradient Boosting": GradientBoostingRegressor(random_state=0),
        "Neural Network (MLP)": make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=800, early_stopping=True, random_state=0)),
    }


def bleach_model_zoo() -> dict:
    return {
        "Baseline (mean)": DummyRegressor(),
        "Linear Regression": LinearRegression(),
        "Ridge poly-2": make_pipeline(StandardScaler(), PolynomialFeatures(2), Ridge(alpha=1.0)),
        "Random Forest": RandomForestRegressor(300, min_samples_leaf=2, random_state=0, n_jobs=1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=2, random_state=0),
    }


# ----------------------------------------------------------------------------- ACS
def train_acs(save: bool = True) -> dict:
    df = load_acs()
    n = len(df); a, b = int(n * 0.70), int(n * 0.85)
    Xtr, ytr = df.loc[:a - 1, ACS_FEATURES], df.loc[:a - 1, ACS_TARGET]
    Xva, yva = df.loc[a:b - 1, ACS_FEATURES], df.loc[a:b - 1, ACS_TARGET]
    Xte, yte = df.loc[b:, ACS_FEATURES], df.loc[b:, ACS_TARGET]
    rows, fitted = [], {}
    for name, m in acs_model_zoo().items():
        m.fit(Xtr, ytr)
        rv, rt = metrics(yva, m.predict(Xva)), metrics(yte, m.predict(Xte))
        rows.append({"Model": name, **{f"Val_{k}": v for k, v in rv.items()}, **{f"Test_{k}": v for k, v in rt.items()}})
    table = pd.DataFrame(rows)
    real = table[table.Model != "Baseline (mean)"]
    best = real.sort_values("Val_RMSE").iloc[0]["Model"]          # selected on VALIDATION only; test untouched
    Xall, yall = df.loc[:b - 1, ACS_FEATURES], df.loc[:b - 1, ACS_TARGET]  # deployment refit = train + val
    for name, m in acs_model_zoo().items():
        fitted[name] = m.fit(Xall, yall)
    bundle = {"features": ACS_FEATURES, "target": ACS_TARGET, "best": best, "models": fitted, "table": table,
              "test_rmse": float(table.loc[table.Model == best, "Test_RMSE"].iloc[0]),
              "split": {"train": (0, a - 1), "val": (a, b - 1), "test": (b, n - 1), "dates": [str(df.Date.iloc[0].date()), str(df.Date.iloc[a].date()), str(df.Date.iloc[b].date()), str(df.Date.iloc[-1].date())]},
              "lo": Xall.quantile(0.01).to_dict(), "hi": Xall.quantile(0.99).to_dict(), "min": Xall.min().to_dict(), "max": Xall.max().to_dict(),
              "X_test": Xte, "y_test": yte}
    # integrity probe: is the target an exact linear function of the inputs?
    lr = LinearRegression().fit(df[ACS_FEATURES], df[ACS_TARGET])
    bundle["integrity"] = {"linear_R2_full": float(lr.score(df[ACS_FEATURES], df[ACS_TARGET])),
                           "max_abs_residual": float(np.abs(df[ACS_TARGET] - lr.predict(df[ACS_FEATURES])).max())}
    if save:
        MODELS.mkdir(exist_ok=True); joblib.dump(bundle, MODELS / "acs_bod_bundle.joblib", compress=3)
    return bundle


# ----------------------------------------------------------------------------- Bleaching
def bleach_frame(own: pd.DataFrame | None = None) -> pd.DataFrame:
    lit = load_literature_clean()
    d = lit[(lit.Task_Group == "KINETICS_OPTICAL_DP") & (~lit.Is_Baseline.astype(bool))].copy()
    d["Group"] = d.Temp_C.astype(int).astype(str) + "C_pH" + d.pH.astype(str)
    d["Origin"] = "EXTERNAL_LITERATURE"
    d = d[["Experiment_ID", "Origin", "Group"] + BLEACH_FEATURES + list(BLEACH_TARGETS)]
    if own is not None and len(own):
        o = own[own["Module"] == "PULP"].copy()
        if len(o):
            o2 = pd.DataFrame({"Experiment_ID": o.Experiment_ID, "Origin": "OWN_EXPERIMENT", "Group": "OWN_" + o.Experiment_ID.astype(str),
                               "pH": pd.to_numeric(o.Treatment_pH, errors="coerce"), "Temp_C": pd.to_numeric(o.Temperature_C, errors="coerce"),
                               "O3_Consumed_pct_odp": pd.to_numeric(o.O3_Consumed_pct_odp, errors="coerce"),
                               "L_star": pd.to_numeric(o.Final_L_star, errors="coerce"), "a_star": np.nan, "b_star": np.nan,
                               "DP": pd.to_numeric(o.Final_DP, errors="coerce")})
            d = pd.concat([d, o2.dropna(subset=BLEACH_FEATURES)], ignore_index=True)
    return d.reset_index(drop=True)


def train_bleach(own: pd.DataFrame | None = None, save: bool = True) -> dict:
    d = bleach_frame(own)
    out = {"features": BLEACH_FEATURES, "targets": {}, "n_external": int((d.Origin == "EXTERNAL_LITERATURE").sum()),
           "n_own": int((d.Origin == "OWN_EXPERIMENT").sum()), "X_all": d[BLEACH_FEATURES].reset_index(drop=True),
           "origin": d.Origin.reset_index(drop=True)}
    for t in BLEACH_TARGETS:
        sub = d.dropna(subset=[t]).reset_index(drop=True)
        X, y, g = sub[BLEACH_FEATURES], sub[t], sub.Group
        rows, oof = [], {}
        for name, m in bleach_model_zoo().items():
            p_g = cross_val_predict(m, X, y, groups=g, cv=LeaveOneGroupOut())
            p_r = cross_val_predict(m, X, y, cv=KFold(5, shuffle=True, random_state=0))
            rows.append({"Model": name, **{f"LOCO_{k}": v for k, v in metrics(y, p_g).items()}, **{f"KFold_{k}": v for k, v in metrics(y, p_r).items()}})
            oof[name] = p_g
        tab = pd.DataFrame(rows)
        best = tab[tab.Model != "Baseline (mean)"].sort_values("LOCO_RMSE").iloc[0]["Model"]
        final = bleach_model_zoo()[best].fit(X, y)
        forest = RandomForestRegressor(300, min_samples_leaf=2, random_state=0, n_jobs=1).fit(X, y)  # ensemble spread -> uncertainty/active learning
        out["targets"][t] = {"best": best, "model": final, "forest": forest, "table": tab, "cv_rmse": float(tab.loc[tab.Model == best, "LOCO_RMSE"].iloc[0]),
                             "n": len(sub), "oof_best": oof[best], "y": y.values, "X": X}
    out["ranges"] = {c: (float(d[c].min()), float(d[c].max())) for c in BLEACH_FEATURES}
    # data-driven "dense" threshold: 95th percentile of leave-one-out nearest-neighbour distance (range-normalised)
    Z = normalise(d[BLEACH_FEATURES].values, out["ranges"])
    dm = np.linalg.norm(Z[:, None] - Z[None], axis=2); np.fill_diagonal(dm, np.inf)
    out["nn_p95"] = float(np.percentile(dm.min(1), 95))
    if save and own is None:
        MODELS.mkdir(exist_ok=True); joblib.dump(out, MODELS / "bleach_bundle.joblib", compress=3)
    return out


def normalise(X, ranges) -> np.ndarray:
    X = np.atleast_2d(np.asarray(X, float))
    lo = np.array([ranges[c][0] for c in BLEACH_FEATURES]); hi = np.array([ranges[c][1] for c in BLEACH_FEATURES])
    return (X - lo) / np.where(hi - lo == 0, 1, hi - lo)


# ----------------------------------------------------------------------------- Own wastewater data
OWN_WW_FEATURES = ["Treatment_Time_min", "Initial_pH", "Temperature_C", "Volume_L", "Initial_Abs"]


def train_own_wastewater(own: pd.DataFrame) -> dict:
    need = int(settings()["assumptions_editable"]["min_own_records_for_own_model"]["value"])
    o = own[own["Module"] == "WASTEWATER"].copy() if len(own) else pd.DataFrame()
    cols = OWN_WW_FEATURES + ["Absorbance_Removal_pct"]
    for c in cols:
        if len(o): o[c] = pd.to_numeric(o[c], errors="coerce")
    o = o.dropna(subset=cols) if len(o) else o
    if len(o) < need:
        return {"trained": False, "n": len(o), "needed": need}
    X, y = o[OWN_WW_FEATURES], o["Absorbance_Removal_pct"]
    m = RandomForestRegressor(300, min_samples_leaf=2, random_state=0).fit(X, y)
    p = cross_val_predict(RandomForestRegressor(300, min_samples_leaf=2, random_state=0), X, y, cv=KFold(min(5, len(o)), shuffle=True, random_state=0))
    return {"trained": True, "n": len(o), "needed": need, "model": m, "cv": metrics(y, p), "X": X}


def load_or_train():
    MODELS.mkdir(exist_ok=True)
    fa, fb = MODELS / "acs_bod_bundle.joblib", MODELS / "bleach_bundle.joblib"
    try:
        acs = joblib.load(fa) if fa.exists() else train_acs()
        bl = joblib.load(fb) if fb.exists() else train_bleach()
        return acs, bl
    except Exception:  # version mismatch on the host -> retrain (takes a few seconds)
        return train_acs(save=False), train_bleach(save=False)


if __name__ == "__main__":
    a = train_acs(); b = train_bleach()
    print(a["table"].round(3).to_string()); print("best ACS:", a["best"], a["integrity"])
    for t, v in b["targets"].items():
        print(t, v["best"], round(v["cv_rmse"], 3), "n=", v["n"]); print(v["table"].round(3).to_string())
    print("nn_p95", b["nn_p95"], b["ranges"])
