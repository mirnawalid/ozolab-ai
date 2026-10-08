# Data folder
- `raw/ACS_EngAu_2026_TableS1.xlsx` - the supporting file downloaded from https://pubs.acs.org/doi/10.1021/acsengineeringau.5c00088 (zip `eg5c00088_si_001.zip`, sheet `Input_Data`). Already included (76 KB). If missing, unzip the SI file and put `ACSEngAu_ML_PPM_Table_S1.xlsx` here renamed to `ACS_EngAu_2026_TableS1.xlsx`.
- `literature/` - ozone-bleaching observations transcribed from the team's screenshots (no graph digitising, no invented values). `combined_clean_dataset.csv` feeds the model; `derived_calculated_not_observations.csv` holds CALCULATED values that are never used as observations.
- `own/experiments.csv` - the team's own experiments (empty at start). `poster_proof_of_concept.csv` - 2 UNVERIFIED poster samples, not used for training.
