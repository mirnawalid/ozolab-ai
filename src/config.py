"""Central configuration. No absolute paths: everything is relative to the repo root."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ACS_XLSX = DATA / "raw" / "ACS_EngAu_2026_TableS1.xlsx"
LIT_CLEAN = DATA / "literature" / "combined_clean_dataset.csv"
LIT_FULL = DATA / "literature" / "literature_ozone_bleaching.csv"
OWN_CSV = DATA / "own" / "experiments.csv"
POSTER_CSV = DATA / "own" / "poster_proof_of_concept.csv"
MODELS = ROOT / "models"
ARCHIVE_XLSX = ROOT / "Project_Archive" / "OzoLab_Ozone_Bleaching_Dataset.xlsx"
SETTINGS_JSON = ROOT / "config" / "settings.json"


def settings() -> dict:
    return json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))


def assumption(name: str):
    return settings()["assumptions_editable"][name]["value"]


ORIGIN_LABELS = {
    "A": "A - External published data (real, from papers/patents/SI file)",
    "B": "B - Our own experimental data",
    "C": "C - Model prediction",
    "D": "D - Engineering assumption",
    "E": "E - User-entered information",
}

# Pulp baseline of the P1/P2 series (Exp 0, oxygen-delignified hardwood kraft pulp)
P1_BASELINE = {"L_star": 83.04, "a_star": 2.67, "b_star": 15.13, "DP": 1201}
