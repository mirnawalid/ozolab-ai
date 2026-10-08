# OzoLab AI - Treatment Decision Support for an Existing Ozone Prototype

AI-powered **decision-support** dashboard (Streamlit) for the OzoLab AI ozone prototype (Galala University x Arizona State University).
It is **completely separate from the hardware**: no Arduino/ESP32 link, no sensors, no pump control. It is a first, basic **prototype** for laboratory staff and researchers (as defined on the project poster); with further development and testing it could be adapted to wider users - that has **not** been demonstrated.

```
CHARACTERIZE -> PREDICT -> OPTIMIZE -> RECOMMEND -> EXPERIMENT -> MEASURE -> LEARN -> IMPROVE
```

You tell the app **what you have** (sample, volume, measurements, equipment, safety confirmations). It returns a **staged treatment recipe**
for the existing prototype (pre-treatment -> ozone -> post-treatment -> verification), expected outcomes with uncertainty, the reasoning,
alternative scenarios, and **what is still UNKNOWN**. After you run the experiment you log the result; the model learns from it, and the
**Experiment Planner** proposes the most informative next experiment.

## Pages
| # | Page | Purpose |
|---|------|---------|
| 0 | Home | Overview, counts per data origin, data-integrity notice |
| 1 | Sample Analysis | Enter what you have (optional fields clearly optional) + safety gates |
| 2 | AI Treatment Recommendation | The recipe, outcomes, "Why this recommendation?", warnings |
| 3 | What-if Simulator | Compare scenarios A/B/C with transparent, editable scoring + graphs |
| 4 | Experiment Planner | Active-learning / design-of-experiments: next experiment |
| 5 | Water Quality Analysis | ACS pulp-mill benchmark exploration + Biochemical Oxygen Demand (BOD) predictor; BOD and ΔBOD defined |
| 6 | Model Explanation | Permutation importance, response curves, direction of influence |
| 7 | Experiment History | Digital treatment record, CSV export/import, prediction error |
| 8 | Data Management | Every dataset with origin labels + downloads |
| 9 | ML Model Performance | Leakage-aware validation, model comparison (R2, MAE, RMSE) |

## Origin labels (never mixed silently)
**A** external published data - **B** our own experiments - **C** model prediction - **D** engineering assumption - **E** user-entered.

## What is ours, what is literature, what was set aside
| | Category | Content |
|---|---|---|
| **A** | What WE did | The software; the transcription of literature tables; the physical prototype; a 2-sample poster 'Proof of Concept' (unlabeled, unverified). **Our own logged experiments: 0 so far.** |
| **B** | Literature / external data | 61 pulp-bleaching kinetic experiments (published, NOT performed by us); ACS file with 1,033 daily records of a European paper-mill plant. |
| **C** | Considered, NOT used in the final system | Detecting dripping water by whether a paper strip bleaches (old idea; final approach uses an indicator - **team must describe the indicator and the water type tried: NEEDS INPUT**); pulp bleaching as our own use-case (set aside - final use-case is laboratory wastewater). |

## What the numbers mean (verified in the files)
| Number | Meaning | Ours? |
|---|---|---|
| **0** | Our own experiments logged so far (a count, not a result) | yes - it is a count of OUR runs |
| **189** | Literature observation rows transcribed from the screenshots (6 papers + 1 patent) | no |
| **127** | The same literature rows after harmonising (189 minus the 62 duplicate rows created because two papers report the same experiments in two tables) | no |
| **61** | Kinetic rows (pH, temperature, ozone consumed -> L*, a*, b*, DP) that train the pulp model | no - published experiments |
| **1,033** | Daily records in the ACS file: one per day from 2020-01-01 to 2022-10-29, a European paper-mill wastewater plant | no - historical data of another plant, not ozone |
| **12** | A SOFTWARE SETTING (`min_own_records_for_own_model`): the app fits a model on our own wastewater runs only after this many runs. Chosen by the developers; **no paper or dataset source**; NEEDS TEAM DECISION | not a count of experiments |

## Reference conditions stated by the team (handwritten notes - verify)
Oxygen flow **90-120 L/hour** (controlled) - ozone generation **<= 400 mg/hour** (controlled; **unit NEEDS VERIFICATION** on the ozonizer label) - water temperature **25 C** (natural) - pH **6.3** (natural; corrects the handwritten 7; which sample it belongs to NEEDS CLARIFICATION because the poster samples show 7.13 / 7.07).

## Datasets
| Dataset | Rows | Used for |
|---|---|---|
| ACS Engineering Au 2026, Table S1 (DOI 10.1021/acsengineeringau.5c00088) | 1,033 daily records | Water-treatment pipeline/benchmark only. **Not an ozone dataset, not ours.** |
| Literature ozone-bleaching tables | 189 transcribed -> 127 harmonised -> 61 train the model | Pulp L*, a*, b*, DP model (literature background module) |
| Own experiments (`data/own/experiments.csv`) | 0 at start | Retraining; becomes the priority source as it grows |
Reference-only study: *MATLAB-empowered brightness defect prediction system in pulp processing bleaching stage* (ScienceDirect S2666016424003281) - its data is not public and was **not** recreated.

Full documentation: `docs/DATASET_DOCUMENTATION.md`, `docs/PROJECT_SCOPE_AND_PROVENANCE.md`. Excel archive: `Project_Archive/OzoLab_Ozone_Bleaching_Dataset.xlsx`.

## Findings you must know before presenting
1. **ACS file integrity.** Effluent Biochemical Oxygen Demand (BOD) in the downloaded file is an *exact* linear function of the 7 inputs (linear R2 = 1.000000, max residual 3.6e-14). Real plant data never behaves this way. The app reports this openly, uses the file only as a benchmark, and never derives an ozone dose from it.
2. **Wastewater has no dose-response data.** Therefore the wastewater recipe is a safe, staged *data-collecting baseline* scaled from the team's own poster reference (100 L / 10 h), not a fabricated optimum.
3. **The pulp model is literature background, not our work, and is weak for some targets** (leave-one-condition-out R2: L* 0.71; a* 0.12; b* 0.36). The app labels weak models as such.
4. **Safety gates.** The recipe is blocked (RED) unless ventilation, ozone off-gas handling, an emergency power cut-off and PPE are confirmed, and ozone output / O2 flow entered are inside the team specification. None of off-gas handling or an emergency stop is visible in the photos. The dashboard cannot stop the machine - the operator and the physical power cut-off do.
5. The poster's two PoC samples (TDS 765 -> 784) show **no TDS removal**; they are stored as UNVERIFIED context, not training data.

## Run locally (Windows)
```
cd path\to\ozolab-ai
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Tests: `python tests/test_smoke.py` and `python tests/test_engine.py`.
Rebuild literature dataset: `python scripts/build_literature_dataset.py`. Retrain models: `python -m src.training`.

## Deploy
See `docs/DEPLOYMENT_WINDOWS.md` (GitHub -> Streamlit Community Cloud -> public URL). Entry file: `app.py`.

## Layout
```
app.py  pages/  src/  config/settings.json  data/{raw,literature,own}  models/  Project_Archive/  docs/  notebooks/  scripts/  tests/
```
Safety limits and assumptions live in `config/settings.json`; every entry states its source/status. The AI works inside them: if a safety rule is violated, the rule takes priority and the recommendation is blocked.

---

## Contact

| Phone | Email | LinkedIn | GitHub |
|---|---|---|---|
| [+20 1090313641](tel:+201090313641) | [mws103561@gu.edu.eg](mailto:mws103561@gu.edu.eg) | [LinkedIn](https://linkedin.com/in/mirna-walid-145a163b5) | [GitHub](https://github.com/mirnawalid) |
