"""Shared Streamlit helpers: page setup, cached models, origin badges, sidebar status."""
import hashlib
import pandas as pd
import streamlit as st
from .config import ORIGIN_LABELS, settings
from .data_loader import data_counts
from .records import get_own
from .training import load_or_train, train_bleach, train_own_wastewater

CSS = """<style>
.block-container{padding-top:1.4rem}
.pill{display:inline-block;padding:2px 10px;border-radius:12px;font-weight:600;font-size:0.85rem;color:#fff}
.GREEN{background:#2e7d32}.YELLOW{background:#b28704}.RED{background:#c62828}
.hero{background:linear-gradient(120deg,#0f3a5c,#1f6f8b);color:#fff;padding:1.1rem 1.4rem;border-radius:14px;margin-bottom:1rem}
.hero h2{margin:0;color:#fff}.hero p{margin:.2rem 0 0;opacity:.92}
.rec{border:2px solid #1f6f8b;border-radius:14px;padding:1rem 1.3rem;background:rgba(31,111,139,.08);font-size:1.15rem;font-weight:600}
.tag{font-size:.75rem;background:#e3eef3;color:#0f3a5c;border-radius:6px;padding:1px 6px;margin-left:6px}
</style>"""


def setup(title: str, icon: str = "🧪"):
    st.set_page_config(page_title=f"OzoLab AI - {title}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    sidebar_status()


def pill(status: str) -> str:
    return f'<span class="pill {status}">{status}</span>'


def hero(title: str, sub: str):
    st.markdown(f'<div class="hero"><h2>{title}</h2><p>{sub}</p></div>', unsafe_allow_html=True)


def tag(code: str) -> str:
    return f'<span class="tag">{code}</span>'


@st.cache_resource(show_spinner="Loading models...")
def base_models():
    return load_or_train()


@st.cache_resource(show_spinner="Retraining with your own experiments...")
def _bleach_with_own(_own: pd.DataFrame, key: str):
    return train_bleach(_own, save=False)


def bleach_bundle():
    """Literature model, retrained with the team's own PULP records if any exist (labelled by origin)."""
    _, bl = base_models(); own = get_own()
    o = own[own["Module"] == "PULP"] if len(own) else own
    if len(o) == 0:
        return bl
    key = hashlib.md5(o.to_csv(index=False).encode()).hexdigest()
    try:
        return _bleach_with_own(own, key)
    except Exception:
        return bl


def own_ww_model():
    own = get_own()
    return train_own_wastewater(own) if len(own) else {"trained": False, "n": 0, "needed": int(settings()["assumptions_editable"]["min_own_records_for_own_model"]["value"])}


def sidebar_status():
    own = get_own(); c = data_counts(own); bl = bleach_bundle()
    with st.sidebar:
        st.markdown("### OzoLab AI")
        st.caption("Decision-support prototype for the team's existing ozone setup. Not connected to hardware.")
        st.markdown(f"**Our own experiments performed: {c['own_records']}**")
        st.caption("A count of runs WE did and logged (0 = none yet). Not a result.")
        st.markdown(f"**Published experiments (literature): {bl['n_external']}**")
        st.caption("Pulp-bleaching kinetics taken from papers - NOT performed by us. Used only by the literature-based pulp module.")
        st.markdown(f"**Historical benchmark: {c['acs_rows']:,} daily records**")
        st.caption("European paper-mill wastewater plant (ACS file). Not ours, not an ozone dataset.")
        st.divider()
        st.caption("Origins: A external - B own - C model - D assumption - E user input")


def default_sample() -> dict:
    return {"module": "WASTEWATER", "volume_L": 5.0, "consistency_pct": 2.0, "pH": 6.3, "temp": 25.0, "TDS": None, "TSS": None, "COD": None,
            "abs0": None, "wavelength": None, "initial_L": None, "turbid": False, "contaminants": [], "sample_type": "Laboratory wastewater",
            "ozone_output_mg_h": None, "air_flow_L_h": None, "transfer_eff_pct": None, "ventilation": False, "offgas": False, "estop": False, "ppe": False, "flammable_solvents": False}


def get_sample() -> dict:
    if "sample" not in st.session_state:
        st.session_state["sample"] = default_sample()
    return st.session_state["sample"]
